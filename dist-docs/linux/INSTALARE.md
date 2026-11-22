# Instalare YukiTube pe Linux

## Ce îți trebuie

- **Firefox** (Arch Linux: `sudo pacman -S firefox`; Debian/Ubuntu: `sudo apt install firefox`; Fedora: `sudo dnf install firefox`)
- `curl` și `jq` (de obicei sunt deja instalate)

## 1. Dezarhivează

```sh
tar -xzf yukitube-0.1.0-linux.tar.gz
cd yukitube-0.1.0-linux
```

## 2. Alege o variantă de instalare

Folosește **doar una** dintre ele, altfel YukiTube apare de două ori în launcher.

### Varianta A: Arch Linux (pachet de sistem, recomandat)

```sh
sudo pacman -U yukitube-0.1.0-1-any.pkg.tar.zst
```

Pacman se ocupă și de dependențe (Firefox, curl, jq). Dezinstalare:

```sh
sudo pacman -R yukitube
```

### Varianta B: orice distribuție, fără sudo (doar pentru utilizatorul tău)

```sh
./install.sh
```

Pune fișierele în `~/.local/bin` și `~/.local/share`. Dezinstalare:

```sh
./install.sh --uninstall
```

## 3. Pornește

Caută „YukiTube” în launcher. La prima pornire, YukiTube își creează profilul și instalează cele două extensii din arhivă, fără să descarce nimic.

## Dacă ceva nu merge

- **„Firefox is not installed”**: instalează Firefox (vezi sus) și încearcă din nou.
- **Nu apare în launcher după varianta B**: deloghează-te și loghează-te înapoi, sau pornește direct cu `~/.local/bin/yukitube`.
- **Extensiile nu apar**: închide YukiTube, șterge `~/.local/share/yukitube/profile/extensions` și pornește din nou.
