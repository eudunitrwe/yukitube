// Command YukiTube is the portable Windows launcher. It keeps a Firefox
// profile in Data\ beside itself, puts the bundled add-ons and settings in it,
// and starts the Firefox in App\Firefox on it. Nothing is installed, and
// nothing outside the folder is needed.
package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
)

func main() {
	exe, err := os.Executable()
	if err == nil {
		exe, err = filepath.EvalSymlinks(exe)
	}
	if err == nil {
		err = run(filepath.Dir(exe), os.Args[1:])
	}
	if err != nil {
		showError(err.Error())
		os.Exit(1)
	}
}

func run(root string, args []string) error {
	app := filepath.Join(root, "App")
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
	css, err := os.ReadFile(filepath.Join(share, "userChrome.css"))
	if err != nil {
		return fmt.Errorf("Lipsește %s: %v", filepath.Join(share, "userChrome.css"), err)
	}
	css = []byte(strings.ReplaceAll(string(css), "@ACCENT@", "#FFD60A"))
	if err := os.WriteFile(filepath.Join(profile, "chrome", "userChrome.css"), css, 0o644); err != nil {
		return err
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

// A YouTube link opens as is; anything else is a search.
func resolve(input string) string {
	input = strings.TrimSpace(input)
	switch {
	case input == "":
		return ""
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
