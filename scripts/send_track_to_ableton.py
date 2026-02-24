#!/usr/bin/env python3
"""
Send generated music track to Ableton Live.

Generates a complete track and automatically:
1. Creates tracks in Ableton
2. Creates MIDI clips
3. Adds all notes
4. Sets up basic mix

Prerequisites:
- Ableton Live running with AbletonOSC enabled
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from music.ableton_controller import AbletonController
from music.generators.melody_generator import MelodyGenerator, Scale
from music.generators.chord_generator import ChordGenerator
from music.generators.bass_generator import BassGenerator
from music.generators.drum_generator import DrumGenerator
import time


def main():
    """Generate and send complete track to Ableton."""
    print("=" * 70)
    print("SENTINEL → ABLETON - Complete Track Integration")
    print("=" * 70)
    print()

    # Configuration
    KEY = 66  # F# minor
    SCALE_MELODY = Scale.MINOR_PENTATONIC
    SCALE_HARMONY = Scale.MINOR
    BPM = 90
    BARS = 8
    CLIP_SLOT = 0  # First scene

    print("Configuration:")
    print(f"  Key: F# Minor")
    print(f"  BPM: {BPM}")
    print(f"  Bars: {BARS}")
    print()

    # Connect to Ableton
    print("-" * 70)
    print("STEP 1: Connect to Ableton")
    print("-" * 70)
    ableton = AbletonController()

    if not ableton.connect():
        print("❌ Failed to connect to Ableton Live")
        print()
        print("Make sure:")
        print("  1. Ableton Live is running")
        print("  2. AbletonOSC is enabled in Preferences")
        print("  3. Status bar shows 'Listening on port 11000'")
        print()
        return

    print("✓ Connected to Ableton")
    print()

    # Set tempo
    print("-" * 70)
    print("STEP 2: Set Tempo")
    print("-" * 70)
    ableton.set_tempo(BPM)
    print(f"✓ Tempo set to {BPM} BPM")
    print()

    # Initialize generators
    print("-" * 70)
    print("STEP 3: Generate Music")
    print("-" * 70)
    chord_gen = ChordGenerator(key_root=KEY, scale=SCALE_HARMONY)
    melody_gen = MelodyGenerator(key_root=KEY, scale=SCALE_MELODY)
    bass_gen = BassGenerator(key_root=KEY, scale=SCALE_HARMONY)
    drum_gen = DrumGenerator(bpm=BPM, swing=0.3)

    # Generate all parts
    print("Generating chords...")
    chords = chord_gen.generate_progression("lofi_1", bars=BARS, beats_per_chord=4.0)
    print(f"  ✓ {len(chords)} chords generated")

    print("Generating melody...")
    melody = melody_gen.generate_motif_based(bars=BARS, creativity=0.7)
    melody = melody_gen.humanize(melody, amount=0.4)
    print(f"  ✓ {len(melody)} notes generated")

    print("Generating bass...")
    bass = bass_gen.generate_walking(chords)
    print(f"  ✓ {len(bass)} notes generated")

    print("Generating drums...")
    drums = drum_gen.generate_lofi(bars=BARS, complexity=0.6, humanize=0.4)
    print(f"  ✓ {len(drums)} hits generated")
    print()

    # Create tracks in Ableton
    print("-" * 70)
    print("STEP 4: Create Tracks in Ableton")
    print("-" * 70)

    # Track 1: Drums (always use index directly, not -1)
    print("Creating drums track...")
    drums_track = 0  # Will be created at index 0
    ableton.create_midi_track(drums_track)
    time.sleep(0.1)
    ableton.set_track_name(drums_track, "Drums")
    print(f"  ✓ Track {drums_track}: Drums")

    # Track 2: Bass
    print("Creating bass track...")
    bass_track = 1
    ableton.create_midi_track(bass_track)
    time.sleep(0.1)
    ableton.set_track_name(bass_track, "Bass")
    print(f"  ✓ Track {bass_track}: Bass")

    # Track 3: Chords
    print("Creating chords track...")
    chords_track = 2
    ableton.create_midi_track(chords_track)
    time.sleep(0.1)
    ableton.set_track_name(chords_track, "Chords")
    print(f"  ✓ Track {chords_track}: Chords")

    # Track 4: Melody
    print("Creating melody track...")
    melody_track = 3
    ableton.create_midi_track(melody_track)
    time.sleep(0.1)
    ableton.set_track_name(melody_track, "Melody")
    print(f"  ✓ Track {melody_track}: Melody")
    print()

    # Create clips
    print("-" * 70)
    print("STEP 5: Create MIDI Clips")
    print("-" * 70)

    print(f"Creating {BARS}-bar clips in scene {CLIP_SLOT}...")
    ableton.create_clip(drums_track, CLIP_SLOT, float(BARS))
    time.sleep(0.1)
    ableton.create_clip(bass_track, CLIP_SLOT, float(BARS))
    time.sleep(0.1)
    ableton.create_clip(chords_track, CLIP_SLOT, float(BARS))
    time.sleep(0.1)
    ableton.create_clip(melody_track, CLIP_SLOT, float(BARS))
    time.sleep(0.1)
    print("✓ All clips created")
    print()

    # Add notes to drums
    print("-" * 70)
    print("STEP 6: Add MIDI Notes")
    print("-" * 70)

    print(f"Adding {len(drums)} drum hits...")
    for hit in drums:
        ableton.add_note(
            track_id=drums_track,
            clip_slot=CLIP_SLOT,
            pitch=hit.sound.value,
            start_time=hit.start,
            duration=0.1,
            velocity=hit.velocity
        )
    print("  ✓ Drums complete")

    print(f"Adding {len(bass)} bass notes...")
    for note in bass:
        ableton.add_note(
            track_id=bass_track,
            clip_slot=CLIP_SLOT,
            pitch=note.pitch,
            start_time=note.start,
            duration=note.duration,
            velocity=note.velocity
        )
    print("  ✓ Bass complete")

    print(f"Adding {len(chords)} chords...")
    for chord in chords:
        chord_notes = chord.get_notes()
        for pitch in chord_notes:
            ableton.add_note(
                track_id=chords_track,
                clip_slot=CLIP_SLOT,
                pitch=pitch,
                start_time=chord.start,
                duration=chord.duration,
                velocity=chord.velocity
            )
    print("  ✓ Chords complete")

    print(f"Adding {len(melody)} melody notes...")
    for note in melody:
        ableton.add_note(
            track_id=melody_track,
            clip_slot=CLIP_SLOT,
            pitch=note.pitch,
            start_time=note.start,
            duration=note.duration,
            velocity=note.velocity
        )
    print("  ✓ Melody complete")
    print()

    # Set up basic mix
    print("-" * 70)
    print("STEP 7: Set Up Mix")
    print("-" * 70)

    # Drums: Louder, centered
    ableton.set_track_volume(drums_track, 0.0)  # Unity gain
    ableton.set_track_pan(drums_track, 0.0)
    print("  ✓ Drums: 0 dB, Center")

    # Bass: Slightly quieter, centered
    ableton.set_track_volume(bass_track, -3.0)
    ableton.set_track_pan(bass_track, 0.0)
    print("  ✓ Bass: -3 dB, Center")

    # Chords: Quieter, slightly left
    ableton.set_track_volume(chords_track, -6.0)
    ableton.set_track_pan(chords_track, -0.2)
    print("  ✓ Chords: -6 dB, Left")

    # Melody: Medium, slightly right
    ableton.set_track_volume(melody_track, -4.0)
    ableton.set_track_pan(melody_track, 0.2)
    print("  ✓ Melody: -4 dB, Right")
    print()

    # Summary
    print("=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print()
    print("Your track is now in Ableton Live:")
    print()
    print("  📊 Stats:")
    print(f"     • 4 MIDI tracks created")
    print(f"     • {BARS} bars at {BPM} BPM")
    print(f"     • {len(drums)} drum hits")
    print(f"     • {len(bass)} bass notes")
    print(f"     • {len(chords)} chords ({sum(len(c.get_notes()) for c in chords)} notes)")
    print(f"     • {len(melody)} melody notes")
    print()
    print("  🎹 Next Steps:")
    print("     1. Load instruments on each track:")
    print("        • Drums → Drum Rack (lo-fi kit)")
    print("        • Bass → Wavetable (bass preset)")
    print("        • Chords → Piano/Rhodes/Pad")
    print("        • Melody → Synth Pluck/Lead")
    print()
    print("     2. Fire the clip in Scene 1:")
    print("        • Click the play button on any clip slot")
    print("        • Or press Spacebar to play all")
    print()
    print("     3. Adjust the mix to taste")
    print()
    print("     4. Add effects (reverb, delay, etc.)")
    print()
    print("     5. Export audio when ready!")
    print()


if __name__ == '__main__':
    main()
