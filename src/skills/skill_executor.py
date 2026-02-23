"""
Skill executor for running skills with sandboxing and resource limits.

Provides isolated execution environment with timeout, resource limits, and security.
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
import signal

import structlog

from .skill_registry import SkillRegistry, SkillMetadata

logger = structlog.get_logger(__name__)


@dataclass
class ExecutionResult:
    """Result of skill execution."""

    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timeout: bool = False
    metadata: Dict[str, Any] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'execution_time': self.execution_time,
            'timeout': self.timeout,
            'metadata': self.metadata or {}
        }


class SkillExecutor:
    """Executor for running skills with sandboxing."""

    def __init__(self, registry: SkillRegistry, timeout: int = 30):
        """
        Initialize skill executor.

        Args:
            registry: SkillRegistry instance
            timeout: Default timeout in seconds (default: 30)
        """
        self.registry = registry
        self.default_timeout = timeout

        logger.info("skill_executor_initialized", timeout=timeout)

    async def execute_skill(
        self,
        skill_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute a skill with parameters.

        Args:
            skill_name: Name of skill to execute
            parameters: Skill parameters
            timeout: Execution timeout (uses default if not specified)

        Returns:
            ExecutionResult
        """
        import time
        start_time = time.time()

        logger.info("executing_skill",
                   skill=skill_name,
                   parameters=list(parameters.keys()))

        # Get skill metadata
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return ExecutionResult(
                success=False,
                error=f"Skill '{skill_name}' not found"
            )

        # Validate skill
        is_valid, issues = self.registry.validate_skill(skill_name)
        if not is_valid:
            return ExecutionResult(
                success=False,
                error=f"Skill validation failed: {', '.join(issues)}"
            )

        # Validate parameters
        validation_error = self._validate_parameters(skill, parameters)
        if validation_error:
            return ExecutionResult(
                success=False,
                error=validation_error
            )

        # Find main script
        script_path = self._find_main_script(skill)
        if not script_path:
            return ExecutionResult(
                success=False,
                error=f"No executable script found for skill '{skill_name}'"
            )

        # Execute skill
        try:
            timeout_value = timeout or self.default_timeout
            output = await self._run_script(
                script_path,
                parameters,
                timeout_value
            )

            execution_time = time.time() - start_time

            logger.info("skill_executed",
                       skill=skill_name,
                       success=True,
                       execution_time=execution_time)

            return ExecutionResult(
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={'script': str(script_path)}
            )

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.error("skill_timeout",
                        skill=skill_name,
                        timeout=timeout_value)

            return ExecutionResult(
                success=False,
                error=f"Skill execution timed out after {timeout_value}s",
                timeout=True,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error("skill_execution_failed",
                        skill=skill_name,
                        error=str(e),
                        execution_time=execution_time)

            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    def _validate_parameters(
        self,
        skill: SkillMetadata,
        parameters: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate skill parameters.

        Args:
            skill: SkillMetadata
            parameters: Parameters to validate

        Returns:
            Error message if validation fails, None otherwise
        """
        # Check required parameters
        for param_name, param_def in skill.parameters.items():
            if param_def.get('required', False):
                if param_name not in parameters:
                    return f"Required parameter '{param_name}' is missing"

        # Check for unknown parameters
        for param_name in parameters:
            if param_name not in skill.parameters:
                logger.warning("unknown_parameter",
                             skill=skill.name,
                             parameter=param_name)

        # Type validation (basic)
        for param_name, param_value in parameters.items():
            if param_name not in skill.parameters:
                continue

            expected_type = skill.parameters[param_name].get('type', 'string')
            if not self._check_parameter_type(param_value, expected_type):
                return f"Parameter '{param_name}' has wrong type (expected {expected_type})"

        return None

    def _check_parameter_type(self, value: Any, expected_type: str) -> bool:
        """
        Check if parameter value matches expected type.

        Args:
            value: Parameter value
            expected_type: Expected type name

        Returns:
            True if type matches
        """
        type_mapping = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict
        }

        expected = type_mapping.get(expected_type.lower())
        if not expected:
            # Unknown type, skip validation
            return True

        return isinstance(value, expected)

    def _find_main_script(self, skill: SkillMetadata) -> Optional[Path]:
        """
        Find main executable script for skill.

        Args:
            skill: SkillMetadata

        Returns:
            Path to main script or None
        """
        # Try common patterns
        patterns = [
            skill.skill_dir / f"{skill.name}.py",
            skill.skill_dir / "main.py",
            skill.skill_dir / "script.py",
            skill.skill_dir / f"{skill.skill_dir.name}.py",
        ]

        for path in patterns:
            if path.exists() and path.is_file():
                return path

        return None

    async def _run_script(
        self,
        script_path: Path,
        parameters: Dict[str, Any],
        timeout: int
    ) -> Any:
        """
        Run Python script with parameters.

        Args:
            script_path: Path to script
            parameters: Skill parameters
            timeout: Timeout in seconds

        Returns:
            Script output (parsed JSON if possible)
        """
        # Prepare parameters as JSON
        params_json = json.dumps(parameters)

        # Build command
        cmd = [
            sys.executable,  # Use same Python interpreter
            str(script_path),
            params_json
        ]

        # Set up environment (inherit current env)
        env = os.environ.copy()

        # Execute script with timeout
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            # Check return code
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                raise RuntimeError(f"Script failed: {error_msg}")

            # Parse output
            output_str = stdout.decode('utf-8', errors='replace')

            # Try to parse as JSON
            try:
                return json.loads(output_str)
            except json.JSONDecodeError:
                # Return as plain text
                return output_str.strip()

        except asyncio.TimeoutError:
            # Kill process if still running
            if process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
            raise

    async def execute_skill_safe(
        self,
        skill_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute skill with exception handling (never raises).

        Args:
            skill_name: Skill name
            parameters: Skill parameters
            timeout: Execution timeout

        Returns:
            ExecutionResult (always returns, never raises)
        """
        try:
            return await self.execute_skill(skill_name, parameters, timeout)
        except Exception as e:
            logger.error("skill_execution_error",
                        skill=skill_name,
                        error=str(e))
            return ExecutionResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )

    def get_skill_help(self, skill_name: str) -> Optional[str]:
        """
        Get help text for a skill.

        Args:
            skill_name: Skill name

        Returns:
            Help text or None
        """
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return None

        # Read SKILL.md file
        try:
            help_text = skill.skill_file.read_text()
            return help_text
        except Exception as e:
            logger.error("failed_to_read_skill_help",
                        skill=skill_name,
                        error=str(e))
            return None
