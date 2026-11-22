package main

import (
	"syscall"
	"unsafe"
)

const (
	firefoxName = "firefox.exe"
	pythonName  = "pythonw.exe"
)

// The launcher is built without a console, so errors go to a message box.
func showError(message string) {
	text, _ := syscall.UTF16PtrFromString(message)
	title, _ := syscall.UTF16PtrFromString("YukiTube")
	const mbOK, mbIconError = 0x0, 0x10
	syscall.NewLazyDLL("user32.dll").NewProc("MessageBoxW").Call(
		0, uintptr(unsafe.Pointer(text)), uintptr(unsafe.Pointer(title)), mbOK|mbIconError)
}
