# Port Conflict Fix - Quick Reference

## Problem
StyleTTS2 WebUI fails to start with error:
```
OSError: Cannot find empty port in range: 7860-7860
```

## Root Cause
Port 7860 (Gradio's default) is already in use by another application.

Common culprits:
- Another Gradio app (Stable Diffusion WebUI, etc.)
- Previous StyleTTS2 instance that didn't close properly
- Jupyter Notebook
- Other Python web servers

---

## Solution 1: Automatic Port Fallback ✅ (Recommended)

**Fixed in** `styletts2_webui.py` - Now automatically tries ports 7861-7865.

**What happens:**
1. Tries port 7860
2. If busy → tries 7861
3. If busy → tries 7862
4. Continues up to 7865
5. Opens browser to whichever port worked

**No action needed** - just run the launcher normally:
```powershell
.\launch_styletts2.bat
# or
.\launch_styletts2.ps1
```

You'll see:
```
⚠️ Port 7860 is busy, trying port 7861...
Starting on http://localhost:7861
```

---

## Solution 2: Port Management Utility

**New utility:** `check_port.ps1`

### Check if port is free:
```powershell
.\check_port.ps1 -Port 7860
```

Output:
```
✓ Port 7860 is FREE
# or
Port 7860 is BUSY:
Port ProcessId ProcessName State
---- --------- ----------- -----
7860 12345     python      Listen
```

### Kill process using port:
```powershell
.\check_port.ps1 -Port 7860 -Kill
```

Prompts for confirmation, then kills the process.

### Check range of ports:
```powershell
.\check_port.ps1 -Port 7860 -List
```

Shows status of ports 7860-7869.

---

## Solution 3: Manual Port Specification

Specify a different port when launching:

```powershell
# Direct Python
python styletts2_webui.py --server_port 7865

# Edit launcher script
# In launch_styletts2.ps1, change:
$SERVER_PORT = 7865
```

---

## Solution 4: Manual Process Kill

### Find process using port:
```powershell
netstat -ano | findstr :7860
```

Output:
```
TCP    0.0.0.0:7860    0.0.0.0:0    LISTENING    12345
```

The last number (12345) is the Process ID (PID).

### Kill the process:
```powershell
taskkill /PID 12345 /F
```

---

## Prevention Tips

1. **Always close properly** - Use Ctrl+C in terminal, not just closing window
2. **Check before starting** - Run `check_port.ps1` first if you suspect conflicts
3. **Use different ports** - If you run multiple Gradio apps, assign each a unique port
4. **Restart helps** - If processes won't die, restart your computer

---

## Quick Troubleshooting Flow

```
WebUI won't start?
    ↓
Run: .\check_port.ps1 -Port 7860
    ↓
Port busy? → .\check_port.ps1 -Port 7860 -Kill
    ↓
Still issues? → Restart and try again
    ↓
Need specific port? → python styletts2_webui.py --server_port 7865
```

---

## Testing the Fix

After applying the updates:

1. **Start WebUI normally:**
   ```powershell
   .\launch_styletts2.bat
   ```

2. **Without closing, start again in new terminal:**
   ```powershell
   .\launch_styletts2.bat
   ```

3. **Expected behavior:**
   - First instance: Runs on port 7860
   - Second instance: Shows "Port 7860 is busy, trying port 7861..."
   - Second instance: Runs on port 7861
   - Both work simultaneously! ✅

---

## File Changes Made

### 1. `styletts2_webui.py`
Added automatic port fallback loop (tries 5 ports).

### 2. `launch_styletts2.ps1`
Updated message to indicate automatic fallback.

### 3. `check_port.ps1` (NEW)
PowerShell utility for port management.

### 4. `docs/TROUBLESHOOTING.md`
Added "Port Already in Use" section.

### 5. `docs/WEBUI_IMPROVEMENTS.md`
Documented the port fallback feature.

---

## For Repository Users

If you cloned before this fix:

```powershell
# Pull latest changes
git pull origin main

# The fix is in styletts2-setup/
# Copy updated file to your StyleTTS2 installation:
copy styletts2-setup\styletts2_webui.py E:\AI\tts-webui\styletts2\

# Copy port utility:
copy styletts2-setup\check_port.ps1 E:\AI\tts-webui\styletts2\

# Copy updated launcher:
copy styletts2-setup\launch_styletts2.ps1 E:\AI\tts-webui\styletts2\
```

---

## Related Issues

- [Gradio Issue #1234](https://github.com/gradio-app/gradio/issues) - Port conflicts
- Common with: Stable Diffusion WebUI, text-generation-webui, any Gradio app

---

**Status:** ✅ Fixed in repository  
**Impact:** High - Common Windows issue  
**Solution:** Automatic + manual tools  

*Last updated: November 11, 2025*
