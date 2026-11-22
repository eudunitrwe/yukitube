# Adds YukiTube to the Start menu and the desktop, pointing at YukiTube.exe in
# this folder, or removes those shortcuts with -Remove. The folder itself is
# never touched: YukiTube stays portable.
#
#   powershell -ExecutionPolicy Bypass -File App\shortcuts.ps1 [-Remove]

param([switch]$Remove)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root 'YukiTube.exe'
$places = [Environment]::GetFolderPath('Programs'), [Environment]::GetFolderPath('Desktop')

if ($Remove) {
    foreach ($place in $places) {
        foreach ($name in 'YukiTube.lnk', 'YukiTube - telecomanda.lnk') {
            $link = Join-Path $place $name
            if (Test-Path -LiteralPath $link) { Remove-Item -LiteralPath $link }
        }
    }
    Write-Host 'Scurtaturile YukiTube au fost sterse. Folderul YukiTube a ramas neatins.'
    exit 0
}

if (-not (Test-Path -LiteralPath $exe)) {
    Write-Error "Nu gasesc $exe. Ruleaza fisierul .cmd din folderul YukiTube dezarhivat."
}

$shell = New-Object -ComObject WScript.Shell
foreach ($place in $places) {
    $link = $shell.CreateShortcut((Join-Path $place 'YukiTube.lnk'))
    $link.TargetPath = $exe
    $link.WorkingDirectory = $root
    $link.IconLocation = "$exe,0"
    $link.Description = 'YouTube in fereastra lui, fara reclame, cu telecomanda'
    $link.Save()
}
# Only the remote, in the Start menu.
$link = $shell.CreateShortcut((Join-Path $places[0] 'YukiTube - telecomanda.lnk'))
$link.TargetPath = $exe
$link.Arguments = '--remote'
$link.WorkingDirectory = $root
$link.IconLocation = (Join-Path $root 'App\Remote\app\assets\yukitube.ico') + ',0'
$link.Description = 'Doar telecomanda YukiTube'
$link.Save()

Write-Host 'YukiTube a fost adaugat in meniul Start si pe Desktop.'
