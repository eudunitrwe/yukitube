# Removes YukiTube's shortcuts. Its Firefox profile (sign-in, history, add-on
# settings) stays unless -RemoveData is given.
#
#   powershell -ExecutionPolicy Bypass -File windows\uninstall.ps1 [-RemoveData]

param([switch]$RemoveData)

$ErrorActionPreference = 'Stop'

foreach ($place in [Environment]::GetFolderPath('Programs'), [Environment]::GetFolderPath('Desktop')) {
    $link = Join-Path $place 'YukiTube.lnk'
    if (Test-Path -LiteralPath $link) { Remove-Item -LiteralPath $link }
}

$root = Join-Path $env:LOCALAPPDATA 'yukitube'
if ($RemoveData -and (Test-Path -LiteralPath $root)) {
    Remove-Item -LiteralPath $root -Recurse
    Write-Host "Removed YukiTube and its profile."
} else {
    Write-Host "Removed YukiTube's shortcuts. Its profile is still in $root."
}
