# Installs YukiTube for the current Windows user: YouTube in its own Firefox
# window, with uBlock Origin and YouTube NonStop.
#
#   powershell -ExecutionPolicy Bypass -File windows\install.ps1 [-Desktop]
#
# Run it again at any time to repair the profile or pick up a new version.
# Works on Windows PowerShell 5.1 (Windows 10) and PowerShell 7.

param(
    # Also put a shortcut on the desktop.
    [switch]$Desktop
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$share = Join-Path (Split-Path -Parent $here) 'share'
$root = Join-Path $env:LOCALAPPDATA 'yukitube'
$profileDir = Join-Path $root 'profile'

function Find-Firefox {
    foreach ($key in 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe',
                     'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe') {
        $path = (Get-ItemProperty -Path $key -ErrorAction SilentlyContinue).'(default)'
        if ($path -and (Test-Path $path)) { return $path }
    }
    foreach ($dir in $env:ProgramFiles, ${env:ProgramFiles(x86)}, (Join-Path $env:LOCALAPPDATA 'Programs')) {
        if (-not $dir) { continue }
        $path = Join-Path $dir 'Mozilla Firefox\firefox.exe'
        if (Test-Path $path) { return $path }
    }
    return $null
}

# Firefox reads its pref files as UTF-8, and a byte order mark breaks them.
function Write-Utf8 ($path, $text) {
    [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding $false))
}

$firefox = Find-Firefox
if (-not $firefox) {
    Write-Error "Firefox is not installed. Install it first, for example with: winget install Mozilla.Firefox"
}

New-Item -ItemType Directory -Force -Path (Join-Path $profileDir 'extensions'), (Join-Path $profileDir 'chrome') | Out-Null

# Add-ons are copied in once; after that Firefox keeps them updated itself.
foreach ($line in Get-Content (Join-Path $share 'addons.tsv')) {
    if (-not $line -or $line.StartsWith('#')) { continue }
    $name, $guid, $url, $sha256 = $line -split "`t"
    $target = Join-Path $profileDir "extensions\$guid.xpi"
    if (Test-Path -LiteralPath $target) { continue }

    # A release archive ships verified copies; a checkout downloads them.
    $bundled = Join-Path $share "addons\$guid.xpi"
    if (Test-Path -LiteralPath $bundled) {
        Copy-Item -LiteralPath $bundled -Destination $target
        continue
    }

    Write-Host "Downloading $name..."
    $tmp = "$target.download"
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $tmp
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $tmp).Hash.ToLower()
    if ($actual -ne $sha256) {
        Remove-Item -LiteralPath $tmp
        Write-Error "$name did not match its checksum."
    }
    Move-Item -LiteralPath $tmp -Destination $target
}

Copy-Item (Join-Path $share 'user.js') (Join-Path $profileDir 'user.js') -Force
$css = (Get-Content -Raw (Join-Path $share 'userChrome.css')).Replace('@ACCENT@', '#FFD60A')
Write-Utf8 (Join-Path $profileDir 'chrome\userChrome.css') $css

$icon = Join-Path $root 'yukitube.ico'
Copy-Item (Join-Path $here 'yukitube.ico') $icon -Force

# The shortcut starts Firefox straight on YukiTube's own profile, so no
# console window flashes up.
$shell = New-Object -ComObject WScript.Shell
$places = @([Environment]::GetFolderPath('Programs'))
if ($Desktop) { $places += [Environment]::GetFolderPath('Desktop') }
foreach ($place in $places) {
    $link = $shell.CreateShortcut((Join-Path $place 'YukiTube.lnk'))
    $link.TargetPath = $firefox
    $link.Arguments = "-profile `"$profileDir`" https://www.youtube.com/"
    $link.WorkingDirectory = Split-Path -Parent $firefox
    $link.IconLocation = "$icon,0"
    $link.Description = 'YouTube in its own window, without ads'
    $link.Save()
}

Write-Host "YukiTube is installed. Open it from the Start menu."
