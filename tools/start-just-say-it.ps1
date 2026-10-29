# Starts Ollama (Max's brain) and the Just Say It server, but only if they are not already running.
# Safe to run many times. It installs nothing and adds no auto-start entries.

$appDir = Split-Path -Parent $PSScriptRoot   # C:\dev\todo-app

function Port-InUse($port) {
    # True when something is already listening on this local port.
    $null -ne (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
}

# 1. Ollama (listens on port 11434)
if (Port-InUse 11434) {
    Write-Host "Ollama is already running."
} else {
    $ollama = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama app.exe"
    if (Test-Path $ollama) {
        Start-Process $ollama -WindowStyle Hidden
        Write-Host "Started Ollama."
    } else {
        Write-Host "Ollama not found at $ollama - install it from ollama.com."
    }
}

# 2. The server (port 8000)
if (Port-InUse 8000) {
    Write-Host "Server is already running on port 8000 - not starting another."
} else {
    Start-Process python -ArgumentList "server.py" -WorkingDirectory $appDir -WindowStyle Minimized
    Write-Host "Started server.py (minimized)."
}
