# Music Automation System - Setup Guide

## Prerequisites

✅ **You Have:**
- Ableton Live 12 Suite (includes Max for Live)
- Python 3.14
- Sentinel project

## Step-by-Step Setup

### Step 1: Install AbletonOSC

**1.1 Install Python OSC library:**
```bash
cd /Users/karlomarceloestrada/sentinel
source venv/bin/activate
pip install python-osc
```

**1.2 Download AbletonOSC:**
```bash
cd ~/Downloads
git clone https://github.com/ideoforms/AbletonOSC.git
```

**1.3 Install Max for Live device:**
```bash
# Copy the .amxd file to Ableton's User Library
cp ~/Downloads/AbletonOSC/abletonosc.amxd ~/Music/Ableton/User\ Library/Presets/MIDI\ Effects/Max\ MIDI\ Effect/
```

### Step 2: Configure Ableton

**2.1 Open Ableton Live 12 Suite**

**2.2 Create a test MIDI track:**
1. Create → Insert MIDI Track
2. Name it "OSC Test"

**2.3 Load AbletonOSC device:**
1. Open Browser (Cmd+Alt+B)
2. Navigate to: Max for Live → Max MIDI Effect
3. Drag `abletonosc.amxd` onto the MIDI track

**2.4 Configure OSC port:**
1. Click on the AbletonOSC device
2. Set port to: `11000` (default)
3. Set host to: `127.0.0.1` (localhost)
4. Click "Enable" or "Connect"

**2.5 Keep Ableton running** (minimized is fine)

### Step 3: Test Connection

**3.1 Run test script:**
```bash
cd /Users/karlomarceloestrada/sentinel
source venv/bin/activate
python scripts/test_ableton_connection.py
```

**Expected output:**
```
Connecting to Ableton via OSC...
✅ Connected to 127.0.0.1:11000
Sending test message...
✅ Message sent
Check Ableton for response
```

**3.2 Verify in Ableton:**
- You should see activity in the AbletonOSC device
- Or hear a note if test sends MIDI

### Step 4: Create Your First Track (Automated)

```bash
python scripts/create_first_track.py
```

This should:
1. Create 4 MIDI tracks in Ableton
2. Name them: Melody, Chords, Bass, Drums
3. Load instruments
4. Add a simple melody

---

## Troubleshooting

### Issue: "Connection refused" or OSC not responding

**Solution 1: Check Ableton is running**
```bash
ps aux | grep -i ableton
```
If not running, launch Ableton first.

**Solution 2: Check AbletonOSC device is loaded**
- Look for the Max for Live device on a track
- Make sure it shows "Connected" or "Enabled"

**Solution 3: Check firewall**
```bash
# Allow localhost connections (should be default)
# Check System Preferences → Security → Firewall
```

**Solution 4: Restart AbletonOSC device**
- In Ableton, delete the device
- Re-add it to the track
- Re-configure port to 11000

### Issue: Max for Live device not found

**Solution: Manually locate the file**
```bash
# Find all .amxd files
find ~/Downloads/AbletonOSC -name "*.amxd"

# Copy to Ableton User Library
cp [path-to-amxd-file] ~/Music/Ableton/User\ Library/Presets/MIDI\ Effects/Max\ MIDI\ Effect/
```

### Issue: Python OSC library not found

```bash
source venv/bin/activate
pip install python-osc --upgrade
```

---

## Next Steps

Once setup is complete:

1. ✅ **Test basic track creation** (create_first_track.py)
2. ✅ **Test instrument loading** (test_instruments.py)
3. ✅ **Test MIDI note addition** (test_midi_notes.py)
4. ✅ **Build music generators** (melody, chords, drums)
5. ✅ **Create Sentinel skills** (daily-music-composer)

---

## Useful Commands

**Check if Ableton is running:**
```bash
ps aux | grep -i "ableton"
```

**Kill Ableton (if needed):**
```bash
killall "Ableton Live 12 Suite"
```

**Test OSC connection:**
```bash
python -c "from pythonosc import udp_client; c = udp_client.SimpleUDPClient('127.0.0.1', 11000); c.send_message('/live/test', []); print('Sent')"
```

**Monitor OSC messages (debugging):**
```bash
# Install OSC monitor
pip install python-osc

# Run monitor
python -c "from pythonosc.dispatcher import Dispatcher; from pythonosc.osc_server import BlockingOSCUDPServer; d = Dispatcher(); d.set_default_handler(lambda addr, *args: print(f'{addr}: {args}')); s = BlockingOSCUDPServer(('127.0.0.1', 11001), d); s.serve_forever()"
```

---

## Resources

- **AbletonOSC GitHub:** https://github.com/ideoforms/AbletonOSC
- **python-osc docs:** https://python-osc.readthedocs.io/
- **Max for Live API:** https://docs.cycling74.com/max8/vignettes/live_api_overview
- **Ableton Live API:** Live Object Model (LOM) documentation

---

**Ready to start!** Run the setup commands and let me know if you encounter any issues.
