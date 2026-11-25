# Instalare YukiTube 0.4.2 pe Linux

Arhiva conține YukiTube: fereastra YouTube și telecomanda ei (fostul NeonTube), ca o singură aplicație. Funcționează pe Linux 64-bit (x86_64) cu glibc 2.34 sau mai nou (Arch Linux, Ubuntu 22.04+, Debian 12+, Fedora 35+).

## Ce îți trebuie

- **Firefox** (Arch Linux: `sudo pacman -S firefox`; Debian/Ubuntu: `sudo apt install firefox`; Fedora: `sudo dnf install firefox`)
- `curl` și `jq` (de obicei sunt deja instalate; altfel: `sudo pacman -S curl jq` / `sudo apt install curl jq`)

## Pasul 0: dacă ai avut NeonTube separat

Telecomanda e acum inclusă în YukiTube. Închide vechiul NeonTube (meniul ⋮ → Ieșire) și dezinstalează-l, altfel ocupă portul 8975 și YukiTube nu își poate porni telecomanda:

```sh
rm -rf ~/.local/share/neontube ~/.local/bin/neontube ~/.local/share/applications/neontube.desktop
```

(sau `./uninstall.sh` din folderul vechii arhive NeonTube, dacă îl mai ai).

Setările vechiului NeonTube (`~/.config/NeonTube/`) sunt preluate automat de telecomanda YukiTube la prima pornire.

## Pasul 1: dezarhivează

```sh
tar -xzf yukitube-0.4.2-linux-x86_64.tar.gz
cd yukitube-0.4.2-linux-x86_64
```

## Pasul 2: alege o variantă de instalare

Folosește **doar una** dintre ele, altfel YukiTube apare de două ori în launcher.

### Varianta A: Arch Linux (pachet de sistem, recomandat)

```sh
sudo pacman -U yukitube-0.4.2-1-any.pkg.tar.zst
```

Pacman instalează și dependențele (Firefox, curl, jq, Python, PySide6). Telecomanda rulează pe PySide6-ul sistemului. Dezinstalare:

```sh
sudo pacman -R yukitube
```

### Varianta B: orice distribuție, fără sudo (doar pentru utilizatorul tău)

```sh
./install.sh
```

Pune fișierele în `~/.local/bin` și `~/.local/share` (telecomanda e inclusă gata compilată, nu ai nevoie de Python). Dezinstalare:

```sh
./install.sh --uninstall
```

## Pasul 3: prima pornire

1. Caută „YukiTube” în launcher și pornește-l. Prima dată durează câteva secunde în plus: YukiTube își pregătește singur profilul și puntea, fără să-ți ceară nimic. Se deschide doar telecomanda YukiTube: YouTube cântă într-un Firefox ascuns, în spatele ei.
2. Caută ceva cu 🔍 și apasă pe un rezultat. Punctul de lângă logo-ul telecomenzii e **verde** când YouTube e conectat.
3. Opțional: apasă **butonul de cont** (👤) ca să te autentifici cu contul Google. Se deschide fereastra YouTube; după autentificare, închide-o. Fereastra YouTube o poți arăta oricând cu butonul ↗ sau din meniul ⋮.

Dacă ai avut NeonTube, în Violentmonkey pot rămâne punți vechi („NeonTube Bridge…”). Telecomanda le ignoră, dar le poți șterge din panoul Violentmonkey (iconița lui → ⚙ → Installed scripts → coșul de gunoi).

Dacă punctul nu se face verde: închide YukiTube și pornește-l din nou (pregătirea se reia singură). Dacă tot nu merge: în telecomandă, meniul **⋮ → „Conectează YukiTube (instalează puntea)”**, apasă **Install** în pagina Violentmonkey, apoi reîncarcă YouTube cu `F5`.

## Dacă ceva nu merge

- **„Firefox is not installed”**: instalează Firefox (vezi sus) și încearcă din nou.
- **Nu apare telecomanda**: rulează `yukitube --remote` și uită-te în `~/.local/state/yukitube/remote.log`. Dacă scrie că portul 8975 e ocupat, închide vechiul NeonTube (pasul 0).
- **Telecomanda nu pornește, cu o eroare despre `GLIBC`** (varianta B, distribuții vechi): distribuția e prea veche pentru telecomanda compilată; folosește YouTube-ul fără ea (`YUKITUBE_REMOTE=0 yukitube`) sau actualizează distribuția.
- **Nu apare în launcher după varianta B**: deloghează-te și loghează-te înapoi, sau pornește direct cu `~/.local/bin/yukitube`.
- **Extensiile nu apar**: închide YukiTube, șterge `~/.local/share/yukitube/profile/extensions` și pornește din nou.
