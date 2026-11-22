// Command YukiTube is the portable Windows launcher. It keeps a Firefox
// profile in Data\ beside itself, puts the bundled add-ons and settings in it,
// starts the YukiTube remote from App\Remote, and starts the Firefox in
// App\Firefox on the profile. Nothing is installed, and nothing outside the
// folder is needed.
//
//	YukiTube.exe                 open YouTube (and the remote)
//	YukiTube.exe <link|words>    open a link or search YouTube
//	YukiTube.exe --remote        open only the remote
package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
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
		return fmt.Errorf("Firefox lipsește din %s.\n\nDezarhivează din nou toată arhiva YukiTube, apoi pornește YukiTube.exe din folderul dezarhivat.", filepath.Dir(firefox))
	}
	share := filepath.Join(app, "share")
	profile := filepath.Join(root, "Data", "profile")

	for _, dir := range []string{filepath.Join(profile, "extensions"), filepath.Join(profile, "chrome")} {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return fmt.Errorf("YukiTube nu poate scrie în %s.\n\nMută folderul YukiTube într-un loc unde ai drept de scriere (de exemplu Documente sau un stick USB).\n\n%v", root, err)
		}
	}
	if err := installAddons(share, filepath.Join(profile, "extensions")); err != nil {
		return err
	}
	if err := copyFile(filepath.Join(share, "user.js"), filepath.Join(profile, "user.js")); err != nil {
		return fmt.Errorf("Setările nu au putut fi copiate: %v", err)
	}
	// The retrowave look: the window (userChrome) and YouTube itself
	// (userContent).
	for _, name := range []string{"userChrome.css", "userContent.css"} {
		if err := copyFile(filepath.Join(share, name), filepath.Join(profile, "chrome", name)); err != nil {
			return fmt.Errorf("Lipsește %s: %v", filepath.Join(share, name), err)
		}
	}

	// The remote talks to YouTube through a userscript in Violentmonkey.
	// Once, on the first launch, the remote offers it and Violentmonkey asks
	// to install it; the marker records that. A missing remote is not a
	// reason to keep YouTube from opening.
	if os.Getenv("YUKITUBE_REMOTE") != "0" {
		startRemote(exe, remote, "--bridge-marker", filepath.Join(profile, ".yukitube-bridge-offered"))
	}

	// A second launch reaches the running window through Firefox's own
	// per-profile remoting, so YukiTube never opens twice on one profile.
	argv := []string{"-profile", profile}
	argv = append(argv, strings.Fields(os.Getenv("YUKITUBE_FIREFOX_ARGS"))...)
	if target := resolve(strings.Join(args, " ")); target != "" {
		argv = append(argv, target)
	}
	cmd := exec.Command(firefox, argv...)
	cmd.Dir = filepath.Dir(firefox)
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("Firefox nu a pornit: %v", err)
	}
	return cmd.Process.Release()
}

func remoteRunning() bool {
	client := http.Client{Timeout: time.Second}
	resp, err := client.Get("http://127.0.0.1:8975/nt/ping")
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1024))
	return strings.Contains(string(body), `"yukitube-remote"`)
}

// Starts the remote detached, unless it already runs. YUKITUBE_OPEN makes
// the links it opens come back here, into the YukiTube window.
func startRemote(exe, remote string, extra ...string) error {
	python := filepath.Join(remote, "runtime", pythonName)
	if _, err := os.Stat(python); err != nil {
		return fmt.Errorf("Telecomanda YukiTube lipsește din %s.\n\nDezarhivează din nou toată arhiva YukiTube.", remote)
	}
	if remoteRunning() {
		return nil
	}
	argv := append([]string{filepath.Join(remote, "app", "yukitube_remote.py"), "--quiet-if-running"}, extra...)
	cmd := exec.Command(python, argv...)
	cmd.Dir = remote
	// YUKITUBE_FIREFOX lets the remote find this Firefox's window to dock to.
	firefox := filepath.Join(filepath.Dir(exe), "App", "Firefox", firefoxName)
	cmd.Env = append(os.Environ(), "YUKITUBE_OPEN="+exe, "YUKITUBE_FIREFOX="+firefox)
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("Telecomanda YukiTube nu a pornit: %v", err)
	}
	return cmd.Process.Release()
}

// Add-ons are copied in once, after checking them against addons.tsv;
// after that Firefox keeps them updated itself.
func installAddons(share, extensions string) error {
	list, err := os.Open(filepath.Join(share, "addons.tsv"))
	if err != nil {
		return fmt.Errorf("Lipsește lista de extensii: %v", err)
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
			return fmt.Errorf("Lipsește extensia %s: %v", name, err)
		} else if got != sum {
			return fmt.Errorf("Extensia %s este coruptă (checksum greșit). Dezarhivează din nou YukiTube.", name)
		}
		if err := copyFile(source, target); err != nil {
			return fmt.Errorf("Extensia %s nu a putut fi copiată: %v", name, err)
		}
	}
	return scanner.Err()
}

var youtubeLink = regexp.MustCompile(`(?i)^(https?://)?([a-z0-9-]+\.)*(youtube\.com|youtu\.be)(/|$)`)

// A YouTube link, or the remote's own address (the bridge userscript it
// offers), opens as is; anything else is a search.
func resolve(input string) string {
	input = strings.TrimSpace(input)
	switch {
	case input == "":
		return ""
	case strings.HasPrefix(input, "http://127.0.0.1:8975/"):
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
