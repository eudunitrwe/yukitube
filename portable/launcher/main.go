// Command YukiTube is the portable Windows launcher. It keeps a Firefox
// profile in Data\ beside itself, puts the bundled add-ons and settings in it,
// and starts the YukiTube remote from App\Remote, which runs YouTube in the
// Firefox in App\Firefox on the profile, hidden (headless). Nothing is
// installed, and nothing outside the folder is needed.
//
//	YukiTube.exe                 open the remote (YouTube runs hidden behind it)
//	YukiTube.exe <link|words>    play a link or search YouTube in the remote
//	YukiTube.exe --remote        open only the remote
package main

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

func main() {
	exe, err := os.Executable()
	if err == nil {
		exe, err = filepath.EvalSymlinks(exe)
	}
	if err == nil {
		err = run(exe, os.Args[1:])
	}
	if err != nil {
		showError(err.Error())
		os.Exit(1)
	}
}

func run(exe string, args []string) error {
	root := filepath.Dir(exe)
	app := filepath.Join(root, "App")
	remote := filepath.Join(app, "Remote")
	if len(args) == 1 && args[0] == "--remote" {
		return startRemote(exe, remote)
	}

	firefox := filepath.Join(app, "Firefox", firefoxName)
	if _, err := os.Stat(firefox); err != nil {
		return msg("firefox_missing", filepath.Dir(firefox))
	}
	share := filepath.Join(app, "share")
	profile := filepath.Join(dataDir(root), "profile")

	for _, dir := range []string{filepath.Join(profile, "extensions"), filepath.Join(profile, "chrome")} {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return msg("not_writable", filepath.Dir(dir), err)
		}
	}
	if err := installAddons(share, filepath.Join(profile, "extensions")); err != nil {
		return err
	}
	if err := copyFile(filepath.Join(share, "user.js"), filepath.Join(profile, "user.js")); err != nil {
		return msg("settings_copy", err)
	}
	// The retrowave look: the window (userChrome) and YouTube itself
	// (userContent).
	for _, name := range []string{"userChrome.css", "userContent.css"} {
		if err := copyFile(filepath.Join(share, name), filepath.Join(profile, "chrome", name)); err != nil {
			return msg("missing_file", filepath.Join(share, name), err)
		}
	}

	target := resolve(strings.Join(args, " "))

	// The remote runs YouTube in this Firefox, hidden; on the first launch
	// it first puts the bridge userscript into Violentmonkey, out of sight.
	// A remote that already runs takes the link or search and comes to the
	// front.
	if os.Getenv("YUKITUBE_REMOTE") != "0" {
		if remoteRunning() {
			if forward(target) {
				return nil
			}
		} else if startRemote(exe, remote, "--firefox", firefox, "--profile", profile, target) == nil {
			return nil
		}
	}

	// Without the remote: the Firefox window alone. A second launch reaches
	// the running window through Firefox's own per-profile remoting.
	argv := []string{"-profile", profile}
	argv = append(argv, strings.Fields(os.Getenv("YUKITUBE_FIREFOX_ARGS"))...)
	if target != "" {
		argv = append(argv, target)
	}
	cmd := exec.Command(firefox, argv...)
	cmd.Dir = filepath.Dir(firefox)
	if err := cmd.Start(); err != nil {
		return msg("firefox_failed", err)
	}
	return cmd.Process.Release()
}

// The remote's address; YUKITUBE_PORT moves it off the default port.
var remoteURL = "http://127.0.0.1:" + remotePort()

func remotePort() string {
	if p := os.Getenv("YUKITUBE_PORT"); p != "" {
		return p
	}
	return "8975"
}

func remoteRunning() bool {
	client := http.Client{Timeout: time.Second}
	resp, err := client.Get(remoteURL + "/yt/ping")
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1024))
	return strings.Contains(string(body), `"yukitube-remote"`)
}

// Hands a link or search ("" just brings it to the front) to the remote
// that already runs.
func forward(target string) bool {
	body, _ := json.Marshal(map[string]string{"arg": target})
	req, err := http.NewRequest("POST", remoteURL+"/yt/open", bytes.NewReader(body))
	if err != nil {
		return false
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-YukiTube", "1")
	client := http.Client{Timeout: 3 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return false
	}
	resp.Body.Close()
	return resp.StatusCode == http.StatusOK
}

// Starts the remote detached, unless it already runs. YUKITUBE_OPEN lets the
// remote, when it runs alone (--remote), open links through this launcher.
func startRemote(exe, remote string, extra ...string) error {
	python := filepath.Join(remote, "runtime", pythonName)
	if _, err := os.Stat(python); err != nil {
		return msg("remote_missing", remote)
	}
	if remoteRunning() {
		return nil
	}
	argv := []string{filepath.Join(remote, "app", "yukitube_remote.py"), "--quiet-if-running"}
	for _, a := range extra {
		if a != "" {
			argv = append(argv, a)
		}
	}
	cmd := exec.Command(python, argv...)
	cmd.Dir = remote
	cmd.Env = append(os.Environ(), "YUKITUBE_OPEN="+exe)
	if err := cmd.Start(); err != nil {
		return msg("remote_failed", err)
	}
	return cmd.Process.Release()
}

// Add-ons are copied in once, after checking them against addons.tsv;
// after that Firefox keeps them updated itself.
func installAddons(share, extensions string) error {
	list, err := os.Open(filepath.Join(share, "addons.tsv"))
	if err != nil {
		return msg("addons_list", err)
	}
	defer list.Close()

	scanner := bufio.NewScanner(list)
	for scanner.Scan() {
		line := strings.TrimRight(scanner.Text(), "\r")
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		fields := strings.Split(line, "\t")
		if len(fields) != 4 {
			continue
		}
		name, guid, sum := fields[0], fields[1], fields[3]
		target := filepath.Join(extensions, guid+".xpi")
		if _, err := os.Stat(target); err == nil {
			continue
		}
		source := filepath.Join(share, "addons", guid+".xpi")
		if got, err := fileSHA256(source); err != nil {
			return msg("addon_missing", name, err)
		} else if got != sum {
			return msg("addon_corrupt", name)
		}
		if err := copyFile(source, target); err != nil {
			return msg("addon_copy", name, err)
		}
	}
	return scanner.Err()
}

// Where the profile lives: Data\ beside YukiTube.exe for the portable
// folder; for an installed YukiTube (App\installed, left by the installer;
// Program Files is not writable) %LOCALAPPDATA%\YukiTube.
func dataDir(root string) string {
	if _, err := os.Stat(filepath.Join(root, "App", "installed")); err == nil {
		if local := os.Getenv("LOCALAPPDATA"); local != "" {
			return filepath.Join(local, "YukiTube")
		}
	}
	return filepath.Join(root, "Data")
}

var youtubeLink = regexp.MustCompile(`(?i)^(https?://)?([a-z0-9-]+\.)*(youtube\.com|youtu\.be)(/|$)`)

// A YouTube link, the remote's own address (the bridge userscript it
// offers), or Google's sign-in pages (the remote's account button) open as
// is; anything else is a search.
func resolve(input string) string {
	input = strings.TrimSpace(input)
	switch {
	case input == "":
		return ""
	case strings.HasPrefix(input, remoteURL+"/"), strings.HasPrefix(input, "https://accounts.google.com/"):
		return input
	case youtubeLink.MatchString(input):
		if strings.HasPrefix(strings.ToLower(input), "http") {
			return input
		}
		return "https://" + input
	default:
		return "https://www.youtube.com/results?search_query=" + url.QueryEscape(input)
	}
}

func fileSHA256(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

// Writes beside the target and renames, so a crash never leaves half a file.
func copyFile(from, to string) error {
	in, err := os.Open(from)
	if err != nil {
		return err
	}
	defer in.Close()
	tmp := to + ".tmp"
	out, err := os.Create(tmp)
	if err != nil {
		return err
	}
	if _, err := io.Copy(out, in); err != nil {
		out.Close()
		os.Remove(tmp)
		return err
	}
	if err := out.Close(); err != nil {
		os.Remove(tmp)
		return err
	}
	return os.Rename(tmp, to)
}
