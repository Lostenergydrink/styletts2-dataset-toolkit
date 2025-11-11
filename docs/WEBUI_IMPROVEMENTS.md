# WebUI Improvements for Dataset Preparation

## Problem
StyleTTS2 pretrained model has hard constraints:
- **178 token vocabulary** (no digits, limited punctuation)
- **512 BERT token limit** (~450 characters max)

Previous WebUI settings encouraged creating datasets that would fail training:
- Audio segments up to 90 seconds → transcripts 600+ characters → training crash
- No validation or normalization → digits/symbols in transcripts → vocabulary mismatch
- Manual post-processing required → error-prone, not scalable

## Solution

### 1. Fixed Step 2: Segment Audio

**Before:**
```python
segment_duration_slider = gr.Slider(
    minimum=30,
    maximum=90,
    value=60,  # 1 minute default
    step=10,
    label="Target Chunk Duration (seconds)"
)
```

**After:**
```python
segment_duration_slider = gr.Slider(
    minimum=3,
    maximum=30,  # Hard limit at 30 seconds
    value=10,    # Safe default
    step=1,
    label="Target Chunk Duration (seconds)",
    info="⚠️ Longer segments may exceed 450 char transcript limit"
)
```

**Why:**
- Average speech rate: ~15 chars/second
- 450 char limit ÷ 15 = ~30 seconds maximum
- 10 second default keeps transcripts ~150 chars (safe)
- Added explicit warnings in UI markdown

### 2. Added Auto-Normalization to Step 4: Export Dataset

**New Function:**
```python
def normalize_transcript(text, max_chars=450):
    """
    Normalize transcript for StyleTTS2 compatibility:
    - Convert digits to words (using num2words if available)
    - Remove unsupported characters (only keep: A-Z, a-z, !'(),:;? and space)
    - Truncate to max_chars at sentence boundary
    
    Returns: (normalized_text, warnings_list)
    """
```

**Integration:**
Export process now automatically:
1. Calls `normalize_transcript()` on every transcript
2. Logs all changes and warnings
3. Shows summary in UI with normalization stats
4. No manual intervention required

**Example Output:**
```
✅ Dataset exported successfully!

Dataset: jinwoo-sung-v2
Files: 42 audio + transcript pairs
Location: E:\AI\tts-webui\styletts2\datasets\jinwoo-sung-v2
Filelist: train_list.txt

🔧 Normalization applied to 8 transcripts:
   - Converted digits to words
   - Removed unsupported characters
   - Truncated overly long text
   - Total warnings: 15

📊 Total Duration: 0h 6m 22s (6.4 minutes)

📝 Format: filename.wav|transcription|speaker
🎓 Ready for fine-tuning!
```

### 3. Dependencies

**Added:**
```python
try:
    from num2words import num2words
    NUM2WORDS_AVAILABLE = True
except ImportError:
    NUM2WORDS_AVAILABLE = False
    print("⚠️ num2words not installed. Text normalization will be limited.")
```

**Installation:**
```powershell
**Installation:**
```bash
pip install num2words
```

### 4. Automatic Port Fallback

**Before:**
```python
app.launch(
    server_name=args.server_name,
    server_port=args.server_port,  # Fails if busy
    share=args.share,
    inbrowser=args.inbrowser,
)
```

**After:**
```python
# Try to launch with automatic port fallback
max_retries = 5
current_port = args.server_port

for attempt in range(max_retries):
    try:
        app.launch(
            server_name=args.server_name,
            server_port=current_port,
            share=args.share,
            inbrowser=args.inbrowser,
            show_api=False,
        )
        break  # Success!
    except OSError as e:
        if "Cannot find empty port" in str(e) and attempt < max_retries - 1:
            current_port += 1
            print(f"⚠️ Port {current_port - 1} is busy, trying port {current_port}...")
        else:
            print(f"\n❌ Error: Could not find an available port.")
            print(f"   Tried ports {args.server_port} to {current_port}")
            print(f"\n💡 Solutions:")
            print(f"   1. Close other applications using these ports")
            print(f"   2. Specify a different port: python styletts2_webui.py --server_port 7865")
            print(f"   3. Check running processes: netstat -ano | findstr :{args.server_port}")
            raise
```

**Why:**
- Default Gradio port (7860) often busy with other applications
- Automatic fallback tries ports 7861, 7862, 7863, 7864, 7865
- Clear error messages if all ports busy
- No manual intervention needed in most cases

**Utility Script Added:**
`check_port.ps1` - PowerShell utility to manage port conflicts:
```powershell
# Check if port is free
.\check_port.ps1 -Port 7860

# Kill process using port
.\check_port.ps1 -Port 7860 -Kill

# List port range status
.\check_port.ps1 -Port 7860 -List
```

---

## Testing

### Test Case 1: Digit Conversion
```

If not installed, fallback behavior:
- Digits are removed instead of converted
- Warning shown in export summary

## Benefits

### For Users:
- ✅ **No manual post-processing** - normalization happens automatically
- ✅ **Safer defaults** - can't accidentally create overly long segments
- ✅ **Clear feedback** - see exactly what was normalized and why
- ✅ **Works out of the box** - sensible defaults for 95% of use cases

### For Training:
- ✅ **No vocabulary mismatches** - digits always converted to words
- ✅ **No BERT length errors** - transcripts truncated at sentence boundaries
- ✅ **Fewer failed training runs** - issues caught before training starts
- ✅ **Better quality data** - consistent character set, proper lengths

### Backwards Compatible:
- ✅ Existing workflows still work
- ✅ Manual normalization scripts still available as fallback
- ✅ Validation script still useful for double-checking
- ✅ Old datasets can be re-exported through WebUI to get normalization

## Testing Checklist

Before your next dataset:
1. [ ] Launch WebUI: `python styletts2_webui.py`
2. [ ] Verify slider shows 3-30 range (not 30-90)
3. [ ] Import audio, segment at 10 seconds
4. [ ] Transcribe with Whisper
5. [ ] Export dataset - check for normalization summary
6. [ ] Verify `train_list.txt` has clean transcripts (no digits)
7. [ ] Run validation script as sanity check (optional)
8. [ ] Start training - should work without errors

## Future Enhancements

Potential improvements for later:
- [ ] Auto train/val split in export step
- [ ] Show real-time char count during transcription
- [ ] Preview normalized transcripts before export
- [ ] Batch validation UI in "5️⃣ View Datasets" tab
- [ ] Configurable normalization rules (advanced users)
- [ ] Integration with `validate_dataset.py` in export step

## Migration Guide

### If you have old datasets with issues:

**Option 1: Re-export through WebUI (recommended)**
1. Keep your processed audio in `training-data/processed/SpeakerName/`
2. Keep your transcripts in `training-data/transcripts/SpeakerName/`
3. Go to "4️⃣ Export Dataset" and re-export
4. WebUI will auto-normalize during export

**Option 2: Use standalone normalization script**
```powershell
cd E:\AI\tts-webui\styletts2
.\.venv\Scripts\python normalize_dataset.py datasets\old-dataset\train_list.txt --preview
.\.venv\Scripts\python normalize_dataset.py datasets\old-dataset\train_list.txt --apply
```

### If you manually edit transcripts:

After editing, either:
1. Re-export through WebUI (will auto-normalize)
2. Run `normalize_dataset.py` on the manifest file
3. Ensure you only use allowed characters: `A-Za-z!'(),:;? `

## Documentation Updates

- [x] `DATASET_REQUIREMENTS.md` - Updated workflow to reflect auto-normalization
- [x] `WEBUI_IMPROVEMENTS.md` - This file
- [ ] `README.md` - Add note about num2words dependency
- [ ] WebUI inline help - Add tooltips for new features
