#!/usr/bin/env python3
"""
Test connection to Ableton Live via AbletonOSC.

Prerequisites:
1. Ableton Live is running
2. AbletonOSC is enabled in Preferences → Link / Tempo / MIDI → Control Surface
3. Status bar shows "AbletonOSC: Listening for OSC on port 11000"
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from music.ableton_controller import AbletonController
import time


def test_connection():
    """Test basic connection to Ableton."""
    print("=" * 70)
    print("ABLETON CONNECTION TEST")
    print("=" * 70)
    print()

    print("Prerequisites:")
    print("  ✓ Ableton Live 12 Suite running")
    print("  ✓ AbletonOSC enabled in Preferences")
    print("  ✓ Status bar shows 'Listening on port 11000'")
    print()

    # Initialize controller
    print("-" * 70)
    print("STEP 1: Initialize Controller")
    print("-" * 70)
    controller = AbletonController(host='127.0.0.1', send_port=11000)
    print("✓ Controller initialized")
    print(f"  Host: {controller.host}")
    print(f"  Send port: {controller.send_port}")
    print(f"  Receive port: {controller.receive_port}")
    print()

    # Test connection
    print("-" * 70)
    print("STEP 2: Test Connection")
    print("-" * 70)
    print("Sending test message to Ableton...")

    try:
        success = controller.connect()

        if success:
            print("✅ CONNECTION SUCCESSFUL!")
            print()
            print("Ableton is listening on port 11000")
            print("Check Ableton's status bar - it should briefly show:")
            print("  'AbletonOSC: received /live/test'")
            print()
            return controller
        else:
            print("❌ CONNECTION FAILED")
            print()
            print("Troubleshooting:")
            print("  1. Is Ableton Live running?")
            print("  2. Is AbletonOSC enabled in Preferences?")
            print("  3. Check status bar for AbletonOSC messages")
            print("  4. Try restarting Ableton Live")
            print()
            return None

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Is Ableton Live running?")
        print("  2. Is AbletonOSC installed correctly?")
        print("     Path: ~/Music/Ableton/User Library/Remote Scripts/AbletonOSC/")
        print("  3. Check firewall settings (port 11000)")
        print()
        return None


def test_basic_operations(controller: AbletonController):
    """Test basic Ableton operations."""
    print("-" * 70)
    print("STEP 3: Test Basic Operations")
    print("-" * 70)
    print()

    try:
        # Test 1: Set tempo
        print("Test 1: Set Tempo")
        print("  Setting tempo to 120 BPM...")
        controller.set_tempo(120.0)
        print("  ✓ Tempo command sent")
        print("  Check Ableton - tempo should be 120 BPM")
        time.sleep(1)
        print()

        # Test 2: Create MIDI track
        print("Test 2: Create MIDI Track")
        print("  Creating MIDI track at end...")
        track_id = controller.create_midi_track(-1)
        print(f"  ✓ Track creation command sent (track_id: {track_id})")
        print("  Check Ableton - new MIDI track should appear")
        time.sleep(1)
        print()

        # Test 3: Set track name
        print("Test 3: Set Track Name")
        print("  Naming track 'Sentinel Test'...")
        controller.set_track_name(track_id, "Sentinel Test")
        print("  ✓ Track name command sent")
        print("  Check Ableton - track should be named 'Sentinel Test'")
        time.sleep(1)
        print()

        # Test 4: Create clip
        print("Test 4: Create MIDI Clip")
        print("  Creating 4-bar clip in first scene...")
        controller.create_clip(track_id, 0, 4.0)
        print("  ✓ Clip creation command sent")
        print("  Check Ableton - 4-bar clip should appear in first scene")
        time.sleep(1)
        print()

        # Test 5: Add note
        print("Test 5: Add MIDI Note")
        print("  Adding C4 note (MIDI 60) at beat 0...")
        controller.add_note(
            track_id=track_id,
            clip_slot=0,
            pitch=60,  # C4
            start_time=0.0,
            duration=1.0,
            velocity=100
        )
        print("  ✓ Note add command sent")
        print("  Check Ableton - double-click clip to see note")
        time.sleep(1)
        print()

        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Check Ableton Live for created track and clip")
        print("  2. Double-click the clip to see the MIDI note")
        print("  3. Load an instrument on the track")
        print("  4. Play the clip (click the play button)")
        print()

    except Exception as e:
        print(f"❌ ERROR during operations: {e}")
        print()


def main():
    """Run all tests."""
    controller = test_connection()

    if controller:
        print()
        response = input("Connection successful! Run basic operations test? (y/n): ")

        if response.lower() == 'y':
            print()
            test_basic_operations(controller)
        else:
            print()
            print("Skipping operations test.")
            print()

    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()
    print("See docs/ABLETON_OSC_SETUP.md for more information.")
    print()


if __name__ == '__main__':
    main()
