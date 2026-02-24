"""
Drum pattern generator for different genres.

Generates realistic drum patterns with:
- Genre-specific patterns (lo-fi, house, trap, etc.)
- Swing and humanization
- Velocity variations
- Ghost notes and fills
"""

import random
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class DrumSound(Enum):
    """Standard drum kit sounds (General MIDI mapping)."""
    KICK = 36           # Bass Drum 1
    SNARE = 38          # Acoustic Snare
    CLAP = 39           # Hand Clap
    CLOSED_HAT = 42     # Closed Hi-Hat
    OPEN_HAT = 46       # Open Hi-Hat
    CRASH = 49          # Crash Cymbal 1
    RIDE = 51           # Ride Cymbal 1
    TOM_LOW = 45        # Low Tom
    TOM_MID = 47        # Mid Tom
    TOM_HIGH = 50       # High Tom
    RIM = 37            # Side Stick/Rimshot


@dataclass
class DrumHit:
    """Single drum hit."""
    sound: DrumSound
    start: float        # Start time in beats
    velocity: int       # Volume (0-127)


class DrumGenerator:
    """Generate drum patterns for different genres."""

    def __init__(self, bpm: int = 90, swing: float = 0.0):
        """
        Initialize drum generator.

        Args:
            bpm: Tempo in beats per minute
            swing: Swing amount (0.0 = straight, 0.5 = triplet swing, 1.0 = heavy swing)
        """
        self.bpm = bpm
        self.swing = swing

    def _apply_swing(self, beat: float) -> float:
        """
        Apply swing to beat position.

        Swing delays the off-beats (0.5, 1.5, 2.5, etc).

        Args:
            beat: Original beat position

        Returns:
            Swung beat position
        """
        if self.swing == 0:
            return beat

        # Check if this is an off-beat (x.5)
        fractional = beat - int(beat)
        if abs(fractional - 0.5) < 0.01:  # Is an off-beat
            # Delay by swing amount
            return int(beat) + 0.5 + (self.swing * 0.16)  # 16th note swing
        else:
            return beat

    def generate_lofi(
        self,
        bars: int = 4,
        complexity: float = 0.5,
        humanize: float = 0.3
    ) -> List[DrumHit]:
        """
        Generate lo-fi / boom-bap drum pattern.

        Characteristics:
        - Laid-back kick pattern
        - Snare on 2 and 4
        - Sparse hi-hats
        - Ghost notes

        Args:
            bars: Number of bars
            complexity: Pattern complexity (0-1)
            humanize: Humanization amount (0-1)

        Returns:
            List of drum hits
        """
        pattern = []
        total_beats = bars * 4.0

        for bar in range(bars):
            bar_start = bar * 4.0

            # Kick pattern (lo-fi: kick on 1, sometimes 3.5)
            pattern.append(DrumHit(DrumSound.KICK, bar_start + 0.0, 100))

            if random.random() < 0.7:  # 70% chance
                pattern.append(DrumHit(DrumSound.KICK, bar_start + 2.5, 85))

            # Snare on 2 and 4 (classic backbeat)
            pattern.append(DrumHit(DrumSound.SNARE, bar_start + 1.0, 95))
            pattern.append(DrumHit(DrumSound.SNARE, bar_start + 3.0, 95))

            # Hi-hats (8th notes, sparse for lo-fi)
            for i in range(8):
                beat = bar_start + (i * 0.5)
                beat_swung = self._apply_swing(beat)

                # Not every hat hit (lo-fi is sparse)
                if random.random() < (0.6 + complexity * 0.3):
                    # Alternate closed/open
                    if i % 4 == 0:
                        hat_sound = DrumSound.CLOSED_HAT
                        velocity = 65
                    else:
                        hat_sound = DrumSound.CLOSED_HAT
                        velocity = 45 + int(random.random() * 15)  # Variation

                    pattern.append(DrumHit(hat_sound, beat_swung, velocity))

            # Ghost notes (quiet snare hits)
            if complexity > 0.5:
                ghost_positions = [0.75, 1.75, 2.75]
                for pos in ghost_positions:
                    if random.random() < 0.4:
                        pattern.append(DrumHit(
                            DrumSound.SNARE,
                            bar_start + pos,
                            30 + int(random.random() * 15)
                        ))

        # Apply humanization
        if humanize > 0:
            pattern = self._humanize_pattern(pattern, humanize)

        return pattern

    def generate_house(
        self,
        bars: int = 4,
        complexity: float = 0.6
    ) -> List[DrumHit]:
        """
        Generate house / dance drum pattern.

        Characteristics:
        - Four-on-the-floor kick
        - Claps/snares on 2 and 4
        - Constant hi-hats (16th notes)
        - Open hat on off-beats

        Args:
            bars: Number of bars
            complexity: Pattern complexity (0-1)

        Returns:
            List of drum hits
        """
        pattern = []

        for bar in range(bars):
            bar_start = bar * 4.0

            # Four-on-the-floor kick (every quarter note)
            for i in range(4):
                pattern.append(DrumHit(
                    DrumSound.KICK,
                    bar_start + i,
                    110 + int(random.random() * 10)
                ))

            # Clap/snare on 2 and 4
            pattern.append(DrumHit(DrumSound.CLAP, bar_start + 1.0, 100))
            pattern.append(DrumHit(DrumSound.CLAP, bar_start + 3.0, 100))

            # Hi-hats (16th notes for house energy)
            for i in range(16):
                beat = bar_start + (i * 0.25)

                # Closed hats
                if i % 2 == 0:  # 8th notes
                    pattern.append(DrumHit(DrumSound.CLOSED_HAT, beat, 70))
                elif complexity > 0.5:  # 16th notes on complex
                    pattern.append(DrumHit(DrumSound.CLOSED_HAT, beat, 50))

            # Open hat on off-beats (house signature)
            if complexity > 0.4:
                for i in [0.5, 1.5, 2.5, 3.5]:
                    if random.random() < 0.7:
                        pattern.append(DrumHit(DrumSound.OPEN_HAT, bar_start + i, 60))

        return pattern

    def generate_trap(
        self,
        bars: int = 4,
        complexity: float = 0.7
    ) -> List[DrumHit]:
        """
        Generate trap / hip-hop drum pattern.

        Characteristics:
        - Heavy kick with rolls
        - Snappy snare
        - Fast hi-hat rolls
        - 808-style patterns

        Args:
            bars: Number of bars
            complexity: Pattern complexity (0-1)

        Returns:
            List of drum hits
        """
        pattern = []

        for bar in range(bars):
            bar_start = bar * 4.0

            # Kick pattern (trap: syncopated)
            kick_pattern = [0.0, 1.5, 2.5]
            for pos in kick_pattern:
                pattern.append(DrumHit(DrumSound.KICK, bar_start + pos, 110))

            # Kick rolls (32nd notes)
            if complexity > 0.6 and random.random() < 0.5:
                roll_start = bar_start + 3.75
                for i in range(2):
                    pattern.append(DrumHit(
                        DrumSound.KICK,
                        roll_start + (i * 0.125),
                        90 + (i * 10)
                    ))

            # Snare on 2 and 4
            pattern.append(DrumHit(DrumSound.SNARE, bar_start + 1.0, 105))
            pattern.append(DrumHit(DrumSound.SNARE, bar_start + 3.0, 105))

            # Hi-hat rolls (trap signature)
            if complexity > 0.5:
                # 32nd note rolls
                for i in range(16):
                    beat = bar_start + (i * 0.25)

                    # Regular hats
                    if i % 2 == 0:
                        pattern.append(DrumHit(DrumSound.CLOSED_HAT, beat, 75))

                    # Rolls on last half beat of each bar
                    if i >= 12:  # Last beat
                        for j in range(2):
                            roll_beat = beat + (j * 0.125)
                            pattern.append(DrumHit(
                                DrumSound.CLOSED_HAT,
                                roll_beat,
                                60 + (j * 10)
                            ))

        return pattern

    def add_fill(
        self,
        pattern: List[DrumHit],
        bar_number: int,
        fill_type: str = "tom"
    ) -> List[DrumHit]:
        """
        Add drum fill at specified bar.

        Args:
            pattern: Existing drum pattern
            bar_number: Which bar to add fill (0-based)
            fill_type: Type of fill ("tom", "snare", "crash")

        Returns:
            Pattern with fill added
        """
        bar_start = bar_number * 4.0
        fill_start = bar_start + 3.0  # Last beat of bar

        if fill_type == "tom":
            # Tom roll (high to low)
            tom_sequence = [DrumSound.TOM_HIGH, DrumSound.TOM_MID, DrumSound.TOM_MID, DrumSound.TOM_LOW]
            for i, tom in enumerate(tom_sequence):
                beat = fill_start + (i * 0.25)
                pattern.append(DrumHit(tom, beat, 90 + (i * 5)))

        elif fill_type == "snare":
            # Snare roll (16th notes)
            for i in range(4):
                beat = fill_start + (i * 0.25)
                pattern.append(DrumHit(DrumSound.SNARE, beat, 80 + (i * 10)))

        elif fill_type == "crash":
            # Crash on downbeat of next bar
            pattern.append(DrumHit(DrumSound.CRASH, bar_start + 4.0, 110))

        return pattern

    def _humanize_pattern(
        self,
        pattern: List[DrumHit],
        amount: float
    ) -> List[DrumHit]:
        """
        Add human-like imperfections.

        Args:
            pattern: Original pattern
            amount: Humanization amount (0-1)

        Returns:
            Humanized pattern
        """
        humanized = []

        for hit in pattern:
            # Timing variation (±amount * 0.03 beats)
            timing_var = random.uniform(-amount * 0.03, amount * 0.03)
            new_start = max(0, hit.start + timing_var)

            # Velocity variation (±amount * 15)
            velocity_var = int(random.uniform(-amount * 15, amount * 15))
            new_velocity = max(20, min(127, hit.velocity + velocity_var))

            humanized.append(DrumHit(
                hit.sound,
                new_start,
                new_velocity
            ))

        return humanized


# Example usage
if __name__ == '__main__':
    print("=" * 70)
    print("DRUM PATTERN GENERATOR DEMO")
    print("=" * 70)

    # Generate lo-fi pattern
    print("\n1. LO-FI PATTERN (90 BPM, swing)")
    lofi_gen = DrumGenerator(bpm=90, swing=0.3)
    lofi_pattern = lofi_gen.generate_lofi(bars=2, complexity=0.6, humanize=0.4)

    print(f"   Generated {len(lofi_pattern)} drum hits")
    print("   First 10 hits:")
    for hit in lofi_pattern[:10]:
        print(f"     {hit.sound.name:12} | Beat: {hit.start:5.2f} | Vel: {hit.velocity:3d}")

    # Generate house pattern
    print("\n2. HOUSE PATTERN (128 BPM, no swing)")
    house_gen = DrumGenerator(bpm=128, swing=0.0)
    house_pattern = house_gen.generate_house(bars=2, complexity=0.7)

    print(f"   Generated {len(house_pattern)} drum hits")
    print("   First 10 hits:")
    for hit in house_pattern[:10]:
        print(f"     {hit.sound.name:12} | Beat: {hit.start:5.2f} | Vel: {hit.velocity:3d}")

    # Generate trap pattern
    print("\n3. TRAP PATTERN (140 BPM, no swing)")
    trap_gen = DrumGenerator(bpm=140, swing=0.0)
    trap_pattern = trap_gen.generate_trap(bars=2, complexity=0.8)

    print(f"   Generated {len(trap_pattern)} drum hits")
    print("   First 10 hits:")
    for hit in trap_pattern[:10]:
        print(f"     {hit.sound.name:12} | Beat: {hit.start:5.2f} | Vel: {hit.velocity:3d}")

    print("\n" + "=" * 70)
    print(f"TOTAL: {len(lofi_pattern) + len(house_pattern) + len(trap_pattern)} hits")
    print("=" * 70)
