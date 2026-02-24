"""
Bass line generator that follows chord progressions.

Generates bass lines that:
- Follow the root notes of chords
- Add rhythmic variation
- Include passing tones and approach notes
- Support different genres (walking bass, synth bass, etc.)
"""

import random
from typing import List
from dataclasses import dataclass

from .chord_generator import Chord, ChordType
from .melody_generator import Scale, Note


class BassGenerator:
    """Generate bass lines that follow chord progressions."""

    def __init__(self, key_root: int = 60, scale: List[int] = None):
        """
        Initialize bass generator.

        Args:
            key_root: Root note of key (default: C4 = 60)
            scale: Scale intervals (default: minor pentatonic)
        """
        self.key_root = key_root
        self.scale = scale or Scale.MINOR_PENTATONIC
        self.scale_notes = self._get_scale_notes()

    def _get_scale_notes(self) -> List[int]:
        """Get notes in the scale across 2 octaves (for bass range)."""
        notes = []
        # Bass range: 2 octaves down from key root
        bass_root = self.key_root - 24  # Two octaves down

        for octave in range(3):  # 3 octaves for bass range
            for interval in self.scale:
                notes.append(bass_root + interval + (octave * 12))

        return notes

    def generate_simple(
        self,
        chords: List[Chord],
        velocity: int = 90
    ) -> List[Note]:
        """
        Generate simple bass line (root notes on downbeats).

        Args:
            chords: Chord progression to follow
            velocity: Note velocity

        Returns:
            List of bass notes
        """
        bass_notes = []

        for chord in chords:
            # Play root note on downbeat
            bass_root = chord.root - 12  # One octave down

            bass_notes.append(Note(
                pitch=bass_root,
                start=chord.start,
                duration=chord.duration,
                velocity=velocity
            ))

        return bass_notes

    def generate_walking(
        self,
        chords: List[Chord],
        velocity: int = 85
    ) -> List[Note]:
        """
        Generate walking bass line (jazz-style).

        Plays quarter notes that walk through chord tones and
        scale notes to connect chords smoothly.

        Args:
            chords: Chord progression to follow
            velocity: Note velocity

        Returns:
            List of bass notes
        """
        bass_notes = []

        for i, chord in enumerate(chords):
            chord_root = chord.root - 12  # One octave down
            chord_notes = [n - 12 for n in chord.get_notes()]  # Chord tones in bass range

            # Number of beats in this chord
            num_beats = int(chord.duration)

            for beat_idx in range(num_beats):
                beat_time = chord.start + beat_idx

                if beat_idx == 0:
                    # Always start with root
                    note_pitch = chord_root
                elif beat_idx == num_beats - 1 and i < len(chords) - 1:
                    # Last beat: approach next chord
                    next_root = chords[i + 1].root - 12
                    # Play note one semitone below next root (chromatic approach)
                    note_pitch = next_root - 1
                else:
                    # Middle beats: use chord tones or scale notes
                    if random.random() < 0.7:
                        # Use chord tone
                        note_pitch = random.choice(chord_notes)
                    else:
                        # Use scale note
                        note_pitch = self._find_nearest_scale_note(chord_root)

                bass_notes.append(Note(
                    pitch=note_pitch,
                    start=beat_time,
                    duration=1.0,  # Quarter note
                    velocity=velocity + random.randint(-5, 5)  # Slight variation
                ))

        return bass_notes

    def generate_synth_bass(
        self,
        chords: List[Chord],
        pattern: str = "standard",
        velocity: int = 100
    ) -> List[Note]:
        """
        Generate synth bass pattern (electronic music style).

        Args:
            chords: Chord progression to follow
            pattern: Rhythm pattern
                - "standard": Root on downbeat, octave jump
                - "16ths": Fast 16th note pattern
                - "offbeat": Syncopated pattern
            velocity: Note velocity

        Returns:
            List of bass notes
        """
        bass_notes = []

        for chord in chords:
            chord_root = chord.root - 12  # One octave down
            chord_notes = [n - 12 for n in chord.get_notes()]

            if pattern == "standard":
                # Root on downbeat, then octave up
                bass_notes.append(Note(
                    pitch=chord_root,
                    start=chord.start,
                    duration=0.5,
                    velocity=velocity
                ))

                bass_notes.append(Note(
                    pitch=chord_root + 12,  # Octave up
                    start=chord.start + 0.5,
                    duration=0.5,
                    velocity=velocity - 20
                ))

            elif pattern == "16ths":
                # Fast 16th note pattern
                sixteenths_per_chord = int(chord.duration * 4)

                for i in range(sixteenths_per_chord):
                    beat = chord.start + (i * 0.25)

                    # Alternate root and fifth
                    if i % 2 == 0:
                        note_pitch = chord_root
                        vel = velocity
                    else:
                        # Use 5th if available in chord
                        if len(chord_notes) >= 2:
                            note_pitch = chord_notes[1]
                        else:
                            note_pitch = chord_root
                        vel = velocity - 30

                    bass_notes.append(Note(
                        pitch=note_pitch,
                        start=beat,
                        duration=0.25,
                        velocity=vel
                    ))

            elif pattern == "offbeat":
                # Syncopated pattern
                # Play on offbeats (0.5, 1.5, 2.5, 3.5)
                offbeats = [0.5, 1.5, 2.5, 3.5]

                for i, offbeat in enumerate(offbeats):
                    if chord.start + offbeat < chord.start + chord.duration:
                        bass_notes.append(Note(
                            pitch=chord_root,
                            start=chord.start + offbeat,
                            duration=0.25,
                            velocity=velocity - 10
                        ))

        return bass_notes

    def generate_funk(
        self,
        chords: List[Chord],
        velocity: int = 95
    ) -> List[Note]:
        """
        Generate funk bass line (syncopated, rhythmic).

        Args:
            chords: Chord progression to follow
            velocity: Note velocity

        Returns:
            List of bass notes
        """
        bass_notes = []

        funk_pattern = [
            (0.0, 1.0, True),    # Beat 1 (root, emphasized)
            (1.0, 0.5, False),   # Beat 2 (fifth)
            (1.75, 0.25, False), # Syncopation
            (2.0, 0.5, True),    # Beat 3 (root)
            (2.75, 0.25, False), # Syncopation
            (3.5, 0.5, False),   # Off-beat
        ]

        for chord in chords:
            chord_root = chord.root - 12
            chord_notes = [n - 12 for n in chord.get_notes()]

            for offset, duration, is_root in funk_pattern:
                if offset < chord.duration:
                    if is_root:
                        note_pitch = chord_root
                        vel = velocity
                    else:
                        # Use chord tones
                        if len(chord_notes) >= 2:
                            note_pitch = random.choice(chord_notes[1:])  # Not root
                        else:
                            note_pitch = chord_root
                        vel = velocity - 20

                    bass_notes.append(Note(
                        pitch=note_pitch,
                        start=chord.start + offset,
                        duration=duration,
                        velocity=vel
                    ))

        return bass_notes

    def _find_nearest_scale_note(self, target: int) -> int:
        """Find nearest scale note to target pitch."""
        return min(self.scale_notes, key=lambda x: abs(x - target))


# Example usage
if __name__ == '__main__':
    from .chord_generator import ChordGenerator

    print("=" * 70)
    print("BASS LINE GENERATOR DEMO")
    print("=" * 70)

    # Create chord progression (F# minor)
    chord_gen = ChordGenerator(key_root=66, scale=Scale.MINOR)
    chords = chord_gen.generate_progression("lofi_1", bars=4)

    print("\nChord Progression:")
    for chord in chords:
        print(f"  {chord.chord_type.value:10} | Root: {chord.root} | Start: {chord.start}")

    # Initialize bass generator
    bass_gen = BassGenerator(key_root=66, scale=Scale.MINOR)

    # 1. Simple bass
    print("\n1. SIMPLE BASS (roots on downbeats)")
    simple_bass = bass_gen.generate_simple(chords)
    print(f"   Generated {len(simple_bass)} notes")
    for note in simple_bass[:4]:
        print(f"     Pitch: {note.pitch} | Start: {note.start} | Dur: {note.duration}")

    # 2. Walking bass
    print("\n2. WALKING BASS (jazz-style)")
    walking_bass = bass_gen.generate_walking(chords)
    print(f"   Generated {len(walking_bass)} notes")
    for note in walking_bass[:8]:
        print(f"     Pitch: {note.pitch} | Start: {note.start} | Dur: {note.duration}")

    # 3. Synth bass
    print("\n3. SYNTH BASS (16th note pattern)")
    synth_bass = bass_gen.generate_synth_bass(chords, pattern="16ths")
    print(f"   Generated {len(synth_bass)} notes")
    for note in synth_bass[:8]:
        print(f"     Pitch: {note.pitch} | Start: {note.start:5.2f} | Dur: {note.duration}")

    # 4. Funk bass
    print("\n4. FUNK BASS (syncopated)")
    funk_bass = bass_gen.generate_funk(chords)
    print(f"   Generated {len(funk_bass)} notes")
    for note in funk_bass[:8]:
        print(f"     Pitch: {note.pitch} | Start: {note.start:5.2f} | Dur: {note.duration}")

    print("\n" + "=" * 70)
    total = len(simple_bass) + len(walking_bass) + len(synth_bass) + len(funk_bass)
    print(f"TOTAL: {total} bass notes generated")
    print("=" * 70)
