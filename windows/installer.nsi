; The YukiTube installer for Windows: puts the portable YukiTube folder in
; C:\Program Files (x86)\YukiTube, with a Desktop and a Start menu shortcut,
; and an entry in Settings > Apps that uninstalls it. The profile (sign-in,
; history) goes to %LOCALAPPDATA%\YukiTube, because Program Files cannot be
; written to; App\installed tells YukiTube.exe so.
;
; Built by bin/dist:
;   makensis -DVERSION=<version> -DSRC=<YukiTube folder> -DOUTFILE=<exe> windows/installer.nsi

Unicode true
SetCompressor /SOLID lzma
SetCompressorDictSize 64

!include "MUI2.nsh"

Name "YukiTube"
OutFile "${OUTFILE}"
; $PROGRAMFILES32 is C:\Program Files (x86) on 64-bit Windows, whatever the
; installer's own bitness.
InstallDir "$PROGRAMFILES32\YukiTube"
RequestExecutionLevel admin
BrandingText "YukiTube ${VERSION}"

VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=1033 "ProductName" "YukiTube"
VIAddVersionKey /LANG=1033 "FileDescription" "YukiTube ${VERSION} Setup"
VIAddVersionKey /LANG=1033 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1033 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=1033 "LegalCopyright" "MIT License, eudunitrwe"

!define MUI_ICON "${SRC}\App\Remote\app\assets\yukitube.ico"
!define MUI_UNICON "${SRC}\App\Remote\app\assets\yukitube.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\YukiTube.exe"
!define MUI_LANGDLL_ALLLANGUAGES

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; English first: the default.
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Romanian"
!insertmacro MUI_LANGUAGE "Russian"

!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\YukiTube"

; YukiTube running from the install folder (the player's Python, its Firefox)
; would keep files locked; it is closed first.
!macro StopYukiTube
  nsExec::Exec `powershell -NoProfile -NonInteractive -Command "Get-Process | Where-Object { $$_.Path -and $$_.Path.StartsWith('$INSTDIR\', [StringComparison]::OrdinalIgnoreCase) } | Stop-Process -Force"`
  Pop $0
  Sleep 1000
!macroend

Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Function un.onInit
  !insertmacro MUI_UNGETLANGUAGE
FunctionEnd

Section "YukiTube"
  !insertmacro StopYukiTube
  ; A previous version's files go first, so nothing stale stays behind.
  RMDir /r "$INSTDIR\App"
  SetOutPath "$INSTDIR"
  File /r /x "Creeaza-scurtaturi.cmd" /x "Sterge-scurtaturi.cmd" /x "INSTALARE.txt" /x "shortcuts.ps1" /x "Data" "${SRC}\*.*"
  FileOpen $0 "$INSTDIR\App\installed" w
  FileWrite $0 "${VERSION}"
  FileClose $0
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  SetShellVarContext all
  CreateShortCut "$DESKTOP\YukiTube.lnk" "$INSTDIR\YukiTube.exe" "" "$INSTDIR\App\Remote\app\assets\yukitube.ico" 0
  CreateShortCut "$SMPROGRAMS\YukiTube.lnk" "$INSTDIR\YukiTube.exe" "" "$INSTDIR\App\Remote\app\assets\yukitube.ico" 0

  WriteRegStr HKLM "${UNINST_KEY}" "DisplayName" "YukiTube"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "${UNINST_KEY}" "Publisher" "eudunitrwe"
  WriteRegStr HKLM "${UNINST_KEY}" "URLInfoAbout" "https://github.com/eudunitrwe/yukitube"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayIcon" "$INSTDIR\App\Remote\app\assets\yukitube.ico"
  WriteRegStr HKLM "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNINST_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "EstimatedSize" 400000
SectionEnd

Section "Uninstall"
  !insertmacro StopYukiTube
  SetShellVarContext all
  Delete "$DESKTOP\YukiTube.lnk"
  Delete "$SMPROGRAMS\YukiTube.lnk"
  ; What the player's settings added for the user: the desktop shortcut and
  ; starting with Windows.
  SetShellVarContext current
  Delete "$DESKTOP\YukiTube.lnk"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "YukiTube"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "${UNINST_KEY}"
  ; The profile in %LOCALAPPDATA%\YukiTube (sign-in, history) stays.
SectionEnd
