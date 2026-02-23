# Sentinel Music Generator - Demo MIDI Files

## 🎵 What's This?

These are AI-generated melodies demonstrating different **creativity levels** in Sentinel's music generation system.

All melodies are in **F# minor pentatonic** (lo-fi/Nujabes territory) at **90 BPM**.

---

## 📁 Files

### 1. `01_basic_melody.mid` - Creativity: 3/10
**The "Elevator Music" Level**

- Strict scale adherence
- Simple quarter note rhythm (no variation)
- Predictable ascending/descending pattern
- Constant velocity (no dynamics)

**Sounds like:** Background music, muzak, basic loops

**Good for:** Placeholder music, testing, understanding basics

---

### 2. `02_varied_melody.mid` - Creativity: 6/10
**The "Competent Composer" Level**

- Mixed rhythms (quarters, eighths, halves, sixteenths)
- Melodic leaps and steps (more interesting)
- Dynamic velocity (60-110 range)
- More natural phrasing

**Sounds like:** "In the style of [artist]" - decent pastiches

**Good for:** Background beats, study music, YouTube tracks

---

### 3. `03_motif_based.mid` - Creativity: 7/10
**The "Thoughtful Composition" Level**

- Creates a 1-bar motif
- Develops it through 8 bars with variations:
  - Transposition (pitch shifts)
  - Rhythmic variations
  - Melodic inversion
  - Repetition with changes
- More coherent structure (like real music!)

**Sounds like:** Intentional composition with themes and development

**Good for:** Actual tracks, original music, creative projects

---

### 4. `04_humanized.mid` - Creativity: 7/10 + Human Touch
**The "Live Musician" Level**

Takes the motif-based melody and adds:
- Timing variations (±0.02 beats - natural swing)
- Velocity variations (±8 velocity - human dynamics)
- Slight duration changes (organic feel)

**Sounds like:** Someone actually playing it, not a robot

**Good for:** Final tracks, anything you want to sound "alive"

---

## 🎧 How to Listen

### Option 1: Ableton Live (Recommended)

1. Open Ableton Live 12 Suite
2. Drag MIDI files onto empty MIDI tracks
3. Load an instrument on each track:
   - **Wavetable** - Modern synth (good for comparison)
   - **Sampler** - Load a piano/rhodes sample
   - **Simpler** - Quick sample playback
4. Press **Spacebar** to play
5. Compare the melodies!

### Option 2: Any DAW

These are standard MIDI files - work in:
- Logic Pro
- FL Studio
- GarageBand
- Reaper
- etc.

### Option 3: Online MIDI Player

Upload to https://signal.vercel.app/midi or similar MIDI players.

---

## 🔍 What to Listen For

### Comparing 01 (Basic) vs 02 (Varied):
- **Rhythm diversity**: Varied has more interesting rhythms
- **Melodic movement**: Varied has leaps, not just steps
- **Dynamics**: Varied has loud/soft variations

### Comparing 02 (Varied) vs 03 (Motif):
- **Structure**: Motif has a theme that develops
- **Coherence**: Motif feels more "composed"
- **Repetition**: Motif uses repetition with variation (real music technique)

### Comparing 03 (Motif) vs 04 (Humanized):
- **Groove**: Humanized swings more naturally
- **Feel**: Humanized feels less "robotic"
- **Timing**: Humanized has subtle timing variations (like a real player)

---

## 🎹 Experiment Ideas

### 1. Same Instrument, All 4 Melodies
Load all 4 MIDI files on separate tracks with the SAME instrument.

**Listen for:** How creativity level affects perceived quality.

### 2. Different Instruments
Try each melody with:
- Piano/Rhodes (organic)
- Synth (electronic)
- Pluck/Harp (percussive)

**Listen for:** How timbre affects perception of creativity.

### 3. Layer Them
Play all 4 at once!

**Result:** Creates a complex polyrhythmic texture.

### 4. Process Them
Add effects:
- Reverb (space)
- Delay (echo/movement)
- Low-pass filter (lo-fi vibe)
- Vinyl crackle (texture)

**Listen for:** How processing enhances the melodies.

---

## 💡 Technical Details

### Generation Parameters

**01_basic_melody.mid:**
```python
generator.generate_basic(bars=8)
# No creativity parameters
```

**02_varied_melody.mid:**
```python
generator.generate_varied(bars=8, creativity=0.6)
# 60% creativity (moderate variation)
```

**03_motif_based.mid:**
```python
generator.generate_motif_based(bars=8, creativity=0.7)
# 70% creativity + motif development
```

**04_humanized.mid:**
```python
motif = generator.generate_motif_based(bars=8, creativity=0.7)
humanized = generator.humanize(motif, amount=0.4)
# 40% humanization (timing + velocity variations)
```

### MIDI Spec
- **Key:** F# minor (MIDI root: 66)
- **Scale:** Minor pentatonic [0, 3, 5, 7, 10]
- **BPM:** 90
- **Time Signature:** 4/4
- **Bars:** 8
- **Notes per file:** ~32 notes

---

## 🚀 Next Steps

This is just the **melody layer**. A full track needs:

1. **Chords** - Harmonic foundation (coming soon)
2. **Bass** - Low-end groove (coming soon)
3. **Drums** - Rhythm section (coming soon)
4. **FX** - Ear candy, transitions (coming soon)

Once all generators are built, Sentinel will create **complete tracks** automatically:
- Melody (done ✅)
- Chords
- Bass
- Drums
- Arrangement
- Mixing
- Export

**Result:** Wake up to AI-generated music daily! 🎵

---

## 🤔 Questions?

### "Why does basic sound so boring?"
That's the point! It shows the difference between "correct" and "creative".

### "Can I use these in my tracks?"
Yes! These are generated for you. Use however you want.

### "How is this different from loops?"
These are **generated fresh** each time, not pre-made loops. Every generation is unique.

### "Can Sentinel generate in other keys/scales?"
Yes! These demos use F# minor pentatonic, but the generator supports:
- All keys (C, C#, D, etc.)
- Multiple scales (major, minor, dorian, blues, etc.)
- Custom scales

### "What about copyright?"
AI-generated melodies are not copyrightable (currently). But once YOU add your creative touch (arrangement, production, mixing), the final track is yours.

---

**Generated by Sentinel Music System** 🤖
**Date:** February 23, 2026
**Version:** Demo v0.1

Enjoy! 🎵
