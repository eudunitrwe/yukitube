# Instalare YukiTube 0.4.7 pe Linux

YukiTube e un player YouTube: folosești doar telecomanda YukiTube, iar YouTube cântă într-un Firefox ascuns, în spatele ei. Funcționează pe Linux 64-bit (x86_64) cu glibc 2.34 sau mai nou (Arch Linux, Ubuntu 22.04+, Debian 12+, Fedora 35+).

## Ce îți trebuie

- **Firefox** (Arch Linux: `sudo pacman -S firefox`; Debian/Ubuntu: `sudo apt install firefox`; Fedora: `sudo dnf install firefox`)
- `curl` și `jq` (de obicei sunt deja instalate; altfel: `sudo pacman -S curl jq` / `sudo apt install curl jq`)

## Alege o variantă de instalare

Folosește **doar una** dintre ele, altfel YukiTube apare de două ori în launcher.

### Varianta A: Arch Linux (pachet de sistem, recomandat)

Descarcă `yukitube-0.4.7-1-any.pkg.tar.zst` (separat, de pe pagina release-ului; e mic, pentru că folosește Python-ul și PySide6 din sistem), apoi:

```sh
sudo pacman -U yukitube-0.4.7-1-any.pkg.tar.zst
```

Pacman instalează și dependențele (Firefox, curl, jq, Python, PySide6). Dezinstalare: `sudo pacman -R yukitube`.

### Varianta B: orice distribuție, fără sudo (doar pentru utilizatorul tău)

În folderul acesta:

```sh
./install.sh
```

Pune fișierele în `~/.local/bin` și `~/.local/share` (telecomanda e inclusă gata compilată, nu ai nevoie de Python). Dezinstalare: `./install.sh --uninstall`.

## Prima pornire

1. Caută „YukiTube” în launcher și pornește-l. Se deschide doar telecomanda. Prima dată scrie câteva secunde „Preparing YukiTube…”: își pregătește singur profilul și puntea, fără să-ți ceară nimic. Telecomanda pornește în engleză; pentru română: meniul ⋮ → **Language / Limba** → **Română**.
2. Caută ceva cu 🔍 și apasă pe un rezultat. Punctul de lângă logo e **verde** când YouTube e conectat.
3. Opțional: apasă **butonul de cont** (👤) ca să te autentifici cu contul Google. Se deschide fereastra YouTube; după autentificare, închide-o.

## Dacă ceva nu merge

- **„Firefox is not installed”**: instalează Firefox (vezi sus) și încearcă din nou.
- **Punctul nu se face verde**: închide YukiTube (⋮ → Quit / Ieșire) și pornește-l din nou; pregătirea se reia singură. Dacă tot nu merge: ⋮ → „Conectează YukiTube (instalează puntea)”, apasă **Install** în pagina Violentmonkey, apoi `F5` în YouTube.
- **Nu apare telecomanda**: uită-te în `~/.local/state/yukitube/remote.log`. Dacă scrie că portul 8975 e ocupat, o altă copie YukiTube rulează deja.
- **Eroare despre `GLIBC`** (varianta B, distribuții vechi): distribuția e prea veche pentru telecomanda compilată; actualizează distribuția.
- **Nu apare în launcher după varianta B**: deloghează-te și loghează-te înapoi, sau pornește direct cu `~/.local/bin/yukitube`.
