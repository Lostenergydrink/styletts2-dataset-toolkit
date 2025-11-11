# StyleTTS2 Code Patches

This directory contains modified StyleTTS2 files that fix critical issues with the original codebase.

## What's Fixed

### 1. **Device Compatibility** (`train_finetune.py`, `train_first.py`, `train_second.py`)
- **Problem:** Hardcoded `.to('cuda')` calls crash on CPU-only systems
- **Solution:** Config-driven device selection (`cuda` / `cpu` / `auto`)
- **Features:**
  - Auto-detection: `device: "auto"` falls back to CPU if CUDA unavailable
  - Conditional DataParallel: Only wraps models when CUDA is available
  - Clear logging of which device is being used

### 2. **Windows DataLoader Fix** (`meldataset.py`)
- **Problem:** `num_workers > 0` causes runaway process spawning on Windows
- **Solution:** Platform detection that forces `num_workers=0` on Windows
- **Impact:** Prevents dozens of console windows opening during training

### 3. **Vocabulary Compatibility** (`utils.py`)
- **Problem:** PyPI `monotonic_align` package missing `mask_from_lens` function
- **Solution:** Fallback implementation when function not found
- **Details:** Creates mask tensor from sequence lengths

### 4. **Model Loading** (`models.py`)
- **Problem:** Pretrained models fail to load when running from different directories
- **Solution:** `_resolve_project_path()` helper that searches multiple locations
- **Searches:** Current dir, parent dirs, Utils/ subdirectory

### 5. **Vocoder Device Handling** (`Modules/hifigan.py`, `Modules/istftnet.py`)
- **Problem:** Hardcoded `.to('cuda')` in vocoder modules
- **Solution:** Device-aware tensor creation using input tensor's device
- **Example:** `.to(F0_curve.device)` instead of `.to('cuda')`

### 6. **TensorBoard Optional** (`train_finetune.py`)
- **Problem:** Training crashes if TensorBoard not installed
- **Solution:** Try/except import with graceful degradation
- **Result:** Training continues without logging if TensorBoard unavailable

### 7. **Validation Loop Fixes** (`train_finetune.py`)
- **Problem:** Division by zero errors when validation set is small
- **Solution:** Safety checks for `iters_test` and short samples
- **Impact:** Stable training with small validation sets

## How to Apply Patches

### Option 1: Automatic (Recommended)
```powershell
# From repository root
.\styletts2-setup\apply_patches.ps1
```

### Option 2: Manual
```powershell
# Navigate to your StyleTTS2 clone
cd path\to\StyleTTS2

# Backup originals
mkdir original_backups
Copy-Item train_finetune.py original_backups\
Copy-Item meldataset.py original_backups\
Copy-Item utils.py original_backups\
Copy-Item models.py original_backups\
Copy-Item Modules\hifigan.py original_backups\
Copy-Item Modules\istftnet.py original_backups\

# Apply patches
Copy-Item path\to\styletts2-dataset-toolkit\styletts2-setup\patches\*.py .
Copy-Item path\to\styletts2-dataset-toolkit\styletts2-setup\patches\Modules\*.py Modules\
```

## Configuration Required

After applying patches, update your `config_ft.yml`:

```yaml
# Device selection (auto-detects)
device: "auto"  # or "cuda" or "cpu"

# Windows-specific: must be 0
loader_params:
  train_num_workers: 0
  val_num_workers: 0

# Separate train/val files (required!)
data_params:
  train_data: "path/to/train_list.txt"
  val_data: "path/to/val_list.txt"  # Must be different file!
  root_path: "path/to/dataset"
```

## Files in This Directory

- `train_finetune.py` - Fine-tuning script with all fixes
- `meldataset.py` - Dataset loader with Windows fix
- `utils.py` - Utilities with mask_from_lens fallback
- `models.py` - Model builder with path resolution
- `Modules/hifigan.py` - HiFi-GAN vocoder with device compatibility
- `Modules/istftnet.py` - iSTFTNet vocoder with device compatibility
- `Modules/discriminators.py` - Discriminators (copied for completeness)

## Verification

After applying patches, verify they work:

```powershell
# Test device detection
cd StyleTTS2
python -c "import yaml; config = yaml.safe_load(open('Configs/config_ft.yml')); print(f'Device: {config.get(\"device\", \"not set\")}')"

# Test training import
python -c "from train_finetune import main; print('✅ Training script imports successfully')"

# Test mask_from_lens fallback
python -c "from utils import mask_from_lens; print('✅ mask_from_lens available')"
```

## Compatibility

These patches are compatible with:
- StyleTTS2 commit: `main` branch (as of November 2025)
- Python: 3.10, 3.11, 3.12
- PyTorch: 2.5.1+, 2.6.0+ (2.6.0+ recommended for security)
- Windows: 10, 11
- Linux: Ubuntu 20.04+, other distros (untested but should work)

## Rollback

If you need to restore original files:

```powershell
cd StyleTTS2
Copy-Item original_backups\*.py .
Copy-Item original_backups\Modules\*.py Modules\
```

## Changelog

### v1.0.0 (November 2025)
- Initial patch set
- Device compatibility for CPU/CUDA
- Windows DataLoader fix
- Vocabulary compatibility
- Model loading improvements
- TensorBoard optional
- Validation loop fixes

## Related Documentation

- [DATASET_REQUIREMENTS.md](../../docs/DATASET_REQUIREMENTS.md) - Vocabulary constraints
- [WEBUI_IMPROVEMENTS.md](../../docs/WEBUI_IMPROVEMENTS.md) - WebUI changes
- [STYLETTS2_INSTALLATION.md](../../docs/STYLETTS2_INSTALLATION.md) - Full setup guide
- [TROUBLESHOOTING.md](../../docs/TROUBLESHOOTING.md) - Common issues
