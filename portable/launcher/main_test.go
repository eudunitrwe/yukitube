package main

import "testing"

func TestResolve(t *testing.T) {
	cases := map[string]string{
		"":                             "",
		"https://youtu.be/abc":         "https://youtu.be/abc",
		"www.youtube.com/watch?v=x":    "https://www.youtube.com/watch?v=x",
		"muzică de studiu":             "https://www.youtube.com/results?search_query=muzic%C4%83+de+studiu",
		"https://evil.com/youtube.com": "https://www.youtube.com/results?search_query=https%3A%2F%2Fevil.com%2Fyoutube.com",
	}
	for input, want := range cases {
		if got := resolve(input); got != want {
			t.Errorf("resolve(%q) = %q, want %q", input, got, want)
		}
	}
}
