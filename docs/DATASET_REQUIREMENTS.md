# StyleTTS2 Dataset Requirements & Workflow

## Critical Constraints

### 1. Vocabulary (178 tokens - IMMUTABLE)
The pretrained LibriTTS model uses a **fixed 178-token vocabulary**. You cannot expand it without retraining from scratch.

**Allowed characters:**
- Letters: `A-Z`, `a-z`
- Punctuation: `!`, `'`, `(`, `)`, `,`, `.`, `:`, `;`, `?`, ` ` (space)

**NOT allowed:**
- ❌ Digits: `0-9`
- ❌ Symbols: `%`, `-`, `&`, `#`, `@`, etc.
- ❌ Special characters: em-dashes, curly quotes, etc.

### 2. BERT Token Limit (512 tokens)
PLBERT text encoder has a **hard limit of 512 tokens** (~450 characters is safe).

**Length guidelines:**
- ✅ Safe: < 450 characters
- ⚠️ Risky: 450-500 characters (may exceed token limit)
- ❌ Fail: > 500 characters (will crash training)

### 3. Audio Requirements
- Format: WAV
- Sample rate: 24000 Hz
- Duration: 3-15 seconds recommended
- Quality: Clean voice, minimal background noise

---

## Workflow for Creating Datasets

### Step 1: Prepare Audio in Gradio WebUI
1. Launch Gradio: `python styletts2_webui.py`
2. Go to "🎓 Dataset Prep & Training" tab
3. Upload audio files to "1️⃣ Import Audio"

### Step 2: Segment Audio ⚠️ **UPDATED WITH SAFE LIMITS**
1. Go to "2️⃣ Segment Audio"
2. **New safe range:** 3-30 seconds (was 30-90)
3. **Recommended:** 10 seconds (default)
4. Why? Longer audio = longer transcripts = exceeds 450 char limit

The slider now prevents you from creating overly long segments that would fail training.

### Step 3: Transcribe with Whisper
1. Go to "3️⃣ Transcribe"
2. Select Whisper model (base recommended)
3. Run transcription

Whisper will produce transcripts with digits/symbols. **This is expected and will be fixed automatically in the next step.**

### Step 4: Export Dataset ✨ **NOW WITH AUTO-NORMALIZATION**
1. Go to "4️⃣ Export Dataset"
2. Enter dataset name
3. Click export

**The export process now automatically:**
- ✅ Converts digits → words ("25%" → "twenty five percent")
- ✅ Removes unsupported characters
- ✅ Truncates overly long transcripts at sentence boundaries
- ✅ Validates against 178-token vocabulary
- ✅ Shows warnings for any issues

**You no longer need to manually run normalization scripts!**

### Step 5: (Optional) Manual Validation
If you want to double-check the exported dataset:

```powershell
cd E:\AI\tts-webui\styletts2
.\.venv\Scripts\python validate_dataset.py datasets\your-dataset\train_list.txt
```

This is **optional** since the export step already normalizes everything. Use this only if:
- You manually edited transcripts after export
- You want to verify everything is perfect before a long training run

### Step 6: Split Train/Val Sets
Use 80-90% for training, 10-20% for validation:

```powershell
# Example: 35 train, 7 val from 42 samples
Get-Content datasets\your-dataset\all_samples.txt | Select-Object -First 35 > train_list.txt
Get-Content datasets\your-dataset\all_samples.txt | Select-Object -Last 7 > val_list.txt
```

### Step 7: Update Config
Edit your `config_ft.yml`:

```yaml
data_params:
  train_data: "datasets/your-dataset/train_list.txt"
  val_data: "datasets/your-dataset/val_list.txt"
  root_path: "datasets/your-dataset"
```

### Step 8: Start Training
```powershell
.\.venv\Scripts\python StyleTTS2\train_finetune.py --config_path path\to\config_ft.yml
```

---

## Changes from Previous Workflow

### ✅ What's Fixed in the WebUI:

1. **Step 2 (Segment Audio):**
   - Slider range changed: 30-90 seconds → **3-30 seconds**
   - Default changed: 60 seconds → **10 seconds**
   - Added warnings about transcript length limits
   - Prevents creating segments that will exceed BERT token limit

2. **Step 4 (Export Dataset):**
   - **Auto-normalization now built-in!**
   - Converts digits to words automatically
   - Removes unsupported characters automatically
   - Truncates long transcripts at sentence boundaries
   - Shows detailed warnings for any issues
   - No manual script running needed

### ⚠️ What You Still Need to Do Manually:

1. **Train/Val Split:** Still need to split the exported `train_list.txt` manually
2. **Config Updates:** Still need to update `config_ft.yml` with paths
3. **Very Long Audio:** If you have 30+ second segments, consider re-segmenting shorter

---

## Common Issues & Solutions

### Issue: "Index out of range" during training
**Cause:** Transcripts contain digits or unsupported characters  
**Solution:** ~~Run `normalize_dataset.py`~~ **FIXED:** Export step now auto-normalizes

### Issue: "Expanded size of tensor (646) must match (512)"
**Cause:** Transcript too long (>450 chars)  
**Solution:** 
1. **Best:** Re-segment audio shorter in Step 2 (slider now limited to 30 sec max)
2. **Automatic:** Export step will truncate at sentence boundary
3. **Manual:** Run `normalize_dataset.py` if you manually edited transcripts

### Issue: Manual edits introduce errors
**Cause:** Typing digits or em-dashes manually  
**Solution:** After any manual edits, run `normalize_dataset.py` or re-export dataset

### Issue: WebUI slider allows 30 seconds but transcript still too long
**Cause:** Fast-paced speech can produce 600+ chars in 30 seconds  
**Solution:** Reduce slider to 15-20 seconds for dense dialogue/narration

### Issue: Training crashes on CUDA after loading model
**Cause:** Batch size too large for GPU VRAM  
**Solution:** Reduce `batch_size` in config (try 4, then 2)

---

## Tools Reference

### validate_dataset.py
**Purpose:** Check transcripts without modifying  
**Usage:**
```powershell
python validate_dataset.py path\to\manifest.txt
```
**Output:** Reports issues (length, digits, unsupported chars)

### normalize_dataset.py
**Purpose:** Auto-fix transcripts for compatibility  
**Usage:**
```powershell
# Preview changes
python normalize_dataset.py path\to\manifest.txt --preview

# Apply changes
python normalize_dataset.py path\to\manifest.txt --apply
```
**Actions:**
- Converts digits → words (using num2words library)
- Removes unsupported characters
- Truncates to 450 chars with sentence-aware splitting
- Logs all changes for review

---

## Best Practices

1. **Chunk audio short** (3-10 sec) to keep transcripts under 450 chars
2. **Always normalize** after Whisper transcription
3. **Validate before training** to catch issues early
4. **Never manually type digits** - use words ("eleven", not "11")
5. **Avoid long monologues** - split into multiple samples
6. **Check validation set** separately from training set
7. **Save original manifests** before normalizing (for reference)

---

## Manual Editing Guidelines

If you need to edit transcripts by hand:

✅ **DO:**
- Use words for numbers: "eleven", "twenty five"
- Use only basic punctuation: `.,!?:;'()`
- Keep sentences under 450 characters
- Use simple apostrophes `'` not curly quotes `'`

❌ **DON'T:**
- Type digits: `11`, `25`, `100`
- Use symbols: `%`, `&`, `#`, `-`, `—`
- Create overly long paragraphs
- Use special Unicode characters

After editing, **always run normalize_dataset.py** as a safety check.

---

## Future Improvements

If you frequently hit these limitations:

1. **Fine-tune PLBERT** with expanded vocabulary (advanced)
2. **Use alternative text encoder** (requires code changes)
3. **Pre-process with better text normalization** in Gradio UI
4. **Implement auto-chunking based on BERT token count** in WebUI

For now, the normalization script handles these issues automatically.
