# Port Management Utility for StyleTTS2 WebUI
# This script helps manage port conflicts for the StyleTTS2 WebUI

param(
    [int]$Port = 7860,
    [switch]$Kill,
    [switch]$List
)

function Get-PortProcess {
    param([int]$PortNumber)
    
    $connections = Get-NetTCPConnection -LocalPort $PortNumber -ErrorAction SilentlyContinue
    
    if ($connections) {
        foreach ($conn in $connections) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                [PSCustomObject]@{
                    Port = $PortNumber
                    ProcessId = $process.Id
                    ProcessName = $process.ProcessName
                    State = $conn.State
                }
            }
        }
    }
}

function Stop-PortProcess {
    param([int]$PortNumber)
    
    $processes = Get-PortProcess -PortNumber $PortNumber
    
    if ($processes) {
        Write-Host "Found processes using port ${PortNumber}:" -ForegroundColor Yellow
        $processes | Format-Table -AutoSize
        
        $confirmation = Read-Host "Kill these processes? (y/n)"
        if ($confirmation -eq 'y') {
            foreach ($proc in $processes) {
                try {
                    Stop-Process -Id $proc.ProcessId -Force
                    Write-Host "✓ Killed process $($proc.ProcessName) (PID: $($proc.ProcessId))" -ForegroundColor Green
                } catch {
                    Write-Host "✗ Failed to kill process $($proc.ProcessName) (PID: $($proc.ProcessId))" -ForegroundColor Red
                    Write-Host "  Try running as Administrator" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "Operation cancelled." -ForegroundColor Gray
        }
    } else {
        Write-Host "✓ Port $PortNumber is free" -ForegroundColor Green
    }
}

function Show-PortRange {
    param(
        [int]$StartPort = 7860,
        [int]$EndPort = 7869
    )
    
    Write-Host "`nScanning ports $StartPort to $EndPort..." -ForegroundColor Cyan
    Write-Host ""
    
    $results = @()
    for ($port = $StartPort; $port -le $EndPort; $port++) {
        $proc = Get-PortProcess -PortNumber $port
        if ($proc) {
            $results += $proc
            Write-Host "Port $port : BUSY ($($proc.ProcessName))" -ForegroundColor Red
        } else {
            Write-Host "Port $port : FREE" -ForegroundColor Green
        }
    }
    
    if ($results) {
        Write-Host "`nProcesses found:" -ForegroundColor Yellow
        $results | Format-Table -AutoSize
    } else {
        Write-Host "`n✓ All ports in range are free!" -ForegroundColor Green
    }
}

# Main script logic
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   StyleTTS2 Port Management Utility" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

if ($List) {
    Show-PortRange -StartPort $Port -EndPort ($Port + 9)
} elseif ($Kill) {
    Stop-PortProcess -PortNumber $Port
} else {
    # Default: Check specific port
    Write-Host "Checking port $Port..." -ForegroundColor Cyan
    Write-Host ""
    
    $proc = Get-PortProcess -PortNumber $Port
    
    if ($proc) {
        Write-Host "Port $Port is BUSY:" -ForegroundColor Red
        $proc | Format-Table -AutoSize
        
        Write-Host ""
        Write-Host "Options:" -ForegroundColor Yellow
        Write-Host "  1. Kill the process: .\check_port.ps1 -Port $Port -Kill" -ForegroundColor Gray
        Write-Host "  2. Use a different port: python styletts2_webui.py --server_port 7865" -ForegroundColor Gray
        Write-Host "  3. Check port range: .\check_port.ps1 -Port $Port -List" -ForegroundColor Gray
    } else {
        Write-Host "✓ Port $Port is FREE" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Examples:" -ForegroundColor Cyan
Write-Host "  .\check_port.ps1 -Port 7860          # Check if port 7860 is free" -ForegroundColor Gray
Write-Host "  .\check_port.ps1 -Port 7860 -Kill    # Kill process using port 7860" -ForegroundColor Gray
Write-Host "  .\check_port.ps1 -Port 7860 -List    # List all ports 7860-7869" -ForegroundColor Gray
Write-Host ""
