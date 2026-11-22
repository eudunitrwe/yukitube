//go:build !windows

package main

import (
	"fmt"
	"os"
)

// Built for other systems only so the launcher can be tested there.
const firefoxName = "firefox"

func showError(message string) {
	fmt.Fprintln(os.Stderr, "yukitube:", message)
}
