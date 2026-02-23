"""
Melody generator with adjustable creativity levels.

Demonstrates different levels of musical creativity:
- Level 1: Rule-based (basic scales)
- Level 2: Pattern-based with variation
- Level 3: AI-enhanced (would use neural networks)
"""

import random
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum


class NoteLength(Enum):
    """Note durations in beats."""
    WHOLE = 4.0
    HALF = 2.0
    QUARTER = 1.0
    EIGHTH = 0.5
    SIXTEENTH = 0.25


@dataclass
class Note:
    """Musical note representation."""
    pitch: int  # MIDI note number (0-127)
    start: float  # Start time in beats
    duration: float  # Length in beats
    velocity: int  # Volume (0-127)

    def to_midi_tuple(self) -> Tuple[int, float, float, int]:
        """Convert to MIDI format (pitch, start, duration, velocity)."""
        return (self.pitch, self.start, self.duration, self.velocity)


class Scale:
    """Musical scales and modes."""

    # Intervals from root note (semitones)
    MAJOR = [0, 2, 4, 5, 7, 9, 11]
    MINOR = [0, 2, 3, 5, 7, 8, 10]
    MINOR_PENTATONIC = [0, 3, 5, 7, 10]
    MAJOR_PENTATONIC = [0, 2, 4, 7, 9]
    DORIAN = [0, 2, 3, 5, 7, 9, 10]
    MIXOLYDIAN = [0, 2, 4, 5, 7, 9, 10]
    BLUES = [0, 3, 5, 6, 7, 10]

    @staticmethod
    def get_notes(root: int, scale: List[int], octaves: int = 2) -> List[int]:
        """
        Get all notes in a scale across multiple octaves.

        Args:
            root: Root MIDI note number
            scale: Scale intervals
            octaves: Number of octaves to generate

        Returns:
            List of MIDI note numbers
        """
        notes = []
        for octave in range(octaves):
            for interval in scale:
                notes.append(root + interval + (octave * 12))
        return notes


class MelodyGenerator:
    """Generate melodies with different creativity levels."""

    def __init__(self, key_root: int = 60, scale: List[int] = None):
        """
        Initialize melody generator.

        Args:
            key_root: Root note of key (default: C4 = 60)
            scale: Scale intervals (default: minor pentatonic)
        """
        self.key_root = key_root
        self.scale = scale or Scale.MINOR_PENTATONIC
        self.scale_notes = Scale.get_notes(key_root, self.scale, octaves=2)

    def generate_basic(self, bars: int = 4) -> List[Note]:
        """
        Level 1: Basic rule-based melody.

        Very predictable, follows scale strictly, simple rhythm.
        Creativity: 3/10

        Args:
            bars: Number of bars to generate (4 beats per bar)

        Returns:
            List of Note objects
        """
        melody = []
        current_beat = 0.0
        beats_per_bar = 4.0
        total_beats = bars * beats_per_bar

        # Simple ascending/descending pattern
        direction = 1  # 1 = up, -1 = down
        current_note_idx = 0

        while current_beat < total_beats:
            # Use quarter notes only (simple rhythm)
            duration = NoteLength.QUARTER.value

            # Get note from scale
            pitch = self.scale_notes[current_note_idx % len(self.scale_notes)]

            # Constant velocity (no dynamics)
            velocity = 80

            melody.append(Note(pitch, current_beat, duration, velocity))

            # Move up or down scale
            current_note_idx += direction

            # Change direction at octave boundaries
            if current_note_idx >= len(self.scale_notes) - 1:
                direction = -1
            elif current_note_idx <= 0:
                direction = 1

            current_beat += duration

        return melody

    def generate_varied(
        self,
        bars: int = 4,
        creativity: float = 0.6
    ) -> List[Note]:
        """
        Level 2: Pattern-based with variation.

        Uses rhythm variation, melodic contours, dynamics.
        Creativity: 6/10

        Args:
            bars: Number of bars to generate
            creativity: 0.0-1.0 (higher = more variation)

        Returns:
            List of Note objects
        """
        melody = []
        current_beat = 0.0
        beats_per_bar = 4.0
        total_beats = bars * beats_per_bar

        # Rhythm options (weighted by commonality)
        rhythms = [
            (NoteLength.QUARTER.value, 0.4),  # Most common
            (NoteLength.EIGHTH.value, 0.3),
            (NoteLength.HALF.value, 0.2),
            (NoteLength.SIXTEENTH.value, 0.1)
        ]

        # Melodic motion patterns
        previous_pitch_idx = len(self.scale_notes) // 2  # Start middle

        while current_beat < total_beats:
            # Choose rhythm (more variation with higher creativity)
            if random.random() < creativity:
                duration = random.choices(
                    [r[0] for r in rhythms],
                    weights=[r[1] for r in rhythms]
                )[0]
            else:
                duration = NoteLength.QUARTER.value

            # Melodic movement (prefer steps, occasional leaps)
            if random.random() < creativity:
                # Occasional leap (3-5 scale degrees)
                movement = random.choice([-5, -4, -3, 3, 4, 5])
            else:
                # Stepwise motion (-2 to +2 scale degrees)
                movement = random.choice([-2, -1, 0, 1, 2])

            next_pitch_idx = previous_pitch_idx + movement
            next_pitch_idx = max(0, min(next_pitch_idx, len(self.scale_notes) - 1))

            pitch = self.scale_notes[next_pitch_idx]

            # Dynamic velocity (with variation)
            base_velocity = 80
            velocity_variation = int(creativity * 30)
            velocity = base_velocity + random.randint(-velocity_variation, velocity_variation)
            velocity = max(40, min(velocity, 120))

            melody.append(Note(pitch, current_beat, duration, velocity))

            previous_pitch_idx = next_pitch_idx
            current_beat += duration

            # Don't exceed total beats
            if current_beat >= total_beats:
                break

        return melody

    def generate_motif_based(
        self,
        bars: int = 8,
        creativity: float = 0.7
    ) -> List[Note]:
        """
        Level 2.5: Motif-based composition.

        Creates a short motif and develops it with variations.
        Creativity: 7/10

        Args:
            bars: Number of bars to generate
            creativity: 0.0-1.0 (affects variation intensity)

        Returns:
            List of Note objects
        """
        # Generate 1-bar motif
        motif = self._generate_motif(bars=1, creativity=creativity)

        melody = []
        current_beat = 0.0
        beats_per_bar = 4.0
        total_beats = bars * beats_per_bar

        variation_types = ['original', 'transposed', 'rhythmic', 'inverted']

        bar_num = 0
        while current_beat < total_beats:
            # Choose variation type
            if bar_num == 0 or random.random() > creativity:
                # Original motif
                variation = motif
            else:
                # Apply variation
                var_type = random.choice(variation_types)
                variation = self._vary_motif(motif, var_type, creativity)

            # Add variation to melody (offset by current_beat)
            for note in variation:
                new_note = Note(
                    note.pitch,
                    current_beat + note.start,
                    note.duration,
                    note.velocity
                )
                melody.append(new_note)

            current_beat += beats_per_bar
            bar_num += 1

        return melody

    def _generate_motif(self, bars: int = 1, creativity: float = 0.6) -> List[Note]:
        """Generate a short musical motif (1-2 bars)."""
        # Use varied generation for motif
        return self.generate_varied(bars=bars, creativity=creativity)

    def _vary_motif(
        self,
        motif: List[Note],
        variation_type: str,
        intensity: float
    ) -> List[Note]:
        """
        Apply variation to a motif.

        Args:
            motif: Original motif
            variation_type: Type of variation
            intensity: How much to vary (0.0-1.0)

        Returns:
            Varied motif
        """
        if variation_type == 'original':
            return motif

        varied = []

        for note in motif:
            if variation_type == 'transposed':
                # Transpose up/down by scale degrees
                transpose = random.choice([-3, -2, 2, 3]) if random.random() < intensity else 0
                # Find pitch in scale and transpose
                try:
                    idx = self.scale_notes.index(note.pitch)
                    new_idx = (idx + transpose) % len(self.scale_notes)
                    new_pitch = self.scale_notes[new_idx]
                except ValueError:
                    new_pitch = note.pitch

                varied.append(Note(new_pitch, note.start, note.duration, note.velocity))

            elif variation_type == 'rhythmic':
                # Vary rhythm
                if random.random() < intensity:
                    new_duration = random.choice([0.5, 1.0, 2.0])
                else:
                    new_duration = note.duration

                varied.append(Note(note.pitch, note.start, new_duration, note.velocity))

            elif variation_type == 'inverted':
                # Melodic inversion (flip intervals)
                if len(varied) > 0:
                    prev_note = varied[-1]
                    interval = note.pitch - prev_note.pitch
                    new_pitch = prev_note.pitch - interval
                    # Keep in scale
                    closest = min(self.scale_notes, key=lambda x: abs(x - new_pitch))
                    varied.append(Note(closest, note.start, note.duration, note.velocity))
                else:
                    varied.append(note)

            else:
                varied.append(note)

        return varied

    def humanize(self, melody: List[Note], amount: float = 0.3) -> List[Note]:
        """
        Add human-like imperfections.

        Args:
            melody: Original melody
            amount: How much to humanize (0.0-1.0)

        Returns:
            Humanized melody
        """
        humanized = []

        for note in melody:
            # Timing variation (±amount * 0.05 beats)
            timing_var = random.uniform(-amount * 0.05, amount * 0.05)
            new_start = max(0, note.start + timing_var)

            # Velocity variation (±amount * 20)
            velocity_var = int(random.uniform(-amount * 20, amount * 20))
            new_velocity = max(40, min(120, note.velocity + velocity_var))

            # Slight duration variation
            duration_var = random.uniform(-amount * 0.05, amount * 0.05)
            new_duration = max(0.1, note.duration + duration_var)

            humanized.append(Note(
                note.pitch,
                new_start,
                new_duration,
                new_velocity
            ))

        return humanized


# Example usage
if __name__ == '__main__':
    # Create generator in F# minor (Nujabes territory)
    generator = MelodyGenerator(key_root=66, scale=Scale.MINOR_PENTATONIC)

    print("Generating 3 melodies with different creativity levels...\n")

    # Level 1: Basic (boring but correct)
    print("1. BASIC MELODY (Creativity: 3/10)")
    basic = generator.generate_basic(bars=4)
    print(f"   Generated {len(basic)} notes")
    print(f"   First 3 notes: {[n.pitch for n in basic[:3]]}")

    # Level 2: Varied (interesting)
    print("\n2. VARIED MELODY (Creativity: 6/10)")
    varied = generator.generate_varied(bars=4, creativity=0.6)
    print(f"   Generated {len(varied)} notes")
    print(f"   First 3 notes: {[n.pitch for n in varied[:3]]}")

    # Level 3: Motif-based (creative)
    print("\n3. MOTIF-BASED (Creativity: 7/10)")
    motif = generator.generate_motif_based(bars=8, creativity=0.7)
    print(f"   Generated {len(motif)} notes")
    print(f"   First 3 notes: {[n.pitch for n in motif[:3]]}")

    # Humanize
    print("\n4. HUMANIZED VERSION")
    humanized = generator.humanize(motif, amount=0.4)
    print(f"   Added timing and velocity variations")
    print(f"   Velocity range: {min(n.velocity for n in humanized)}-{max(n.velocity for n in humanized)}")
