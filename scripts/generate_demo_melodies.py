#!/usr/bin/env python3
"""
Generate demo melodies at different creativity levels.

Creates 3 MIDI files demonstrating:
1. Basic (low creativity)
2. Varied (medium creativity)
3. Motif-based (high creativity)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from music.generators.melody_generator import MelodyGenerator, Scale
import mido
from mido import Message, MidiFile, MidiTrack


def notes_to_midi(notes, output_path, tempo=90, track_name="Melody"):
    """
    Convert Note objects to MIDI file.

    Args:
        notes: List of Note objects
        output_path: Path to save MIDI file
        tempo: BPM
        track_name: Name of MIDI track
    """
    # Create MIDI file
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set track name
    track.append(mido.MetaMessage('track_name', name=track_name))

    # Set tempo (microseconds per beat)
    microseconds_per_beat = int(60_000_000 / tempo)
    track.append(mido.MetaMessage('set_tempo', tempo=microseconds_per_beat))

    # Convert notes to MIDI messages
    # MIDI uses ticks, we need to convert beats to ticks
    ticks_per_beat = mid.ticks_per_beat  # Default: 480

    # Sort notes by start time
    sorted_notes = sorted(notes, key=lambda n: n.start)

    current_time_ticks = 0

    for note in sorted_notes:
        # Calculate start time in ticks
        note_start_ticks = int(max(0, note.start) * ticks_per_beat)
        note_duration_ticks = int(max(0.1, note.duration) * ticks_per_beat)

        # Delta time until this note starts
        delta_time = max(0, note_start_ticks - current_time_ticks)

        # Note on
        track.append(Message(
            'note_on',
            note=note.pitch,
            velocity=note.velocity,
            time=delta_time
        ))

        current_time_ticks = note_start_ticks

        # Note off
        track.append(Message(
            'note_off',
            note=note.pitch,
            velocity=0,
            time=note_duration_ticks
        ))

        current_time_ticks += note_duration_ticks

    # End of track
    track.append(mido.MetaMessage('end_of_track', time=0))

    # Save MIDI file
    mid.save(output_path)
    print(f"✅ Saved: {output_path}")


def main():
    """Generate demo melodies."""
    print("=" * 70)
    print("SENTINEL MUSIC GENERATOR - Creativity Demo")
    print("=" * 70)
    print()

    # Output directory
    output_dir = Path(__file__).parent.parent / 'music' / 'demos'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create generator in F# minor (lo-fi friendly key)
    print("Key: F# minor (Nujabes territory)")
    print("Scale: Minor Pentatonic")
    print("BPM: 90")
    print()

    generator = MelodyGenerator(key_root=66, scale=Scale.MINOR_PENTATONIC)

    # ========================================
    # Demo 1: Basic Melody (Low Creativity)
    # ========================================
    print("-" * 70)
    print("1. BASIC MELODY (Creativity: 3/10)")
    print("-" * 70)
    print("   • Follows scale strictly")
    print("   • Simple quarter note rhythm")
    print("   • Predictable ascending/descending pattern")
    print("   • Constant velocity (no dynamics)")
    print()

    basic = generator.generate_basic(bars=8)
    basic_path = output_dir / '01_basic_melody.mid'
    notes_to_midi(basic, basic_path, tempo=90, track_name="Basic Melody")

    print(f"   Generated: {len(basic)} notes over 8 bars")
    print(f"   Note range: MIDI {min(n.pitch for n in basic)}-{max(n.pitch for n in basic)}")
    print()

    # ========================================
    # Demo 2: Varied Melody (Medium Creativity)
    # ========================================
    print("-" * 70)
    print("2. VARIED MELODY (Creativity: 6/10)")
    print("-" * 70)
    print("   • Mixed rhythm (quarters, eighths, halves)")
    print("   • Melodic leaps and steps")
    print("   • Dynamic velocity (60-110)")
    print("   • More natural phrasing")
    print()

    varied = generator.generate_varied(bars=8, creativity=0.6)
    varied_path = output_dir / '02_varied_melody.mid'
    notes_to_midi(varied, varied_path, tempo=90, track_name="Varied Melody")

    print(f"   Generated: {len(varied)} notes over 8 bars")
    print(f"   Note range: MIDI {min(n.pitch for n in varied)}-{max(n.pitch for n in varied)}")
    print(f"   Velocity range: {min(n.velocity for n in varied)}-{max(n.velocity for n in varied)}")
    print()

    # ========================================
    # Demo 3: Motif-Based (High Creativity)
    # ========================================
    print("-" * 70)
    print("3. MOTIF-BASED COMPOSITION (Creativity: 7/10)")
    print("-" * 70)
    print("   • Creates short motif, then develops it")
    print("   • Uses variations (transposition, inversion)")
    print("   • Repetition with variation (like real music)")
    print("   • More coherent structure")
    print()

    motif = generator.generate_motif_based(bars=8, creativity=0.7)
    motif_path = output_dir / '03_motif_based.mid'
    notes_to_midi(motif, motif_path, tempo=90, track_name="Motif Development")

    print(f"   Generated: {len(motif)} notes over 8 bars")
    print(f"   Note range: MIDI {min(n.pitch for n in motif)}-{max(n.pitch for n in motif)}")
    print()

    # ========================================
    # Demo 4: Humanized Version
    # ========================================
    print("-" * 70)
    print("4. HUMANIZED (Adds imperfections)")
    print("-" * 70)
    print("   • Slight timing variations (swing/groove)")
    print("   • Velocity variations (human dynamics)")
    print("   • More 'organic' feel")
    print()

    humanized = generator.humanize(motif, amount=0.4)
    humanized_path = output_dir / '04_humanized.mid'
    notes_to_midi(humanized, humanized_path, tempo=90, track_name="Humanized Melody")

    print(f"   Generated: {len(humanized)} notes over 8 bars")
    print(f"   Timing variations: ±0.02 beats")
    print(f"   Velocity variations: ±8 points")
    print()

    # Summary
    print("=" * 70)
    print("DEMO COMPLETE!")
    print("=" * 70)
    print()
    print("📁 MIDI files saved to:")
    print(f"   {output_dir}/")
    print()
    print("🎵 To listen:")
    print("   1. Open Ableton Live")
    print("   2. Drag MIDI files onto tracks")
    print("   3. Load an instrument (e.g., Wavetable, Sampler)")
    print("   4. Press Play!")
    print()
    print("🎹 Try this:")
    print("   • Load all 4 MIDI files on separate tracks")
    print("   • Use same instrument on each")
    print("   • Compare the creativity levels")
    print("   • Notice how humanization improves feel")
    print()
    print("💡 Next steps:")
    print("   • Add chords (chord_generator.py)")
    print("   • Add drums (drum_generator.py)")
    print("   • Add bass (bass_generator.py)")
    print("   • Mix and export!")
    print()


if __name__ == '__main__':
    main()
