# Sentinel Music Automation System - Project Plan

**Start Date:** 2026-02-23
**Goal:** Fully automated music production system using Ableton Live + Sentinel
**Timeline:** 4-5 weeks

## Executive Summary

Build a system where Sentinel can compose, produce, mix, and export complete music tracks automatically using Ableton Live, controlled via AbletonOSC and Max for Live.

## Architecture

```
SENTINEL (Python - Orchestrator)
    ↓
AbletonOSC (OSC Bridge)
    ↓
Max for Live Devices (Inside Ableton)
    ↓
ABLETON LIVE (DAW)
    ↓
Final Audio Export (WAV/MP3)
```

## Project Phases

### Phase 1: Infrastructure Setup (Week 1)
**Goal:** Get AbletonOSC working with basic Ableton control

**Tasks:**
1. Install AbletonOSC
   - Clone repository
   - Install Max for Live device in Ableton
   - Configure OSC port (11000)
   - Test connection

2. Create Python wrapper library
   - Connection manager
   - Track creation
   - Clip management
   - Basic parameter control

3. Test basic operations
   - Create MIDI track
   - Load instrument
   - Add notes to clip
   - Play/stop

**Deliverable:** Working Python → Ableton connection with basic control

---

### Phase 2: Music Generation (Week 2)
**Goal:** Build algorithms to generate musical content

**Components:**

#### 1. Melody Generator
```python
# melody_generator.py
generate_melody(
    key="C",
    scale="major",
    length_bars=8,
    mood="happy",
    complexity=0.7
) → List[Note]
```

**Features:**
- Scale-based note selection
- Rhythm patterns (quarter, eighth, sixteenth notes)
- Melodic contour (ascending, descending, wave)
- Motif repetition
- Variation generation

#### 2. Chord Progression Generator
```python
# chord_generator.py
generate_chords(
    key="C",
    progression_type="pop",  # pop, jazz, classical
    bars=8
) → List[Chord]
```

**Progressions:**
- Pop: I-V-vi-IV, I-IV-V, vi-IV-I-V
- Jazz: ii-V-I, iii-vi-ii-V-I
- Lo-fi: ii-V-I, vi-IV-V-I
- Custom: User-defined

#### 3. Drum Pattern Generator
```python
# drum_generator.py
generate_drums(
    genre="lofi",  # lofi, house, techno, trap
    bpm=90,
    swing=0.6,
    complexity=0.5
) → DrumPattern
```

**Elements:**
- Kick pattern
- Snare/clap
- Hi-hats (closed, open)
- Percussion (shakers, tambourine)
- Genre-specific variations

#### 4. Bass Line Generator
```python
# bass_generator.py
generate_bass(
    chord_progression=chords,
    style="walking",  # walking, root, octave, melodic
    complexity=0.6
) → List[Note]
```

#### 5. Reference Track Analyzer
```python
# reference_analyzer.py
analyze_track(audio_file) → TrackAnalysis

TrackAnalysis:
- bpm: int
- key: str
- scale: str (major/minor)
- chord_progression: List[Chord]
- structure: Dict (intro, verse, chorus, bridge, outro)
- instrumentation: List[str]
- mood: str
- genre: str
```

**Tools:**
- librosa (audio analysis)
- music21 (music theory)
- essentia (feature extraction)

**Deliverable:** Musical generators producing MIDI data

---

### Phase 3: Ableton Integration (Week 3)
**Goal:** Control Ableton to build full projects

**Components:**

#### 1. Track Builder
```python
# track_builder.py
class AbletonTrackBuilder:
    def create_midi_track(name, color)
    def load_instrument(track_id, instrument_name)
    def load_sample(track_id, sample_path)
    def create_clip(track_id, bar_start, bar_length)
    def add_notes(track_id, clip_id, notes)
```

#### 2. Instrument Manager
```python
# instrument_manager.py
load_instrument(track, instrument_type, preset=None)

Supported:
- Wavetable (Ableton synth)
- Sampler (sample playback)
- Simpler (one-shot sampler)
- Drum Rack (drums)
- External VSTs (if available)
```

#### 3. Effects Chain Builder
```python
# effects_manager.py
add_effect(track, effect_type, parameters)

Effects:
- EQ (frequency shaping)
- Compressor (dynamics)
- Reverb (space)
- Delay (echo)
- Filter (tone shaping)
- Saturator (warmth)
- Auto Filter (movement)
```

#### 4. Mixing Automation
```python
# mixer.py
class AutoMixer:
    def set_volume(track_id, db_level)
    def set_pan(track_id, pan_value)
    def create_send(from_track, to_track, amount)
    def setup_sidechain(source_track, target_track)
    def create_automation(track, parameter, curve)
```

**Deliverable:** Full project creation capability

---

### Phase 4: Sentinel Skills (Week 4)
**Goal:** Create Sentinel skills for music production

#### Skill 1: `daily-music-composer`
```yaml
name: daily-music-composer
description: Compose and produce a complete track daily
parameters:
  genre: string (lofi, house, techno, ambient)
  mood: string (happy, sad, energetic, chill)
  reference_track: string (path or URL)
  bpm: number (optional)
  key: string (optional)
```

**Workflow:**
1. Analyze reference track (if provided)
2. Generate melody, chords, drums, bass
3. Create Ableton project
4. Load instruments and samples
5. Add MIDI to clips
6. Apply mixing (levels, panning, effects)
7. Export audio
8. Notify via Slack

#### Skill 2: `sample-library-manager`
```yaml
name: sample-library-manager
description: Organize and search sample library
parameters:
  action: string (search, organize, tag)
  query: string (genre, mood, instrument)
```

**Features:**
- Index sample library
- Tag samples by genre/mood/type
- Search by characteristics
- Suggest samples for compositions

#### Skill 3: `reference-track-analyzer`
```yaml
name: reference-track-analyzer
description: Analyze audio track for musical features
parameters:
  audio_file: string (path or URL)
  analyze_chords: boolean
  analyze_structure: boolean
```

#### Skill 4: `ableton-project-builder`
```yaml
name: ableton-project-builder
description: Build Ableton project from musical data
parameters:
  composition: object (melody, chords, drums, bass)
  template: string (optional starting template)
  mix: boolean (auto-mix the track)
  export: boolean (export audio)
```

**Deliverable:** Working Sentinel skills for music production

---

### Phase 5: Polish & Automation (Week 5)
**Goal:** Production-ready system with scheduling

**Features:**

#### 1. Daily Automation
```bash
# Cron job (7 AM daily)
0 7 * * * /path/to/sentinel/run_daily_music.sh
```

**Script workflow:**
1. Wake up computer (if sleeping)
2. Open Ableton (if not running)
3. Generate music
4. Build project
5. Export audio
6. Upload to cloud/SoundCloud
7. Notify user

#### 2. Error Handling
- Ableton connection lost → retry
- OSC message failed → log and continue
- Sample not found → use alternative
- Export failed → retry with different settings

#### 3. Quality Control
- Check MIDI for empty clips
- Validate audio export
- Ensure no clipping (check levels)
- Verify file sizes

#### 4. File Management
```
~/Music/Sentinel/
├── projects/
│   ├── 2026-02-23_LoFi_Morning/
│   │   ├── project.als
│   │   ├── midi/
│   │   ├── samples/
│   │   └── exports/
│   └── 2026-02-24_House_Track/
├── templates/
│   ├── lofi_template.als
│   ├── house_template.als
│   └── techno_template.als
└── library/
    ├── drums/
    ├── bass/
    ├── synths/
    └── fx/
```

**Deliverable:** Fully automated daily music production

---

## Technical Stack

### Core Libraries
```python
# requirements.txt additions
python-osc>=1.8.1          # OSC communication
mido>=1.3.0                # MIDI file handling
music21>=9.1.0             # Music theory
librosa>=0.10.0            # Audio analysis
pretty_midi>=0.2.10        # MIDI manipulation
numpy>=1.24.0              # Numerical operations
scipy>=1.11.0              # Scientific computing
```

### Music AI (Optional)
```python
# Advanced music generation
magenta>=2.1.0             # Google's music AI
transformers>=4.35.0       # Hugging Face models
```

## File Structure

```
sentinel/
├── src/
│   ├── music/                      # NEW: Music system
│   │   ├── __init__.py
│   │   ├── generators/
│   │   │   ├── melody_generator.py
│   │   │   ├── chord_generator.py
│   │   │   ├── drum_generator.py
│   │   │   └── bass_generator.py
│   │   ├── ableton/
│   │   │   ├── osc_client.py       # AbletonOSC wrapper
│   │   │   ├── track_builder.py
│   │   │   ├── instrument_manager.py
│   │   │   ├── effects_manager.py
│   │   │   └── mixer.py
│   │   ├── analysis/
│   │   │   ├── reference_analyzer.py
│   │   │   ├── audio_features.py
│   │   │   └── chord_detection.py
│   │   └── composition/
│   │       ├── composer.py         # Main orchestrator
│   │       ├── arranger.py
│   │       └── mixer_ai.py
│   ├── skills/                     # Existing
│   ├── memory/                     # Existing
│   ├── adapters/                   # Existing
│   └── heartbeat/                  # Existing
│
├── .claude/skills/
│   ├── daily-music-composer/
│   │   ├── SKILL.md
│   │   └── composer.py
│   ├── sample-library-manager/
│   │   ├── SKILL.md
│   │   └── manager.py
│   └── reference-track-analyzer/
│       ├── SKILL.md
│       └── analyzer.py
│
├── music/                          # NEW: Music output
│   ├── projects/
│   ├── templates/
│   ├── library/
│   └── exports/
│
├── tests/
│   └── test_music_system.py
│
└── scripts/
    └── run_daily_music.sh
```

## Success Criteria

### Phase 1 Success
- ✅ Connect to Ableton via OSC
- ✅ Create MIDI track programmatically
- ✅ Add notes to clip
- ✅ Hear sound from Ableton

### Phase 2 Success
- ✅ Generate 16-bar melody in any key
- ✅ Generate chord progression
- ✅ Generate drum pattern
- ✅ Generate bass line
- ✅ All MIDI exports correctly

### Phase 3 Success
- ✅ Create full Ableton project (4+ tracks)
- ✅ Load instruments automatically
- ✅ Add effects chain
- ✅ Mix tracks (levels, pan)
- ✅ Export audio

### Phase 4 Success
- ✅ Sentinel skill executes full workflow
- ✅ Generate track from text prompt
- ✅ Analyze reference track
- ✅ Slack notification on completion

### Phase 5 Success
- ✅ Daily automated track generation
- ✅ Error handling and recovery
- ✅ Quality control checks
- ✅ File organization
- ✅ Wake up to new music!

## Example Usage

### Via Slack
```
You: "@Sentinel compose a lo-fi hip-hop track,
      reference: Nujabes - Feather,
      mood: rainy morning"

Sentinel: "✅ Starting composition...
           - Analyzing reference track
           - Generating musical ideas
           - Building Ableton project
           - Expected completion: 6:45 AM"

[6 hours later]

Sentinel: "🎵 Your track is ready!
           - Project: ~/Music/Sentinel/projects/2026-02-24_LoFi_Rainy/
           - Audio: ~/Music/Sentinel/exports/2026-02-24_LoFi_Rainy.wav
           - Listen: [Slack audio player]

           Track Info:
           - BPM: 90
           - Key: F# minor
           - Length: 3:24
           - Instruments: Rhodes, Bass, Drums, Vinyl

           Open in Ableton to tweak or export stems!"
```

### Via Python
```python
from src.skills.skill_manager import SkillManager

manager = SkillManager()

result = await manager.execute_skill('daily-music-composer', {
    'genre': 'lofi',
    'mood': 'chill',
    'bpm': 90,
    'key': 'Fm',
    'reference_track': '~/Music/reference.mp3'
})

print(result.output['project_path'])
print(result.output['audio_export'])
```

## Cost Estimate

### One-Time Costs
- Ableton Live Suite: $749 (already owned)
- Sample libraries: $0-500 (optional)
- Development time: ~80-120 hours

### Monthly Costs
- Claude API (music analysis): ~$10-20/month
- Cloud storage: ~$5/month
- Music AI APIs (optional): ~$10-30/month

**Total: ~$25-55/month**

## Timeline

| Week | Phase | Hours | Deliverable |
|------|-------|-------|-------------|
| 1 | Infrastructure | 20-30h | AbletonOSC working |
| 2 | Music Generation | 20-25h | Generators producing MIDI |
| 3 | Ableton Integration | 25-30h | Full project creation |
| 4 | Sentinel Skills | 15-20h | Skills working |
| 5 | Polish & Automation | 15-20h | Daily automation |

**Total: 95-125 hours (~3-4 weeks full-time)**

## Next Steps

### Immediate (Today)
1. Install AbletonOSC
2. Set up development environment
3. Test basic OSC connection
4. Create first Python → Ableton command

### This Week
1. Build OSC wrapper library
2. Create first melody generator
3. Test MIDI → Ableton workflow

### This Month
1. Complete all music generators
2. Build Ableton integration
3. Create Sentinel skills
4. Test end-to-end workflow

---

**Status:** 📋 Planning Complete - Ready to Build!

Built with Claude Code 🤖
