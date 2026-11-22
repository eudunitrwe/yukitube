package main

import "testing"

func TestResolve(t *testing.T) {
	cases := map[string]string{
		"":                                       "",
		"https://youtu.be/abc":                   "https://youtu.be/abc",
		"www.youtube.com/watch?v=x":              "https://www.youtube.com/watch?v=x",
		"muzică de studiu":                       "https://www.youtube.com/results?search_query=muzic%C4%83+de+studiu",
		"https://evil.com/youtube.com":           "https://www.youtube.com/results?search_query=https%3A%2F%2Fevil.com%2Fyoutube.com",
		"http://127.0.0.1:8975/yukitube.user.js": "http://127.0.0.1:8975/yukitube.user.js",
		"http://127.0.0.1:8976/x":                "https://www.youtube.com/results?search_query=http%3A%2F%2F127.0.0.1%3A8976%2Fx",
	}
	for input, want := range cases {
		if got := resolve(input); got != want {
			t.Errorf("resolve(%q) = %q, want %q", input, got, want)
		}
	}
}
