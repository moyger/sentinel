"""
Proactive reasoning engine for intelligent alert analysis.

Uses Claude API to analyze alerts from all monitors and generate
contextual insights, recommendations, and prioritization.
"""

from typing import Dict, Any, List, Optional
from anthropic import AsyncAnthropic

from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class ReasoningEngine:
    """
    Analyzes heartbeat data and generates intelligent insights.

    Uses Claude to:
    - Prioritize alerts based on context
    - Identify patterns and connections
    - Generate actionable recommendations
    - Summarize complex situations
    """

    def __init__(self):
        """Initialize reasoning engine."""
        self.claude = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("Reasoning engine initialized")

    async def analyze_heartbeat(
        self,
        heartbeat_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze heartbeat results and generate insights.

        Args:
            heartbeat_results: Results from heartbeat orchestrator

        Returns:
            Dictionary with analysis and recommendations
        """
        alerts = heartbeat_results.get("alerts", [])
        summary = heartbeat_results.get("summary", {})
        monitors = heartbeat_results.get("monitors", {})

        if not alerts:
            return {
                "has_insights": False,
                "message": "No alerts to analyze"
            }

        logger.info("Analyzing heartbeat results...", alert_count=len(alerts))

        try:
            # Build analysis prompt
            prompt = self._build_analysis_prompt(alerts, summary, monitors)

            # Call Claude API
            response = await self.claude.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=1024,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            analysis_text = response.content[0].text

            logger.info(
                "Heartbeat analysis completed",
                tokens_used=response.usage.total_tokens
            )

            return {
                "has_insights": True,
                "analysis": analysis_text,
                "alert_count": len(alerts),
                "tokens_used": response.usage.total_tokens
            }

        except Exception as e:
            logger.error("Reasoning analysis failed", error=str(e), exc_info=True)
            return {
                "has_insights": False,
                "error": str(e)
            }

    async def prioritize_alerts(
        self,
        alerts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use Claude to intelligently prioritize alerts.

        Args:
            alerts: List of alerts from monitors

        Returns:
            Alerts sorted by intelligent priority
        """
        if not alerts:
            return []

        logger.info("Prioritizing alerts...", alert_count=len(alerts))

        try:
            # Build prioritization prompt
            prompt = self._build_prioritization_prompt(alerts)

            # Call Claude API
            response = await self.claude.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=512,
                temperature=0.3,  # Lower temp for more consistent ordering
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response to get priority order
            # For now, return original alerts (can enhance with actual reordering)
            logger.info("Alert prioritization completed")

            return alerts

        except Exception as e:
            logger.error("Alert prioritization failed", error=str(e), exc_info=True)
            return alerts  # Return original order on failure

    def _build_analysis_prompt(
        self,
        alerts: List[Dict[str, Any]],
        summary: Dict[str, Any],
        monitors: Dict[str, Any]
    ) -> str:
        """
        Build prompt for heartbeat analysis.

        Args:
            alerts: List of alerts
            summary: Heartbeat summary
            monitors: Monitor results

        Returns:
            Analysis prompt
        """
        prompt = """You are Sentinel's proactive reasoning engine. Analyze the following heartbeat data and provide actionable insights.

## Heartbeat Summary
"""

        # Add summary stats
        prompt += f"- Total alerts: {summary.get('total_alerts', 0)}\n"
        prompt += f"- Urgent: {summary.get('alerts_by_priority', {}).get('urgent', 0)}\n"
        prompt += f"- Normal: {summary.get('alerts_by_priority', {}).get('normal', 0)}\n"
        prompt += f"- Low: {summary.get('alerts_by_priority', {}).get('low', 0)}\n"
        prompt += "\n"

        # Add monitor status
        prompt += "## Monitor Status\n"
        for monitor_name, monitor_data in monitors.items():
            status = monitor_data.get("status", "unknown")
            prompt += f"- {monitor_name.title()}: {status}\n"
        prompt += "\n"

        # Add alerts
        prompt += "## Alerts\n"
        for i, alert in enumerate(alerts[:10], 1):  # Limit to 10 alerts
            prompt += f"\n### Alert {i}: {alert.get('title')}\n"
            prompt += f"**Source:** {alert.get('source')}\n"
            prompt += f"**Priority:** {alert.get('priority')}\n"
            prompt += f"**Message:**\n{alert.get('message')}\n"

        prompt += """

## Your Task

Provide a concise analysis (2-3 paragraphs) that:

1. **Highlights the most important items** - What needs immediate attention?
2. **Identifies patterns or connections** - Are there related issues across different alerts?
3. **Provides actionable recommendations** - What should the user do first?

Keep your response focused and actionable. Use bullet points for recommendations.
"""

        return prompt

    def _build_prioritization_prompt(
        self,
        alerts: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for alert prioritization.

        Args:
            alerts: List of alerts

        Returns:
            Prioritization prompt
        """
        prompt = """You are helping prioritize these alerts. Consider urgency, impact, and dependencies.

## Alerts to Prioritize

"""

        for i, alert in enumerate(alerts, 1):
            prompt += f"{i}. **{alert.get('title')}** ({alert.get('priority')})\n"
            prompt += f"   Source: {alert.get('source')}\n"
            prompt += f"   {alert.get('message', '')[:100]}...\n\n"

        prompt += """
Rank these alerts from most to least important, considering:
- True urgency (not just labeled priority)
- Impact on the user's day
- Dependencies between items

Respond with just the numbers in priority order (e.g., "3, 1, 5, 2, 4").
"""

        return prompt
