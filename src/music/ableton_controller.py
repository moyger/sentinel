"""
Ableton Live controller via AbletonOSC.

Provides high-level Python interface to control Ableton Live programmatically
using OSC (Open Sound Control) messages.

Requirements:
- AbletonOSC installed in Ableton Live's Remote Scripts
- Ableton Live running with AbletonOSC enabled
- python-osc package installed
"""

from typing import List, Optional, Tuple
from pythonosc import udp_client, osc_server, dispatcher
from pythonosc.osc_message import OscMessage
import threading
import time
import logging

logger = logging.getLogger(__name__)


class AbletonController:
    """Control Ableton Live via OSC messages."""

    def __init__(
        self,
        host: str = '127.0.0.1',
        send_port: int = 11000,
        receive_port: int = 11001
    ):
        """
        Initialize Ableton OSC controller.

        Args:
            host: Ableton host (default: localhost)
            send_port: Port to send OSC messages to Ableton (default: 11000)
            receive_port: Port to receive OSC messages from Ableton (default: 11001)
        """
        self.host = host
        self.send_port = send_port
        self.receive_port = receive_port

        # OSC client (send to Ableton)
        self.client = udp_client.SimpleUDPClient(host, send_port)

        # OSC server (receive from Ableton) - optional
        self.server = None
        self.server_thread = None

        self._connected = False

    def connect(self) -> bool:
        """
        Test connection to Ableton.

        Returns:
            True if connection successful
        """
        try:
            # Send test message
            self.client.send_message('/live/test', [])
            self._connected = True
            logger.info(f"Connected to Ableton on port {self.send_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ableton: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """Disconnect from Ableton."""
        if self.server_thread:
            self.server.shutdown()
            self.server_thread.join()
        self._connected = False
        logger.info("Disconnected from Ableton")

    # ============================================================================
    # SONG CONTROL
    # ============================================================================

    def play(self):
        """Start playback."""
        self.client.send_message('/live/song/start_playing', [])

    def stop(self):
        """Stop playback."""
        self.client.send_message('/live/song/stop_playing', [])

    def set_tempo(self, bpm: float):
        """
        Set song tempo.

        Args:
            bpm: Tempo in beats per minute (20-999)
        """
        self.client.send_message('/live/song/set/tempo', [bpm])

    def get_tempo(self) -> Optional[float]:
        """Get current tempo (requires OSC server setup)."""
        # TODO: Implement with OSC response handling
        pass

    def set_time_signature(self, numerator: int, denominator: int):
        """
        Set time signature.

        Args:
            numerator: Top number (e.g., 4 in 4/4)
            denominator: Bottom number (e.g., 4 in 4/4)
        """
        self.client.send_message('/live/song/set/signature_numerator', [numerator])
        self.client.send_message('/live/song/set/signature_denominator', [denominator])

    # ============================================================================
    # TRACK OPERATIONS
    # ============================================================================

    def create_midi_track(self, index: int = -1) -> int:
        """
        Create a MIDI track.

        Args:
            index: Position to insert track (-1 = end)

        Returns:
            Track index
        """
        self.client.send_message('/live/song/create_midi_track', [index])
        # If index is -1, we'd need to query the track count
        # For now, return the index
        return index

    def create_audio_track(self, index: int = -1) -> int:
        """
        Create an audio track.

        Args:
            index: Position to insert track (-1 = end)

        Returns:
            Track index
        """
        self.client.send_message('/live/song/create_audio_track', [index])
        return index

    def set_track_name(self, track_id: int, name: str):
        """
        Set track name.

        Args:
            track_id: Track index (0-based)
            name: Track name
        """
        self.client.send_message('/live/track/set/name', [track_id, name])

    def set_track_volume(self, track_id: int, volume_db: float):
        """
        Set track volume.

        Args:
            track_id: Track index
            volume_db: Volume in dB (-inf to 6.0, 0 = unity)
        """
        self.client.send_message('/live/track/set/volume', [track_id, volume_db])

    def set_track_pan(self, track_id: int, pan: float):
        """
        Set track panning.

        Args:
            track_id: Track index
            pan: Pan position (-1.0 = left, 0 = center, 1.0 = right)
        """
        self.client.send_message('/live/track/set/panning', [track_id, pan])

    def mute_track(self, track_id: int, muted: bool = True):
        """
        Mute/unmute track.

        Args:
            track_id: Track index
            muted: True to mute, False to unmute
        """
        self.client.send_message('/live/track/set/mute', [track_id, 1 if muted else 0])

    def solo_track(self, track_id: int, solo: bool = True):
        """
        Solo/unsolo track.

        Args:
            track_id: Track index
            solo: True to solo, False to unsolo
        """
        self.client.send_message('/live/track/set/solo', [track_id, 1 if solo else 0])

    def arm_track(self, track_id: int, armed: bool = True):
        """
        Arm/disarm track for recording.

        Args:
            track_id: Track index
            armed: True to arm, False to disarm
        """
        self.client.send_message('/live/track/set/arm', [track_id, 1 if armed else 0])

    # ============================================================================
    # CLIP OPERATIONS
    # ============================================================================

    def create_clip(
        self,
        track_id: int,
        clip_slot: int,
        length_bars: float
    ) -> Tuple[int, int]:
        """
        Create MIDI clip in clip slot.

        Args:
            track_id: Track index
            clip_slot: Clip slot index (0 = first scene)
            length_bars: Clip length in bars

        Returns:
            (track_id, clip_slot) tuple
        """
        self.client.send_message(
            '/live/clip_slot/create_clip',
            [track_id, clip_slot, length_bars]
        )
        return (track_id, clip_slot)

    def fire_clip(self, track_id: int, clip_slot: int):
        """
        Fire (play) clip.

        Args:
            track_id: Track index
            clip_slot: Clip slot index
        """
        self.client.send_message('/live/clip_slot/fire', [track_id, clip_slot])

    def stop_clip(self, track_id: int, clip_slot: int):
        """
        Stop clip.

        Args:
            track_id: Track index
            clip_slot: Clip slot index
        """
        self.client.send_message('/live/clip_slot/stop', [track_id, clip_slot])

    def add_note(
        self,
        track_id: int,
        clip_slot: int,
        pitch: int,
        start_time: float,
        duration: float,
        velocity: int,
        muted: bool = False
    ):
        """
        Add MIDI note to clip.

        Args:
            track_id: Track index
            clip_slot: Clip slot index
            pitch: MIDI note number (0-127)
            start_time: Note start time in beats
            duration: Note duration in beats
            velocity: Note velocity (0-127)
            muted: Whether note is muted
        """
        self.client.send_message(
            '/live/clip/add/notes',
            [track_id, clip_slot, pitch, start_time, duration, velocity, 1 if muted else 0]
        )

    def add_notes_batch(
        self,
        track_id: int,
        clip_slot: int,
        notes: List[Tuple[int, float, float, int]]
    ):
        """
        Add multiple MIDI notes to clip.

        Args:
            track_id: Track index
            clip_slot: Clip slot index
            notes: List of (pitch, start_time, duration, velocity) tuples
        """
        for pitch, start_time, duration, velocity in notes:
            self.add_note(track_id, clip_slot, pitch, start_time, duration, velocity)

    def clear_clip(self, track_id: int, clip_slot: int):
        """
        Clear all notes from clip.

        Args:
            track_id: Track index
            clip_slot: Clip slot index
        """
        self.client.send_message('/live/clip/clear_all_notes', [track_id, clip_slot])

    def set_clip_name(self, track_id: int, clip_slot: int, name: str):
        """
        Set clip name.

        Args:
            track_id: Track index
            clip_slot: Clip slot index
            name: Clip name
        """
        self.client.send_message('/live/clip/set/name', [track_id, clip_slot, name])

    # ============================================================================
    # DEVICE OPERATIONS
    # ============================================================================

    def load_device(
        self,
        track_id: int,
        device_name: str,
        device_index: int = -1
    ):
        """
        Load instrument or effect device on track.

        Args:
            track_id: Track index
            device_name: Name of device (e.g., "Wavetable", "Reverb")
            device_index: Position in device chain (-1 = end)
        """
        # Note: AbletonOSC may have limited device loading support
        # Check API documentation for available device names
        self.client.send_message(
            '/live/track/load_device',
            [track_id, device_name, device_index]
        )

    def set_device_parameter(
        self,
        track_id: int,
        device_index: int,
        parameter_index: int,
        value: float
    ):
        """
        Set device parameter value.

        Args:
            track_id: Track index
            device_index: Device position in chain (0-based)
            parameter_index: Parameter index (0-based)
            value: Parameter value (range depends on parameter)
        """
        self.client.send_message(
            '/live/device/set/parameter/value',
            [track_id, device_index, parameter_index, value]
        )

    # ============================================================================
    # SCENE OPERATIONS
    # ============================================================================

    def fire_scene(self, scene_index: int):
        """
        Fire (play) scene.

        Args:
            scene_index: Scene index (0-based)
        """
        self.client.send_message('/live/scene/fire', [scene_index])

    def create_scene(self, index: int = -1) -> int:
        """
        Create new scene.

        Args:
            index: Position to insert scene (-1 = end)

        Returns:
            Scene index
        """
        self.client.send_message('/live/song/create_scene', [index])
        return index

    # ============================================================================
    # UTILITY
    # ============================================================================

    def set_log_level(self, level: str = 'info'):
        """
        Set AbletonOSC log level.

        Args:
            level: Log level ('debug', 'info', 'warning', 'error')
        """
        self.client.send_message('/live/api/set/log_level', [level])

    def is_connected(self) -> bool:
        """Check if connected to Ableton."""
        return self._connected


# Convenience functions for common operations
def quick_connect() -> Optional[AbletonController]:
    """
    Quick connect to Ableton (default settings).

    Returns:
        AbletonController if successful, None otherwise
    """
    controller = AbletonController()
    if controller.connect():
        return controller
    return None
