# Install VS Code Extensions
# This script installs all extensions listed in vscode-extensions.txt

$inputFile = Join-Path $PSScriptRoot "vscode-extensions.txt"

Write-Host "Installing VS Code extensions..." -ForegroundColor Cyan

# Check if extensions file exists
if (-not (Test-Path $inputFile)) {
    Write-Host "Error: Extensions file not found at $inputFile" -ForegroundColor Red
    Write-Host "Please run export-vscode-extensions.ps1 first" -ForegroundColor Yellow
    exit 1
}

try {
    # Read extensions from file
    $extensions = Get-Content $inputFile | Where-Object { $_ -and $_.Trim() }
    
    if (-not $extensions) {
        Write-Host "No extensions found in file" -ForegroundColor Red
        exit 1
    }
    
    $total = ($extensions | Measure-Object).Count
    $current = 0
    $installed = 0
    $failed = 0
    
    Write-Host "Found $total extensions to install`n" -ForegroundColor Yellow
    
    foreach ($extension in $extensions) {
        $current++
        Write-Host "[$current/$total] Installing $extension..." -ForegroundColor Cyan
        
        $result = code --install-extension $extension 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Installed successfully" -ForegroundColor Green
            $installed++
        } else {
            Write-Host "  ✗ Failed to install" -ForegroundColor Red
            $failed++
        }
    }
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Installation Summary:" -ForegroundColor Cyan
    Write-Host "  Total:     $total" -ForegroundColor Yellow
    Write-Host "  Installed: $installed" -ForegroundColor Green
    Write-Host "  Failed:    $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    if ($failed -gt 0) {
        Write-Host "Some extensions failed to install. You may need to install them manually." -ForegroundColor Yellow
    } else {
        Write-Host "All extensions installed successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
