# Quick Start - Sentinel Music Automation

One-page guide to get music into Ableton in 60 seconds.

---

## Prerequisites (One-Time Setup)

1. **Ableton Live 12 Suite** installed
2. **AbletonOSC** enabled:
   - Open Ableton → Preferences (`Cmd+,`)
   - Link / Tempo / MIDI tab
   - Control Surface → Select "AbletonOSC"
   - Status bar shows: "Listening on port 11000"
3. **Sentinel environment** activated:
   ```bash
   cd ~/sentinel
   source venv/bin/activate
   ```

---

## Generate + Send Track to Ableton

### One Command

```bash
python scripts/send_track_to_ableton.py
```

**That's it!** You'll get:
- 4 MIDI tracks (Drums, Bass, Chords, Melody)
- 8 bars at 90 BPM in F# minor
- Lo-fi style with walking bass
- Basic mix applied

---

## Test Connection Only

```bash
python scripts/test_ableton_connection.py
```

Verifies Ableton is listening and responsive.

---

## Generate MIDI File (No Ableton)

```bash
python scripts/generate_complete_track.py
```

**Output**: `music/demos/05_complete_track.mid`

Import manually into any DAW.

---

## Python API Examples

### Quick Track to Ableton

```python
from music.ableton_controller import AbletonController
from music.generators.drum_generator import DrumGenerator

# Connect
ableton = AbletonController()
ableton.connect()

# Generate drums
drum_gen = DrumGenerator(bpm=90, swing=0.3)
drums = drum_gen.generate_lofi(bars=8)

# Create track
track_id = 0
ableton.create_midi_track(track_id)
ableton.set_track_name(track_id, "Drums")

# Create clip
ableton.create_clip(track_id, 0, 8.0)

# Add notes
for hit in drums:
    ableton.add_note(track_id, 0, hit.sound.value, hit.start, 0.1, hit.velocity)

# Play
ableton.set_tempo(90.0)
ableton.fire_clip(track_id, 0)
ableton.play()
```

### Custom Configuration

```python
from music.generators import *

# Configuration
KEY = 60  # C major
BPM = 120
BARS = 16

# Generate
chord_gen = ChordGenerator(key_root=KEY, scale=Scale.MAJOR)
melody_gen = MelodyGenerator(key_root=KEY, scale=Scale.MAJOR_PENTATONIC)

chords = chord_gen.generate_progression("pop_1", bars=BARS)
melody = melody_gen.generate_motif_based(bars=BARS, creativity=0.8)

# ... send to Ableton
```

---

## Available Styles

### Chord Progressions

```python
"pop_1"    # I-V-vi-IV (Let It Be)
"pop_2"    # vi-IV-I-V (Don't Stop Believin')
"lofi_1"   # ii-V-I (jazz-influenced)
"jazz_1"   # ii-V-I (classic turnaround)
"sad_1"    # vi-IV-I-V (melancholic)
```

### Bass Styles

```python
bass_gen.generate_simple(chords)         # Root notes only
bass_gen.generate_walking(chords)        # Jazz walking bass
bass_gen.generate_synth_bass(chords)     # Electronic patterns
bass_gen.generate_funk(chords)           # Syncopated funk
```

### Drum Genres

```python
drum_gen.generate_lofi(bars=8)     # Laid-back, swung
drum_gen.generate_house(bars=8)    # Four-on-the-floor
drum_gen.generate_trap(bars=8)     # Heavy, syncopated
```

---

## Common Operations

### Change Key and Tempo

```python
# F# minor, 90 BPM
KEY = 66
BPM = 90
SCALE = Scale.MINOR_PENTATONIC
```

### Change Style

```python
# House music at 128 BPM
chord_gen = ChordGenerator(key_root=60, scale=Scale.MINOR)
chords = chord_gen.generate_progression("pop_1", bars=8)

bass_gen = BassGenerator(key_root=60, scale=Scale.MINOR)
bass = bass_gen.generate_synth_bass(chords, pattern="16ths")

drum_gen = DrumGenerator(bpm=128, swing=0.0)
drums = drum_gen.generate_house(bars=8, complexity=0.8)
```

### Adjust Mix in Ableton

```python
ableton.set_track_volume(0, -6.0)    # -6 dB
ableton.set_track_pan(0, -0.5)       # Left
ableton.mute_track(1, True)          # Mute bass
ableton.solo_track(0, True)          # Solo drums
```

---

## Troubleshooting

### "Connection failed"
1. Is Ableton running?
2. Is AbletonOSC enabled in Preferences?
3. Status bar shows "Listening on port 11000"?

### "Module not found"
```bash
source venv/bin/activate
pip install python-osc mido
```

### "No sound"
- Load instruments on tracks in Ableton
- Click track to select it
- Drag instrument from Browser

---

## File Locations

```
~/sentinel/
├── scripts/
│   ├── send_track_to_ableton.py       # Full integration
│   ├── test_ableton_connection.py     # Connection test
│   └── generate_complete_track.py     # MIDI file only
│
├── src/music/
│   ├── ableton_controller.py          # Python wrapper
│   └── generators/
│       ├── melody_generator.py
│       ├── chord_generator.py
│       ├── bass_generator.py
│       └── drum_generator.py
│
├── music/demos/                       # Generated MIDI files
│
└── docs/
    └── ABLETON_OSC_SETUP.md           # Full setup guide
```

---

## Learn More

- **Full Setup**: [docs/ABLETON_OSC_SETUP.md](docs/ABLETON_OSC_SETUP.md)
- **Phase 2 Summary**: [MUSIC_GENERATION_COMPLETE.md](MUSIC_GENERATION_COMPLETE.md)
- **Phase 3 Summary**: [ABLETON_INTEGRATION_COMPLETE.md](ABLETON_INTEGRATION_COMPLETE.md)
- **AbletonOSC API**: https://github.com/ideoforms/AbletonOSC

---

**Get started in 3 commands**:

```bash
cd ~/sentinel
source venv/bin/activate
python scripts/send_track_to_ableton.py
```

🎵 **Make music!**
