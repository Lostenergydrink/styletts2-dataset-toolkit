# StyleTTS2 Patch Application Script
# Automatically applies code patches to a StyleTTS2 installation

param(
    [string]$StyleTTS2Path = "",
    [switch]$NoBackup = $false,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  StyleTTS2 Patch Application Script" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PatchesDir = Join-Path $ScriptDir "patches"

# Check if patches directory exists
if (-not (Test-Path $PatchesDir)) {
    Write-Host "❌ Error: Patches directory not found at: $PatchesDir" -ForegroundColor Red
    exit 1
}

# Get StyleTTS2 path
if (-not $StyleTTS2Path) {
    Write-Host "Enter the path to your StyleTTS2 installation:" -ForegroundColor Yellow
    Write-Host "(e.g., C:\Users\YourName\StyleTTS2)" -ForegroundColor Gray
    $StyleTTS2Path = Read-Host "Path"
}

# Validate StyleTTS2 path
if (-not (Test-Path $StyleTTS2Path)) {
    Write-Host "❌ Error: StyleTTS2 directory not found at: $StyleTTS2Path" -ForegroundColor Red
    exit 1
}

# Check for key StyleTTS2 files
$RequiredFiles = @("train_finetune.py", "meldataset.py", "models.py", "utils.py")
$MissingFiles = @()

foreach ($file in $RequiredFiles) {
    $filePath = Join-Path $StyleTTS2Path $file
    if (-not (Test-Path $filePath)) {
        $MissingFiles += $file
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "❌ Error: This doesn't appear to be a valid StyleTTS2 installation." -ForegroundColor Red
    Write-Host "Missing files: $($MissingFiles -join ', ')" -ForegroundColor Red
    exit 1
}

Write-Host "✅ StyleTTS2 installation found" -ForegroundColor Green
Write-Host "   Location: $StyleTTS2Path`n" -ForegroundColor Gray

# List patches to apply
Write-Host "Patches to apply:" -ForegroundColor Cyan
Write-Host "  - train_finetune.py (device compatibility, validation fixes)" -ForegroundColor White
Write-Host "  - meldataset.py (Windows DataLoader fix)" -ForegroundColor White
Write-Host "  - utils.py (mask_from_lens fallback)" -ForegroundColor White
Write-Host "  - models.py (path resolution)" -ForegroundColor White
Write-Host "  - Modules/hifigan.py (device compatibility)" -ForegroundColor White
Write-Host "  - Modules/istftnet.py (device compatibility)" -ForegroundColor White
Write-Host "  - Modules/discriminators.py (completeness)" -ForegroundColor White
Write-Host ""

# Confirm
if (-not $Force) {
    $response = Read-Host "Apply these patches? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "❌ Cancelled by user" -ForegroundColor Yellow
        exit 0
    }
}

# Create backup directory
if (-not $NoBackup) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $BackupDir = Join-Path $StyleTTS2Path "original_backups_$timestamp"
    
    Write-Host "`nCreating backup directory..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $BackupDir "Modules") -Force | Out-Null
    
    Write-Host "✅ Backup directory created: $BackupDir" -ForegroundColor Green
}

# Apply patches
Write-Host "`nApplying patches..." -ForegroundColor Cyan

$PatchFiles = @(
    @{Source="train_finetune.py"; Dest="train_finetune.py"},
    @{Source="meldataset.py"; Dest="meldataset.py"},
    @{Source="utils.py"; Dest="utils.py"},
    @{Source="models.py"; Dest="models.py"},
    @{Source="Modules\hifigan.py"; Dest="Modules\hifigan.py"},
    @{Source="Modules\istftnet.py"; Dest="Modules\istftnet.py"},
    @{Source="Modules\discriminators.py"; Dest="Modules\discriminators.py"}
)

$SuccessCount = 0
$FailCount = 0

foreach ($patch in $PatchFiles) {
    $sourcePath = Join-Path $PatchesDir $patch.Source
    $destPath = Join-Path $StyleTTS2Path $patch.Dest
    
    if (-not (Test-Path $sourcePath)) {
        Write-Host "  ⚠️  Skipping $($patch.Source) (patch file not found)" -ForegroundColor Yellow
        continue
    }
    
    try {
        # Backup original if requested
        if (-not $NoBackup -and (Test-Path $destPath)) {
            $backupPath = Join-Path $BackupDir $patch.Dest
            $backupDir = Split-Path -Parent $backupPath
            if (-not (Test-Path $backupDir)) {
                New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
            }
            Copy-Item $destPath $backupPath -Force
        }
        
        # Copy patch
        Copy-Item $sourcePath $destPath -Force
        Write-Host "  ✅ $($patch.Dest)" -ForegroundColor Green
        $SuccessCount++
    }
    catch {
        Write-Host "  ❌ Failed to patch $($patch.Dest): $_" -ForegroundColor Red
        $FailCount++
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Patch Application Complete" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Results:" -ForegroundColor White
Write-Host "  ✅ Successfully patched: $SuccessCount file(s)" -ForegroundColor Green
if ($FailCount -gt 0) {
    Write-Host "  ❌ Failed: $FailCount file(s)" -ForegroundColor Red
}
if (-not $NoBackup) {
    Write-Host "  💾 Backups saved to: $BackupDir" -ForegroundColor Cyan
}

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Update your config_ft.yml:" -ForegroundColor White
Write-Host "     - Set device: 'auto' (or 'cuda' / 'cpu')" -ForegroundColor Gray
Write-Host "     - Add loader_params with num_workers: 0" -ForegroundColor Gray
Write-Host "     - Use separate train_data and val_data files" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. See example config at:" -ForegroundColor White
Write-Host "     $ScriptDir\configs\config_ft.yml" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Verify patches worked:" -ForegroundColor White
Write-Host "     cd $StyleTTS2Path" -ForegroundColor Gray
Write-Host "     python -c `"from train_finetune import main; print('✅ OK')`"" -ForegroundColor Gray
Write-Host ""

if (-not $NoBackup) {
    Write-Host "To rollback patches:" -ForegroundColor Yellow
    Write-Host "  Copy-Item $BackupDir\* $StyleTTS2Path -Recurse -Force" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "For detailed documentation, see:" -ForegroundColor Cyan
Write-Host "  - docs/DATASET_REQUIREMENTS.md" -ForegroundColor Gray
Write-Host "  - docs/STYLETTS2_INSTALLATION.md" -ForegroundColor Gray
Write-Host "  - styletts2-setup/patches/README.md" -ForegroundColor Gray
Write-Host ""

if ($SuccessCount -eq $PatchFiles.Count) {
    Write-Host "🎉 All patches applied successfully!" -ForegroundColor Green
    exit 0
} elseif ($FailCount -gt 0) {
    Write-Host "⚠️  Some patches failed. Check errors above." -ForegroundColor Yellow
    exit 1
} else {
    exit 0
}
