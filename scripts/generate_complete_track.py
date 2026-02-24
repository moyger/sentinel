#!/usr/bin/env python3
"""
Generate a complete music track with all elements.

Creates a full arrangement with:
- Melody
- Chords
- Bass
- Drums

Exports as MIDI file for use in Ableton or any DAW.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from music.generators.melody_generator import MelodyGenerator, Scale
from music.generators.chord_generator import ChordGenerator
from music.generators.bass_generator import BassGenerator
from music.generators.drum_generator import DrumGenerator, DrumHit
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage


def create_midi_track(name: str, channel: int = 0) -> MidiTrack:
    """Create a MIDI track with name."""
    track = MidiTrack()
    track.append(MetaMessage('track_name', name=name))
    track.append(MetaMessage('channel_prefix', channel=channel))
    return track


def notes_to_midi_track(notes, track_name="Track", channel=0, ticks_per_beat=480):
    """
    Convert Note objects to MIDI track.

    Args:
        notes: List of Note objects
        track_name: Name of track
        channel: MIDI channel (0-15)
        ticks_per_beat: MIDI ticks per beat

    Returns:
        MidiTrack
    """
    track = create_midi_track(track_name, channel)

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
            time=delta_time,
            channel=channel
        ))

        current_time_ticks = note_start_ticks

        # Note off
        track.append(Message(
            'note_off',
            note=note.pitch,
            velocity=0,
            time=note_duration_ticks,
            channel=channel
        ))

        current_time_ticks += note_duration_ticks

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    return track


def chords_to_midi_track(chords, track_name="Chords", channel=1, ticks_per_beat=480):
    """
    Convert Chord objects to MIDI track.

    Args:
        chords: List of Chord objects
        track_name: Name of track
        channel: MIDI channel
        ticks_per_beat: MIDI ticks per beat

    Returns:
        MidiTrack
    """
    track = create_midi_track(track_name, channel)

    current_time_ticks = 0

    for chord in chords:
        chord_notes = chord.get_notes()

        # Calculate start time
        chord_start_ticks = int(max(0, chord.start) * ticks_per_beat)
        chord_duration_ticks = int(max(0.1, chord.duration) * ticks_per_beat)

        # Delta time to chord start
        delta_time = max(0, chord_start_ticks - current_time_ticks)

        # Note on for all chord notes (simultaneously)
        for i, note_pitch in enumerate(chord_notes):
            track.append(Message(
                'note_on',
                note=note_pitch,
                velocity=chord.velocity,
                time=delta_time if i == 0 else 0,  # Only first note has delta
                channel=channel
            ))

        current_time_ticks = chord_start_ticks

        # Note off for all chord notes
        for i, note_pitch in enumerate(chord_notes):
            track.append(Message(
                'note_off',
                note=note_pitch,
                velocity=0,
                time=chord_duration_ticks if i == 0 else 0,
                channel=channel
            ))

        current_time_ticks += chord_duration_ticks

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    return track


def drums_to_midi_track(drum_hits, track_name="Drums", channel=9, ticks_per_beat=480):
    """
    Convert DrumHit objects to MIDI track.

    Args:
        drum_hits: List of DrumHit objects
        track_name: Name of track
        channel: MIDI channel (9 is standard drum channel)
        ticks_per_beat: MIDI ticks per beat

    Returns:
        MidiTrack
    """
    track = create_midi_track(track_name, channel)

    # Sort by start time
    sorted_hits = sorted(drum_hits, key=lambda h: h.start)

    current_time_ticks = 0

    for hit in sorted_hits:
        # Calculate start time
        hit_start_ticks = int(max(0, hit.start) * ticks_per_beat)

        # Delta time
        delta_time = max(0, hit_start_ticks - current_time_ticks)

        # Note on
        track.append(Message(
            'note_on',
            note=hit.sound.value,  # Drum MIDI note
            velocity=hit.velocity,
            time=delta_time,
            channel=channel
        ))

        current_time_ticks = hit_start_ticks

        # Note off (short duration for drums)
        track.append(Message(
            'note_off',
            note=hit.sound.value,
            velocity=0,
            time=int(0.1 * ticks_per_beat),  # 0.1 beat duration
            channel=channel
        ))

        current_time_ticks += int(0.1 * ticks_per_beat)

    # End of track
    track.append(MetaMessage('end_of_track', time=0))

    return track


def main():
    """Generate complete track."""
    print("=" * 70)
    print("SENTINEL MUSIC GENERATOR - Complete Track")
    print("=" * 70)
    print()

    # Configuration
    KEY = 66  # F# minor
    SCALE = Scale.MINOR_PENTATONIC
    BPM = 90
    BARS = 8

    print(f"Key: F# Minor")
    print(f"Scale: Minor Pentatonic")
    print(f"BPM: {BPM}")
    print(f"Bars: {BARS}")
    print()

    # Output directory
    output_dir = Path(__file__).parent.parent / 'music' / 'demos'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / '05_complete_track.mid'

    # Initialize generators
    chord_gen = ChordGenerator(key_root=KEY, scale=Scale.MINOR)
    melody_gen = MelodyGenerator(key_root=KEY, scale=SCALE)
    bass_gen = BassGenerator(key_root=KEY, scale=Scale.MINOR)
    drum_gen = DrumGenerator(bpm=BPM, swing=0.3)

    # Generate chord progression
    print("-" * 70)
    print("1. GENERATING CHORDS")
    print("-" * 70)
    chords = chord_gen.generate_progression("lofi_1", bars=BARS, beats_per_chord=4.0)
    print(f"✓ Generated {len(chords)} chords")
    for chord in chords:
        print(f"    {chord.chord_type.value:10} @ beat {chord.start:4.1f}")
    print()

    # Generate melody
    print("-" * 70)
    print("2. GENERATING MELODY")
    print("-" * 70)
    melody = melody_gen.generate_motif_based(bars=BARS, creativity=0.7)
    melody = melody_gen.humanize(melody, amount=0.4)
    print(f"✓ Generated {len(melody)} notes (motif-based + humanized)")
    print(f"    Note range: MIDI {min(n.pitch for n in melody)}-{max(n.pitch for n in melody)}")
    print()

    # Generate bass
    print("-" * 70)
    print("3. GENERATING BASS")
    print("-" * 70)
    bass = bass_gen.generate_walking(chords)
    print(f"✓ Generated {len(bass)} notes (walking bass)")
    print(f"    Note range: MIDI {min(n.pitch for n in bass)}-{max(n.pitch for n in bass)}")
    print()

    # Generate drums
    print("-" * 70)
    print("4. GENERATING DRUMS")
    print("-" * 70)
    drums = drum_gen.generate_lofi(bars=BARS, complexity=0.6, humanize=0.4)
    print(f"✓ Generated {len(drums)} drum hits")
    print(f"    Sounds used: {len(set(h.sound for h in drums))} different drums")
    print()

    # Create MIDI file
    print("-" * 70)
    print("5. CREATING MIDI FILE")
    print("-" * 70)

    mid = MidiFile()
    ticks_per_beat = mid.ticks_per_beat

    # Add tempo track
    tempo_track = MidiTrack()
    microseconds_per_beat = int(60_000_000 / BPM)
    tempo_track.append(MetaMessage('set_tempo', tempo=microseconds_per_beat))
    tempo_track.append(MetaMessage('end_of_track'))
    mid.tracks.append(tempo_track)

    # Add tracks
    mid.tracks.append(drums_to_midi_track(drums, "Drums", channel=9, ticks_per_beat=ticks_per_beat))
    mid.tracks.append(notes_to_midi_track(bass, "Bass", channel=1, ticks_per_beat=ticks_per_beat))
    mid.tracks.append(chords_to_midi_track(chords, "Chords", channel=2, ticks_per_beat=ticks_per_beat))
    mid.tracks.append(notes_to_midi_track(melody, "Melody", channel=3, ticks_per_beat=ticks_per_beat))

    # Save MIDI file
    mid.save(output_file)
    print(f"✓ Saved: {output_file}")
    print()

    # Summary
    print("=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    print()
    print(f"📁 File: {output_file.name}")
    print(f"📊 Stats:")
    print(f"   • Chords: {len(chords)} ({sum(len(c.get_notes()) for c in chords)} total notes)")
    print(f"   • Melody: {len(melody)} notes")
    print(f"   • Bass: {len(bass)} notes")
    print(f"   • Drums: {len(drums)} hits")
    print(f"   • Total events: {len(chords) + len(melody) + len(bass) + len(drums)}")
    print()
    print("🎧 To listen:")
    print("   1. Open Ableton Live (or any DAW)")
    print("   2. Drag this MIDI file into Ableton")
    print("   3. Load instruments on each track:")
    print("      • Drums → Drum Rack")
    print("      • Bass → Wavetable/Electric")
    print("      • Chords → Piano/Rhodes/Pad")
    print("      • Melody → Synth/Pluck")
    print("   4. Press Play!")
    print()


if __name__ == '__main__':
    main()
