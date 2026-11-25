package main

import (
	"syscall"
	"unsafe"
)

const (
	firefoxName = "firefox.exe"
	pythonName  = "pythonw.exe"
)

// The language chosen in the YukiTube player, which keeps its settings in
// HKCU\Software\YukiTube\remote (Qt's QSettings); "en" until one is chosen.
func uiLanguage() string {
	key, _ := syscall.UTF16PtrFromString(`Software\YukiTube\remote`)
	name, _ := syscall.UTF16PtrFromString("lang")
	buf := make([]uint16, 16)
	size := uint32(len(buf) * 2)
	const hkeyCurrentUser, rrfRtRegSz = 0x80000001, 0x00000002
	r, _, _ := syscall.NewLazyDLL("advapi32.dll").NewProc("RegGetValueW").Call(
		hkeyCurrentUser, uintptr(unsafe.Pointer(key)), uintptr(unsafe.Pointer(name)), rrfRtRegSz,
		0, uintptr(unsafe.Pointer(&buf[0])), uintptr(unsafe.Pointer(&size)))
	if r != 0 {
		return "en"
	}
	return syscall.UTF16ToString(buf)
}

// The launcher is built without a console, so errors go to a message box.
func showError(message string) {
	text, _ := syscall.UTF16PtrFromString(message)
	title, _ := syscall.UTF16PtrFromString("YukiTube")
	const mbOK, mbIconError = 0x0, 0x10
	syscall.NewLazyDLL("user32.dll").NewProc("MessageBoxW").Call(
		0, uintptr(unsafe.Pointer(text)), uintptr(unsafe.Pointer(title)), mbOK|mbIconError)
}
