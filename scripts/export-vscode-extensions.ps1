# Export VS Code Extensions
# This script exports all currently installed VS Code extensions to a file

$outputFile = Join-Path $PSScriptRoot "vscode-extensions.txt"

Write-Host "Exporting VS Code extensions..." -ForegroundColor Cyan

try {
    # Get list of installed extensions
    $extensions = code --list-extensions
    
    if ($extensions) {
        # Save to file
        $extensions | Out-File -FilePath $outputFile -Encoding UTF8
        
        $count = ($extensions | Measure-Object).Count
        Write-Host "✓ Successfully exported $count extensions to:" -ForegroundColor Green
        Write-Host "  $outputFile" -ForegroundColor Yellow
    } else {
        Write-Host "No extensions found or VS Code is not in PATH" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
