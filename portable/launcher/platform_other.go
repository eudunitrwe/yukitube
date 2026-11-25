//go:build !windows

package main

import (
	"fmt"
	"os"
)

// Built for other systems only so the launcher can be tested there.
const (
	firefoxName = "firefox"
	pythonName  = "python3"
)

func uiLanguage() string {
	if l := os.Getenv("YUKITUBE_LANG"); l != "" {
		return l
	}
	return "en"
}

func showError(message string) {
	fmt.Fprintln(os.Stderr, "yukitube:", message)
}
