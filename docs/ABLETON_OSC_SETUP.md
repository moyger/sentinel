# AbletonOSC Setup Guide

Complete guide to setting up AbletonOSC for Sentinel music automation.

## ✅ Step 1: Install AbletonOSC (COMPLETE)

AbletonOSC has been installed to:
```
~/Music/Ableton/User Library/Remote Scripts/AbletonOSC/
```

## 📋 Step 2: Configure in Ableton Live

### Manual Steps (YOU MUST DO THIS):

1. **Open Ableton Live 12 Suite**

2. **Open Preferences**
   - Mac: `Live → Preferences` or `Cmd+,`
   - Windows: `Options → Preferences`

3. **Go to Link / Tempo / MIDI tab**

4. **Under "Control Surface" dropdown**:
   - Select **"AbletonOSC"**
   - Input: None
   - Output: None

5. **Check status bar**
   - You should see: **"AbletonOSC: Listening for OSC on port 11000"**
   - This confirms it's working!

### Troubleshooting

**If AbletonOSC doesn't appear in dropdown**:
- Restart Ableton Live
- Check installation path:
  ```bash
  ls ~/Music/Ableton/User\ Library/Remote\ Scripts/AbletonOSC/
  ```
- Should see: `__init__.py`, `abletonosc/`, etc.

**If you see errors**:
- Check logs at: `~/Music/Ableton/User Library/Remote Scripts/AbletonOSC/logs/`

## 🔌 Step 3: Test Connection

### Option A: Using Python (automated)

```bash
cd /Users/karlomarceloestrada/sentinel
source venv/bin/activate
python scripts/test_ableton_connection.py
```

**Expected output**:
```
Connecting to Ableton...
✅ Connection successful!
Ableton is listening on port 11000
```

### Option B: Manual Test

1. **Keep Ableton Live running** with AbletonOSC enabled

2. **Send test OSC message**:
   ```bash
   python -c "from pythonosc import udp_client; c = udp_client.SimpleUDPClient('127.0.0.1', 11000); c.send_message('/live/test', []); print('Sent test message')"
   ```

3. **Check Ableton's status bar**
   - Should briefly show: "AbletonOSC: received /live/test"

## 📡 OSC Communication Details

### Ports
- **Send to Ableton**: Port **11000** (from Python)
- **Receive from Ableton**: Port **11001** (to Python)
- **Protocol**: UDP
- **Host**: 127.0.0.1 (localhost)

### Message Format

**Create MIDI Track**:
```python
client.send_message('/live/song/create_midi_track', [-1])
# -1 = add at end
```

**Start Playback**:
```python
client.send_message('/live/song/start_playing', [])
```

**Set Tempo**:
```python
client.send_message('/live/song/set/tempo', [90.0])
```

## 🎯 Common Operations

### Track Creation

```python
# Create MIDI track
client.send_message('/live/song/create_midi_track', [-1])

# Create audio track
client.send_message('/live/song/create_audio_track', [-1])

# Create return track
client.send_message('/live/song/create_return_track', [])
```

### Track Control

```python
# Set track name
client.send_message('/live/track/set/name', [0, "Drums"])

# Set volume (in dB, range: -inf to 6.0)
client.send_message('/live/track/set/volume', [0, 0.0])

# Mute/Unmute
client.send_message('/live/track/set/mute', [0, 1])  # 1 = muted

# Arm for recording
client.send_message('/live/track/set/arm', [0, 1])  # 1 = armed
```

### Clip Operations

```python
# Create MIDI clip
client.send_message('/live/clip_slot/create_clip', [0, 0, 8.0])
# track 0, clip_slot 0, 8 bars long

# Add note to clip (pitch, start_time, duration, velocity, muted)
client.send_message('/live/clip/add_note', [0, 0, 60, 0.0, 1.0, 100, 0])
# track 0, clip 0, note C4, at beat 0, 1 beat long, velocity 100, not muted

# Play clip
client.send_message('/live/clip_slot/fire', [0, 0])
```

### Song Control

```python
# Start/Stop playback
client.send_message('/live/song/start_playing', [])
client.send_message('/live/song/stop_playing', [])

# Set tempo
client.send_message('/live/song/set/tempo', [120.0])

# Set time signature
client.send_message('/live/song/set/signature_numerator', [4])
client.send_message('/live/song/set/signature_denominator', [4])
```

## 📚 Full API Reference

Complete API documentation: [AbletonOSC GitHub](https://github.com/ideoforms/AbletonOSC#readme)

### Main APIs:
- **Song API**: Global playback, tempo, tracks, scenes
- **Track API**: Volume, panning, mute, solo, devices
- **Clip API**: MIDI notes, automation, loop settings
- **Device API**: Instrument/effect parameters
- **Scene API**: Scene launching and properties

## 🛠️ Python Wrapper (Sentinel)

Sentinel provides a high-level Python wrapper in [src/music/ableton_controller.py](../src/music/ableton_controller.py:1):

```python
from music.ableton_controller import AbletonController

# Connect to Ableton
ableton = AbletonController()
if ableton.connect():
    print("✓ Connected to Ableton!")

# Create a MIDI track
track_id = ableton.create_midi_track(-1)  # -1 = add at end
ableton.set_track_name(track_id, "Drums")

# Create a MIDI clip (track_id, clip_slot, length_bars)
clip_slot = 0  # First scene
ableton.create_clip(track_id, clip_slot, 8.0)

# Add notes from generators
from music.generators.drum_generator import DrumGenerator
drum_gen = DrumGenerator(bpm=90, swing=0.3)
drums = drum_gen.generate_lofi(bars=8)

for hit in drums:
    ableton.add_note(
        track_id=track_id,
        clip_slot=clip_slot,
        pitch=hit.sound.value,
        start_time=hit.start,
        duration=0.1,
        velocity=hit.velocity
    )

# Set tempo and play
ableton.set_tempo(90.0)
ableton.fire_clip(track_id, clip_slot)  # Fire the clip
ableton.play()  # Start transport
```

### Available Methods

**Song Control**:
- `play()` - Start playback
- `stop()` - Stop playback
- `set_tempo(bpm)` - Set tempo
- `set_time_signature(numerator, denominator)` - Set time signature

**Track Operations**:
- `create_midi_track(index=-1)` - Create MIDI track
- `create_audio_track(index=-1)` - Create audio track
- `set_track_name(track_id, name)` - Set track name
- `set_track_volume(track_id, volume_db)` - Set volume (-inf to 6.0)
- `set_track_pan(track_id, pan)` - Set pan (-1.0 to 1.0)
- `mute_track(track_id, muted=True)` - Mute/unmute
- `solo_track(track_id, solo=True)` - Solo/unsolo
- `arm_track(track_id, armed=True)` - Arm for recording

**Clip Operations**:
- `create_clip(track_id, clip_slot, length_bars)` - Create MIDI clip
- `fire_clip(track_id, clip_slot)` - Play clip
- `stop_clip(track_id, clip_slot)` - Stop clip
- `add_note(track_id, clip_slot, pitch, start_time, duration, velocity)` - Add note
- `add_notes_batch(track_id, clip_slot, notes)` - Add multiple notes
- `clear_clip(track_id, clip_slot)` - Clear all notes
- `set_clip_name(track_id, clip_slot, name)` - Set clip name

**Scene Operations**:
- `fire_scene(scene_index)` - Fire scene
- `create_scene(index=-1)` - Create scene

## ⚠️ Important Notes

### Ableton Must Be Running
- AbletonOSC only works when **Ableton Live is running**
- The application can be minimized but not closed
- If Ableton crashes, restart and re-enable AbletonOSC

### Limitations
- **No remote start**: Cannot launch Ableton programmatically (macOS limitation)
- **One instance**: Only one Ableton instance can use OSC at a time
- **Local only**: OSC communication is localhost only (for security)

### Performance
- **Low latency**: OSC messages are nearly instant (<10ms)
- **Concurrent**: Multiple messages can be sent rapidly
- **Reliable**: UDP is fast but doesn't guarantee delivery (rarely an issue on localhost)

## 🔍 Debugging

### Enable Debug Logging

```python
client.send_message('/live/api/set/log_level', ['debug'])
```

**Check logs at**:
```
~/Music/Ableton/User Library/Remote Scripts/AbletonOSC/logs/abletonosc.log
```

### Common Issues

**"Connection refused"**:
- Ableton is not running
- AbletonOSC not enabled in preferences
- Firewall blocking port 11000

**"No response from Ableton"**:
- Check AbletonOSC status bar message
- Verify port 11000 is not in use: `lsof -i :11000`
- Restart Ableton

**"Invalid parameters"**:
- Check OSC message format
- Consult API docs for correct parameter types
- Enable debug logging

## ✅ Verification Checklist

Before proceeding to automation:

- [ ] Ableton Live 12 Suite installed
- [ ] AbletonOSC copied to Remote Scripts folder
- [ ] Ableton restarted
- [ ] AbletonOSC selected in Preferences
- [ ] Status bar shows "Listening on port 11000"
- [ ] Test message sent successfully
- [ ] Python wrapper can connect

---

## Next Steps

Once setup is complete:

1. ✅ **Test connection** (scripts/test_ableton_connection.py)
2. ✅ **Create tracks** programmatically
3. ✅ **Load instruments** and effects
4. ✅ **Add MIDI clips** with generated music
5. ✅ **Mix and export** final audio

---

**Setup completed**: February 24, 2026
**Sentinel Music Automation** - Phase 3: Ableton Integration
