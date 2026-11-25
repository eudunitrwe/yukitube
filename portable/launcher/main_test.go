package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestResolve(t *testing.T) {
	cases := map[string]string{
		"":                                       "",
		"https://youtu.be/abc":                   "https://youtu.be/abc",
		"www.youtube.com/watch?v=x":              "https://www.youtube.com/watch?v=x",
		"muzică de studiu":                       "https://www.youtube.com/results?search_query=muzic%C4%83+de+studiu",
		"https://evil.com/youtube.com":           "https://www.youtube.com/results?search_query=https%3A%2F%2Fevil.com%2Fyoutube.com",
		"http://127.0.0.1:8975/yukitube.user.js": "http://127.0.0.1:8975/yukitube.user.js",
		"https://accounts.google.com/ServiceLogin?service=youtube": "https://accounts.google.com/ServiceLogin?service=youtube",
		"http://accounts.google.com/x":                             "https://www.youtube.com/results?search_query=http%3A%2F%2Faccounts.google.com%2Fx",
		"http://127.0.0.1:8976/x":                                  "https://www.youtube.com/results?search_query=http%3A%2F%2F127.0.0.1%3A8976%2Fx",
	}
	for input, want := range cases {
		if got := resolve(input); got != want {
			t.Errorf("resolve(%q) = %q, want %q", input, got, want)
		}
	}
}

func TestMessages(t *testing.T) {
	for key, m := range messages {
		for _, lang := range []string{"en", "ro", "ru"} {
			if m[lang] == "" {
				t.Errorf("message %q has no %s text", key, lang)
			}
		}
	}
	t.Setenv("YUKITUBE_LANG", "ru")
	if got := msg("firefox_failed", "x").Error(); got != "Firefox не запустился: x" {
		t.Errorf("msg in ru = %q", got)
	}
	t.Setenv("YUKITUBE_LANG", "xx")
	if got := msg("firefox_failed", "x").Error(); got != "Firefox did not start: x" {
		t.Errorf("msg fallback = %q", got)
	}
}

func TestDataDir(t *testing.T) {
	root := t.TempDir()
	if got := dataDir(root); got != filepath.Join(root, "Data") {
		t.Errorf("portable dataDir = %q", got)
	}
	os.MkdirAll(filepath.Join(root, "App"), 0o755)
	os.WriteFile(filepath.Join(root, "App", "installed"), nil, 0o644)
	t.Setenv("LOCALAPPDATA", "/local")
	if got := dataDir(root); got != filepath.Join("/local", "YukiTube") {
		t.Errorf("installed dataDir = %q", got)
	}
}
