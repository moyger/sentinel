"""
Chord progression generator with multiple genres and styles.

Generates chord progressions for different musical contexts:
- Pop/Rock progressions
- Jazz progressions
- Lo-fi/Hip-hop progressions
- Custom progressions
"""

import random
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

from .melody_generator import Scale


class ChordType(Enum):
    """Common chord types."""
    MAJOR = "major"
    MINOR = "minor"
    DOMINANT_7 = "dom7"
    MAJOR_7 = "maj7"
    MINOR_7 = "min7"
    DIMINISHED = "dim"
    AUGMENTED = "aug"


@dataclass
class Chord:
    """Chord representation."""
    root: int  # MIDI note number
    chord_type: ChordType
    start: float  # Start time in beats
    duration: float  # Length in beats
    velocity: int  # Volume (0-127)

    def get_notes(self) -> List[int]:
        """Get MIDI note numbers for this chord."""
        intervals = CHORD_INTERVALS[self.chord_type]
        return [self.root + interval for interval in intervals]


# Chord intervals (semitones from root)
CHORD_INTERVALS = {
    ChordType.MAJOR: [0, 4, 7],
    ChordType.MINOR: [0, 3, 7],
    ChordType.DOMINANT_7: [0, 4, 7, 10],
    ChordType.MAJOR_7: [0, 4, 7, 11],
    ChordType.MINOR_7: [0, 3, 7, 10],
    ChordType.DIMINISHED: [0, 3, 6],
    ChordType.AUGMENTED: [0, 4, 8],
}


# Common progressions (in scale degrees)
PROGRESSIONS = {
    # Pop/Rock
    "pop_1": [1, 5, 6, 4],      # I-V-vi-IV (very common: Let It Be, Don't Stop Believin')
    "pop_2": [1, 4, 5, 1],      # I-IV-V-I (classic rock)
    "pop_3": [6, 4, 1, 5],      # vi-IV-I-V (emotional pop)
    "pop_4": [1, 6, 4, 5],      # I-vi-IV-V (50s progression)

    # Lo-fi / Hip-hop
    "lofi_1": [2, 5, 1],        # ii-V-I (jazz-influenced)
    "lofi_2": [6, 4, 5, 1],     # vi-IV-V-I
    "lofi_3": [1, 3, 6, 4],     # I-iii-vi-IV
    "lofi_4": [2, 5, 1, 6],     # ii-V-I-vi

    # Jazz
    "jazz_1": [2, 5, 1],        # ii-V-I (most common jazz)
    "jazz_2": [3, 6, 2, 5, 1],  # iii-vi-ii-V-I
    "jazz_3": [1, 6, 2, 5],     # I-vi-ii-V (turnaround)
    "jazz_4": [6, 2, 5, 1],     # vi-ii-V-I (minor ii-V-I)

    # Sad/Emotional
    "sad_1": [6, 4, 1, 5],      # vi-IV-I-V (melancholic)
    "sad_2": [1, 6, 3, 4],      # I-vi-iii-IV
    "sad_3": [6, 2, 5, 1],      # vi-ii-V-I
}


class ChordGenerator:
    """Generate chord progressions for different styles."""

    def __init__(self, key_root: int = 60, scale: List[int] = None):
        """
        Initialize chord generator.

        Args:
            key_root: Root note of key (default: C4 = 60)
            scale: Scale intervals (default: major scale)
        """
        self.key_root = key_root
        self.scale = scale or Scale.MAJOR
        self.scale_notes = self._get_scale_notes()

    def _get_scale_notes(self) -> List[int]:
        """Get notes in the scale (one octave)."""
        return [self.key_root + interval for interval in self.scale]

    def _scale_degree_to_midi(self, degree: int) -> int:
        """
        Convert scale degree (1-7) to MIDI note.

        Args:
            degree: Scale degree (1-based)

        Returns:
            MIDI note number
        """
        # Adjust to 0-based index
        index = (degree - 1) % len(self.scale_notes)
        return self.scale_notes[index]

    def _get_chord_type_for_degree(self, degree: int, genre: str = "pop") -> ChordType:
        """
        Determine chord type based on scale degree and genre.

        In major scale:
        - I, IV, V = Major
        - ii, iii, vi = Minor
        - vii = Diminished

        Args:
            degree: Scale degree (1-7)
            genre: Music genre

        Returns:
            Chord type
        """
        # Normalize degree to 1-7
        degree_normalized = ((degree - 1) % 7) + 1

        if genre in ["jazz", "lofi"]:
            # Use 7th chords for jazz/lofi
            if degree_normalized in [1, 4]:
                return ChordType.MAJOR_7
            elif degree_normalized in [2, 3, 6]:
                return ChordType.MINOR_7
            elif degree_normalized == 5:
                return ChordType.DOMINANT_7
            else:
                return ChordType.MINOR_7
        else:
            # Use triads for pop/rock
            if degree_normalized in [1, 4, 5]:
                return ChordType.MAJOR
            elif degree_normalized in [2, 3, 6]:
                return ChordType.MINOR
            else:
                return ChordType.DIMINISHED

    def generate_progression(
        self,
        progression_name: str = "pop_1",
        bars: int = 4,
        beats_per_chord: float = 4.0,
        velocity: int = 70
    ) -> List[Chord]:
        """
        Generate a chord progression from a preset.

        Args:
            progression_name: Name of progression preset
            bars: Number of bars
            beats_per_chord: Beats per chord
            velocity: Chord velocity

        Returns:
            List of Chord objects
        """
        if progression_name not in PROGRESSIONS:
            raise ValueError(f"Unknown progression: {progression_name}")

        pattern = PROGRESSIONS[progression_name]
        genre = progression_name.split("_")[0]  # Extract genre from name

        chords = []
        current_beat = 0.0
        total_beats = bars * 4.0

        while current_beat < total_beats:
            # Cycle through progression pattern
            for degree in pattern:
                if current_beat >= total_beats:
                    break

                root = self._scale_degree_to_midi(degree)
                chord_type = self._get_chord_type_for_degree(degree, genre)

                chord = Chord(
                    root=root,
                    chord_type=chord_type,
                    start=current_beat,
                    duration=beats_per_chord,
                    velocity=velocity
                )

                chords.append(chord)
                current_beat += beats_per_chord

        return chords

    def generate_custom(
        self,
        degrees: List[int],
        bars: int = 4,
        beats_per_chord: float = 4.0,
        chord_types: List[ChordType] = None,
        velocity: int = 70
    ) -> List[Chord]:
        """
        Generate custom chord progression.

        Args:
            degrees: List of scale degrees (1-7)
            bars: Number of bars
            beats_per_chord: Beats per chord
            chord_types: Optional list of chord types (auto-detected if None)
            velocity: Chord velocity

        Returns:
            List of Chord objects
        """
        chords = []
        current_beat = 0.0
        total_beats = bars * 4.0

        while current_beat < total_beats:
            for i, degree in enumerate(degrees):
                if current_beat >= total_beats:
                    break

                root = self._scale_degree_to_midi(degree)

                # Use provided chord type or auto-detect
                if chord_types and i < len(chord_types):
                    chord_type = chord_types[i]
                else:
                    chord_type = self._get_chord_type_for_degree(degree)

                chord = Chord(
                    root=root,
                    chord_type=chord_type,
                    start=current_beat,
                    duration=beats_per_chord,
                    velocity=velocity
                )

                chords.append(chord)
                current_beat += beats_per_chord

        return chords

    def add_variation(
        self,
        chords: List[Chord],
        variation_type: str = "rhythm"
    ) -> List[Chord]:
        """
        Add variation to chord progression.

        Args:
            chords: Original chord progression
            variation_type: Type of variation
                - "rhythm": Vary rhythm (half notes, quarter notes)
                - "inversion": Use chord inversions
                - "substitution": Substitute similar chords

        Returns:
            Varied chord progression
        """
        varied = []

        for chord in chords:
            if variation_type == "rhythm":
                # Randomly split chords into shorter durations
                if random.random() < 0.3 and chord.duration >= 2.0:
                    # Split into two chords
                    half_duration = chord.duration / 2
                    varied.append(Chord(
                        chord.root, chord.chord_type, chord.start,
                        half_duration, chord.velocity
                    ))
                    varied.append(Chord(
                        chord.root, chord.chord_type,
                        chord.start + half_duration,
                        half_duration, chord.velocity
                    ))
                else:
                    varied.append(chord)

            elif variation_type == "substitution":
                # Randomly substitute chords with similar ones
                if random.random() < 0.2:
                    # Substitute major with major7, minor with minor7
                    if chord.chord_type == ChordType.MAJOR:
                        new_chord = Chord(
                            chord.root, ChordType.MAJOR_7, chord.start,
                            chord.duration, chord.velocity
                        )
                        varied.append(new_chord)
                    elif chord.chord_type == ChordType.MINOR:
                        new_chord = Chord(
                            chord.root, ChordType.MINOR_7, chord.start,
                            chord.duration, chord.velocity
                        )
                        varied.append(new_chord)
                    else:
                        varied.append(chord)
                else:
                    varied.append(chord)

            else:
                varied.append(chord)

        return varied


# Example usage
if __name__ == '__main__':
    # Create generator in F# minor
    generator = ChordGenerator(key_root=66, scale=Scale.MINOR)

    print("Chord Progression Generator Demo\n")
    print("=" * 70)

    # Generate lo-fi progression
    print("\n1. Lo-fi Progression (ii-V-I)")
    lofi_chords = generator.generate_progression("lofi_1", bars=4)

    for chord in lofi_chords:
        notes = chord.get_notes()
        print(f"  {chord.chord_type.value:10} | Start: {chord.start:4.1f} | Notes: {notes}")

    # Generate pop progression
    print("\n2. Pop Progression (I-V-vi-IV)")
    pop_chords = generator.generate_progression("pop_1", bars=4)

    for chord in pop_chords:
        notes = chord.get_notes()
        print(f"  {chord.chord_type.value:10} | Start: {chord.start:4.1f} | Notes: {notes}")

    # Generate custom progression
    print("\n3. Custom Progression (I-vi-IV-V)")
    custom_chords = generator.generate_custom(
        degrees=[1, 6, 4, 5],
        bars=4,
        beats_per_chord=4.0
    )

    for chord in custom_chords:
        notes = chord.get_notes()
        print(f"  {chord.chord_type.value:10} | Start: {chord.start:4.1f} | Notes: {notes}")

    print("\n" + "=" * 70)
    print(f"Total chords generated: {len(lofi_chords) + len(pop_chords) + len(custom_chords)}")
