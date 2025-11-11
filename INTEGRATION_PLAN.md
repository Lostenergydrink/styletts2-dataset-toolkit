# Integration Plan: Parent Folder → Repository

## Overview
This document tracks the integration of all improvements from `E:\AI\tts-webui\styletts2\` into the `styletts2-dataset-toolkit` repository.

## Status: 0/26 Complete

---

## Category 1: Core Dataset Tools (Critical)
**Priority: HIGHEST - These prevent training failures**

- [ ] **Task 1**: Copy `validate_dataset.py` to `styletts2-setup/`
  - Checks transcripts for: length >450 chars, digits, unsupported characters
  - Usage: `python validate_dataset.py datasets/name/train_list.txt`

- [ ] **Task 2**: Copy `normalize_dataset.py` to `styletts2-setup/`
  - Auto-fixes transcripts using num2words
  - Preview and apply modes
  - Usage: `python normalize_dataset.py datasets/name/train_list.txt --apply`

- [ ] **Task 3**: Copy enhanced `styletts2_webui.py` to `styletts2-setup/`
  - **Critical changes:**
    - Segment slider: 30-90sec → **3-30sec** (default 10sec)
    - Export step: built-in `normalize_transcript()` function
    - Automatic num2words conversion
    - Real-time normalization warnings

---

## Category 2: Documentation (Critical)
**Priority: HIGHEST - Users need to understand constraints**

- [ ] **Task 4**: Add `docs/DATASET_REQUIREMENTS.md`
  - 178-token vocabulary constraint (immutable)
  - 512 BERT token limit (~450 char safe limit)
  - Updated workflow with auto-normalization
  - Best practices, common issues, solutions

- [ ] **Task 5**: Add `docs/WEBUI_IMPROVEMENTS.md`
  - Technical changelog
  - Before/after code comparisons
  - Problem → solution mapping
  - Migration guide for old datasets

- [ ] **Task 6**: Update `docs/DATASET_PREP_GUIDE.md`
  - Replace outdated 60-second slider guidance
  - Document auto-normalization in export step
  - Add troubleshooting for vocab/BERT errors
  - Emphasize train/val split requirement

- [ ] **Task 21**: Create `docs/STYLETTS2_INSTALLATION.md`
  - Venv creation process
  - Dependency installation order
  - Pretrained model download and setup
  - Config file configuration
  - Validation steps before training

- [ ] **Task 22**: Update `docs/TROUBLESHOOTING.md`
  - Vocab mismatch errors: "index out of range"
  - BERT length errors: "expanded size must match (512)"
  - CUDA device errors: "srcIndex < srcSelectDimSize"
  - Windows DataLoader runaway processes
  - Checkpoint loading failures

---

## Category 3: StyleTTS2 Code Patches (High Priority)
**Priority: HIGH - Enables CPU fallback and Windows compatibility**

- [ ] **Task 7**: Create `styletts2-setup/patches/` directory structure
  ```
  styletts2-setup/patches/
  ├── train_finetune.py
  ├── meldataset.py
  ├── utils.py
  ├── models.py
  └── Modules/
      ├── hifigan.py
      ├── istftnet.py
      └── discriminators.py
  ```

- [ ] **Task 8**: Copy `train_finetune.py` with device handling
  - **Changes:**
    - Device config support: `cuda` / `cpu` / `auto`
    - Lines ~110-125: Device selection logic with fallback
    - Conditional DataParallel wrapping (only if CUDA)
    - Tensorboard optional import (try/except)
    - Validation loop division-by-zero fixes

- [ ] **Task 9**: Copy `meldataset.py` with Windows fix
  - **Changes:**
    - Platform detection: `import platform`
    - `safe_num_workers()` function in `build_dataloader()`
    - Force `num_workers=0` on Windows to prevent process fork bomb
    - TextCleaner: `logger.warning()` instead of `print()`

- [ ] **Task 10**: Copy `utils.py` with mask_from_lens fallback
  - **Changes:**
    - Lines 1-20: Try/except import for `mask_from_lens`
    - Fallback implementation for incomplete PyPI package
    - Creates mask tensor from sequence lengths

- [ ] **Task 11**: Copy `models.py` with path resolution
  - **Changes:**
    - `_resolve_project_path()` helper function
    - Multi-path search for ASR, F0, PLBERT models
    - Works from any working directory

- [ ] **Task 12**: Copy `Modules/hifigan.py` with device compatibility
  - **Changes:**
    - Replace `.to('cuda')` with `.to(F0_curve.device)`
    - Device-aware tensor creation throughout

- [ ] **Task 13**: Copy `Modules/istftnet.py` with device compatibility
  - **Changes:**
    - Replace `.to('cuda')` with `.to(N.device)`
    - Device-aware tensor operations

- [ ] **Task 14**: Copy `Modules/discriminators.py` (if modified)
  - Check for hardcoded `.to('cuda')` calls
  - Replace with device variables

---

## Category 4: Configuration & Examples (High Priority)

- [ ] **Task 15**: Copy example `config_ft.yml` to `styletts2-setup/configs/`
  - **Key settings:**
    ```yaml
    device: "auto"  # or "cuda" or "cpu"
    loader_params:
      train_num_workers: 0  # 0 for Windows
      val_num_workers: 0
    data_params:
      train_data: "path/to/train_list.txt"  # separate files!
      val_data: "path/to/val_list.txt"
    save_freq: 2
    epochs: 50
    batch_size: 8  # adjust for your GPU
    ```

- [ ] **Task 20**: Document train/val split requirement
  - Add to `DATASET_REQUIREMENTS.md`
  - Include PowerShell split commands:
    ```powershell
    Get-Content all.txt | Select-Object -First 35 > train_list.txt
    Get-Content all.txt | Select-Object -Last 7 > val_list.txt
    ```

- [ ] **Task 24**: Create `examples/dataset-structure/`
  - Sample `train_list.txt` format
  - Sample `val_list.txt` format
  - Directory layout example
  - Format explanation: `filename.wav|transcription|0`

---

## Category 5: Dependencies & Installation (High Priority)

- [ ] **Task 16**: Create comprehensive `styletts2-setup/requirements.txt`
  - **Core ML:**
    ```
    torch==2.6.0+cu124
    torchvision==0.21.0+cu124
    torchaudio==2.6.0+cu124
    transformers==4.57.1
    accelerate
    ```
  - **Audio:**
    ```
    librosa
    soundfile
    resampy
    pyworld
    phonemizer
    ```
  - **Text:**
    ```
    num2words  # CRITICAL for normalization
    sentencepiece
    g2p_en
    inflect
    unidecode
    nltk
    jiwer
    ```
  - **Utils:**
    ```
    pyyaml
    munch
    pandas
    numpy
    scipy
    matplotlib
    click
    tensorboard
    ipython
    ```
  - **StyleTTS2-specific:**
    ```
    einops
    einops-exts
    rotary-embedding-torch
    torch-stft
    pytorch-wavelets
    git+https://github.com/resemble-ai/monotonic_align.git
    ```
  - **WebUI:**
    ```
    gradio
    whisper
    pydub
    ```

- [ ] **Task 17**: Document PyTorch version requirement
  - Add to `INSTALLATION.md`
  - **Why:** CVE-2025-32434 security vulnerability in `torch.load`
  - **Command:**
    ```powershell
    pip install torch==2.6.0+cu124 torchvision==0.21.0+cu124 torchaudio==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124
    ```

- [ ] **Task 18**: Document pretrained model requirements
  - **LibriTTS model:** `Models/LibriTTS/epochs_2nd_00020.pth`
    - Download: [HuggingFace Link]
    - Size: ~1-2GB
  - **ASR model:** `Utils/ASR/epoch_00080.pth`
  - **F0 model (JDC):** `Utils/JDC/bst.t7`
  - **PLBERT model:** `Utils/PLBERT/` directory
  - Add directory structure diagram
  - Include validation command to check all models exist

- [ ] **Task 19**: Update `README.md` dependencies section
  - Add `num2words` to dependencies list
  - Mention 178-token vocabulary constraint
  - Mention 512 BERT token limit
  - Note Windows `num_workers=0` requirement
  - Link to `DATASET_REQUIREMENTS.md` for details

---

## Category 6: Launcher Scripts (Medium Priority)

- [ ] **Task 3**: Copy training launcher scripts
  - `train_styletts2.bat` → `styletts2-setup/`
  - `train_styletts2.ps1` → `styletts2-setup/`
  - **Features:**
    - Virtual environment activation
    - Path validation (venv, script, config)
    - Working directory handling
    - Clear status messages

---

## Category 7: Automation & Testing (Medium Priority)

- [ ] **Task 25**: Create `styletts2-setup/apply_patches.ps1`
  - Prompts user for StyleTTS2 clone location
  - Backs up original files to `original_backups/`
  - Copies all patches from `patches/` to StyleTTS2 directory
  - Validates file checksums
  - Provides rollback capability

- [ ] **Task 23**: Document venv rebuild process
  - Add to `TROUBLESHOOTING.md`
  - **Symptoms:** Permission errors, corrupted .pyd files (WinError 5)
  - **Solution:**
    ```powershell
    Remove-Item -Path ".venv" -Recurse -Force
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    # Reinstall dependencies in order...
    ```

- [ ] **Task 26**: Test complete workflow on clean machine
  - Clone repo
  - Run `install.ps1`
  - Apply patches with `apply_patches.ps1`
  - Create test dataset with WebUI
  - Validate with `validate_dataset.py`
  - Start training
  - Document any missing steps or dependencies

---

## Critical Path (Do These First)

### Phase 1: Core Functionality (Tasks 1-6)
These prevent users from hitting the same training failures:
1. Copy dataset tools (validate, normalize)
2. Copy enhanced WebUI with auto-normalization
3. Add critical documentation (DATASET_REQUIREMENTS, WEBUI_IMPROVEMENTS)
4. Update DATASET_PREP_GUIDE with correct workflow

### Phase 2: Code Patches (Tasks 7-14)
Enable CPU fallback and Windows compatibility:
1. Create patches directory
2. Copy all modified Python files with device handling
3. Copy Windows DataLoader fix

### Phase 3: Configuration (Tasks 15-20)
Provide working examples and clear guidelines:
1. Example config with device='auto'
2. Train/val split documentation
3. Dataset structure examples

### Phase 4: Dependencies (Tasks 16-19)
Ensure reproducible setup:
1. Comprehensive requirements.txt
2. PyTorch version documentation
3. Pretrained model download guide
4. Update README

### Phase 5: Polish (Tasks 21-26)
Complete the package:
1. Installation guide
2. Troubleshooting section
3. Patch application automation
4. End-to-end testing

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `validate_dataset.py` runs without errors
- [ ] `normalize_dataset.py` converts digits correctly
- [ ] WebUI slider shows 3-30 second range
- [ ] WebUI export shows normalization summary
- [ ] `DATASET_REQUIREMENTS.md` explains 178-token limit
- [ ] `config_ft.yml` includes `device: auto` and `loader_params`
- [ ] All patches apply cleanly to fresh StyleTTS2 clone
- [ ] Training starts successfully on CPU
- [ ] Training starts successfully on CUDA
- [ ] Windows DataLoader doesn't spawn extra processes
- [ ] README mentions all critical dependencies
- [ ] Installation guide covers all steps
- [ ] Troubleshooting covers vocab and BERT errors

---

## Dependencies Reference

### Critical Additions
- **num2words** - Converts digits to words (20 → "twenty")
- **tensorboard** - Training monitoring (optional but recommended)
- **monotonic_align** - From GitHub, not PyPI (PyPI version incomplete)

### Version-Specific Requirements
- **PyTorch 2.6.0+cu124** - Security fix for CVE-2025-32434
- **Transformers 4.57.1** - Requires PyTorch 2.6+ for security

### Platform-Specific
- **Windows:** Must use `num_workers=0` in DataLoader
- **CUDA 12.4:** Required for PyTorch 2.6.0+cu124

---

## Notes

### Why This Matters
The repository currently documents a **broken workflow** that will cause:
- Vocabulary mismatch errors (digits in transcripts)
- BERT length errors (transcripts >450 chars)
- Windows process fork bombs (num_workers >0)
- CPU training failures (hardcoded CUDA)

The parent folder contains **all the fixes** that make it actually work.

### Migration for Existing Users
Users with the old repository version should:
1. Pull latest changes
2. Run `normalize_dataset.py` on existing datasets
3. Update config files with new parameters
4. Apply code patches to their StyleTTS2 clone

---

**Last Updated:** November 10, 2025
**Status:** Planning Phase - Ready to Execute
