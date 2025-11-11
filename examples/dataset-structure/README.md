# StyleTTS2 Dataset Structure Example

This directory shows the correct format for StyleTTS2 training datasets.

## Directory Structure

```
your-dataset/
├── audio_001.wav
├── audio_002.wav
├── audio_003.wav
├── ...
├── train_list.txt    ← Training manifest
└── val_list.txt      ← Validation manifest (separate file!)
```

## Manifest File Format

Each line in `train_list.txt` and `val_list.txt` follows this format:

```
filename.wav|transcription|speaker_id
```

### Components:

1. **filename.wav** - Name of the audio file (relative to root_path)
2. **transcription** - Text content (must follow vocabulary constraints!)
3. **speaker_id** - Integer speaker ID (use `0` for single-speaker)

### Example Files:

See `train_list_example.txt` and `val_list_example.txt` in this directory.

## Critical Requirements

### 1. Vocabulary Constraints (IMMUTABLE)

Transcriptions must ONLY contain these 178 characters:
- **Letters:** A-Z, a-z
- **Punctuation:** `!`, `'`, `(`, `)`, `,`, `.`, `:`, `;`, `?`, space

**NOT allowed:**
- ❌ Digits: `0-9`
- ❌ Symbols: `%`, `-`, `&`, `#`, `@`, `—`, etc.
- ❌ Special Unicode characters

**Example violations and fixes:**
```
❌ "The year was 1984"          → ✅ "The year was nineteen eighty four"
❌ "It's 25% complete"           → ✅ "It's twenty five percent complete"
❌ "End-to-end solution"         → ✅ "End to end solution"
❌ "Temperature: -5°C"           → ✅ "Temperature negative five degrees"
```

### 2. Length Constraints

- **Maximum:** ~450 characters (BERT has 512 token limit)
- **Recommended:** 50-300 characters per sample
- **Audio duration:** 3-30 seconds (corresponds to safe transcript lengths)

**Why?** StyleTTS2 uses PLBERT with 512 max position embeddings. Longer transcripts cause training crashes.

### 3. Separate Train/Val Files

⚠️ **CRITICAL:** You MUST use different files for training and validation!

**❌ Wrong:**
```yaml
data_params:
  train_data: "dataset/train_list.txt"
  val_data: "dataset/train_list.txt"    # Same file - BAD!
```

**✅ Correct:**
```yaml
data_params:
  train_data: "dataset/train_list.txt"
  val_data: "dataset/val_list.txt"      # Different file - GOOD!
```

## Audio File Requirements

- **Format:** WAV (16-bit or 24-bit)
- **Sample Rate:** 24000 Hz (will be resampled if different)
- **Channels:** Mono (will be converted if stereo)
- **Duration:** 3-30 seconds recommended
- **Quality:** Clean vocals, minimal background noise

## Creating Your Dataset

### Using the WebUI (Automatic - Recommended)

1. Import audio → 2. Segment (3-30 sec) → 3. Transcribe → 4. Export

The WebUI **automatically normalizes** transcripts during export:
- Converts digits to words
- Removes unsupported characters
- Truncates long transcripts

No manual intervention needed!

### Manual Creation

If creating manifests manually:

1. **Prepare audio:**
   ```powershell
   ffmpeg -i input.mp3 -ar 24000 -ac 1 output.wav
   ```

2. **Transcribe** (use Whisper, Azure Speech, etc.)

3. **Normalize transcripts:**
   ```powershell
   python styletts2-setup/normalize_dataset.py your-dataset/all_samples.txt --apply
   ```

4. **Split train/val:**
   ```powershell
   # 90/10 split example
   Get-Content all_samples.txt | Select-Object -First 90 > train_list.txt
   Get-Content all_samples.txt | Select-Object -Last 10 > val_list.txt
   ```

5. **Validate:**
   ```powershell
   python styletts2-setup/validate_dataset.py your-dataset/train_list.txt
   python styletts2-setup/validate_dataset.py your-dataset/val_list.txt
   ```

## Validation Before Training

Always validate your dataset before training:

```powershell
cd styletts2-dataset-toolkit
python styletts2-setup/validate_dataset.py datasets/your-dataset/train_list.txt
```

**Output should show:**
```
✅ All transcripts are valid!
```

If you see warnings:
- Run `normalize_dataset.py` with `--apply` flag
- Re-validate until clean

## Common Mistakes

### 1. Using same file for train and val
**Symptom:** Validation metrics don't make sense, overfitting
**Fix:** Create separate val_list.txt

### 2. Digits in transcripts
**Symptom:** "index out of range in gather" errors during training
**Fix:** Run normalize_dataset.py or re-export from WebUI

### 3. Transcripts too long
**Symptom:** "expanded size must match (512)" errors
**Fix:** Re-segment audio shorter (10-15 sec chunks)

### 4. Wrong file paths
**Symptom:** "FileNotFoundError" during training
**Fix:** Use absolute paths in config_ft.yml or ensure relative paths are correct

### 5. Incorrect format
**Symptom:** Training crashes immediately or unexpected behavior
**Fix:** Ensure format is exactly `filename.wav|transcription|0` with pipes (`|`)

## Dataset Size Guidelines

| Dataset Size | Training Time* | Quality |
|--------------|---------------|---------|
| 30 minutes   | ~2 hours      | Good - recognizable voice |
| 1-2 hours    | ~4-8 hours    | Great - natural speech |
| 4+ hours     | ~12-24 hours  | Excellent - near-perfect |

*On RTX 3060 12GB with batch_size=4

## Tips for High-Quality Datasets

1. **Use stem separation** to isolate clean vocals
2. **Consistent audio quality** - same recording environment
3. **Diverse content** - various sentence structures and emotions
4. **Accurate transcripts** - review Whisper outputs for errors
5. **Short segments** - 5-15 seconds ideal
6. **Clean boundaries** - avoid cutting mid-word
7. **Remove silent sections** - trim leading/trailing silence

## Related Documentation

- [DATASET_REQUIREMENTS.md](../../docs/DATASET_REQUIREMENTS.md) - Detailed constraints
- [DATASET_PREP_GUIDE.md](../../docs/DATASET_PREP_GUIDE.md) - Full workflow
- [WEBUI_IMPROVEMENTS.md](../../docs/WEBUI_IMPROVEMENTS.md) - Auto-normalization details
