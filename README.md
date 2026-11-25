# YukiTube

**🇬🇧 A small YouTube player with skins (retrowave neon, or a classic 90s look) — no ads, no "Video paused. Continue watching?". YouTube plays in a hidden Firefox behind it. For Linux and Windows 10/11.**

**🇷🇴 Un player YouTube mic, cu skin-uri (retrowave neon sau un look clasic din anii ’90) — fără reclame, fără „Continui vizionarea?”. YouTube cântă într-un Firefox ascuns, în spatele lui. Pentru Linux și Windows 10/11.**

Made by **[eudunitrwe](https://github.com/eudunitrwe)** with the help of **[Claude Code](https://claude.com/claude-code)**.
Făcut de **[eudunitrwe](https://github.com/eudunitrwe)** cu ajutorul **[Claude Code](https://claude.com/claude-code)**.

### ⬇️ [Download / Descarcă (Releases)](https://github.com/eudunitrwe/yukitube/releases/latest)

| | File / Fișier |
| --- | --- |
| 🐧 Arch Linux | `yukitube-<version>-1-any.pkg.tar.zst` (small, uses the system's Python/PySide6) |
| 🐧 Linux (x86_64, any distro) | `yukitube-<version>-linux-x86_64.tar.xz` |
| 🪟 Windows 10/11 (x64, portable) | `yukitube-<version>-windows-x64.zip` |

---

## 🇬🇧 English

### What it does

YukiTube is a YouTube player: you use only the **YukiTube remote** (search, play, volume, account), and YouTube plays in a hidden Firefox behind it, on a profile of its own (your login, history and extensions stay apart from your normal Firefox). The YouTube window (no tab bar, dark neon purple/pink/cyan theme) appears only when you ask for it. It comes with three add-ons preinstalled from addons.mozilla.org:

- **uBlock Origin** blocks ads, including YouTube video ads.
- **YouTube NonStop** automatically dismisses "Continue watching?".
- **Violentmonkey** runs the "YukiTube Bridge" userscript that lets the **YukiTube remote** (play/pause, search, volume, open videos) talk to the YouTube window.

### Install on Linux

Needs Firefox, `curl` and `jq` (x86_64, glibc 2.34+: Arch Linux, Ubuntu 22.04+, Debian 12+, Fedora 35+).

```sh
# Option A — Arch Linux (system package, recommended):
sudo pacman -U yukitube-<version>-1-any.pkg.tar.zst      # uninstall: sudo pacman -R yukitube

# Option B — any distro, no sudo (installs to ~/.local):
tar -xJf yukitube-<version>-linux-x86_64.tar.xz
cd yukitube-<version>-linux-x86_64
./install.sh                                            # uninstall: ./install.sh --uninstall
```

Use only one option. Then launch **YukiTube** from your app launcher or run `yukitube`.

### Install on Windows 10/11

Nothing to install — Firefox and the remote are inside the archive, no admin rights needed.

1. Right-click `yukitube-<version>-windows-x64.zip` → **Extract All…** (e.g. to Documents, Desktop or a USB stick — not `C:\Program Files`).
2. Optional: double-click **`Creeaza-scurtaturi.cmd`** in the extracted `YukiTube` folder to add Start menu and Desktop shortcuts.
3. Double-click **`YukiTube.exe`**. If SmartScreen says "Windows protected your PC", click **More info → Run anyway** (first run only).

To uninstall: run `Sterge-scurtaturi.cmd`, then delete the `YukiTube` folder.

### First run (both systems)

Only the remote opens; nothing to click. The very first launch takes a few seconds longer ("Pregătesc YukiTube…") while YukiTube sets itself up. Search with 🔍 (or `Ctrl+F`) and click a result to play it. To sign in to YouTube, click the **account button** (👤): the YouTube window opens on Google's sign-in page; close it when you're done. The ↗ button (or menu ⋮) shows or hides the YouTube window. Drag the remote's edges to resize it. Closing the remote stops YouTube too.

Full step-by-step instructions (in Romanian) are inside each archive: `INSTALARE.md` (Linux) / `INSTALARE.txt` (Windows).

---

## 🇷🇴 Română

### Ce face

YukiTube e un player YouTube: folosești doar **telecomanda YukiTube** (căutare, redare, volum, cont), iar YouTube cântă într-un Firefox ascuns, în spatele ei, pe un profil separat (autentificarea, istoricul și extensiile nu se amestecă cu Firefox-ul tău obișnuit). Fereastra YouTube (fără bara de taburi, culori neon mov/roz/cyan) apare doar când o ceri. Vine cu trei add-on-uri instalate din start, de pe addons.mozilla.org:

- **uBlock Origin** blochează reclamele, inclusiv pe cele video de pe YouTube.
- **YouTube NonStop** închide singur dialogul „Continui vizionarea?”.
- **Violentmonkey** rulează scriptul „YukiTube Bridge”, prin care **telecomanda YukiTube** (pauză/redare, căutare, volum, deschis videoclipuri) vorbește cu fereastra YouTube.

### Instalare pe Linux

Ai nevoie de Firefox, `curl` și `jq` (x86_64, glibc 2.34+: Arch Linux, Ubuntu 22.04+, Debian 12+, Fedora 35+).

```sh
# Varianta A — Arch Linux (pachet de sistem, recomandat):
sudo pacman -U yukitube-<versiune>-1-any.pkg.tar.zst     # dezinstalare: sudo pacman -R yukitube

# Varianta B — orice distribuție, fără sudo (în ~/.local):
tar -xJf yukitube-<versiune>-linux-x86_64.tar.xz
cd yukitube-<versiune>-linux-x86_64
./install.sh                                            # dezinstalare: ./install.sh --uninstall
```

Folosește doar una dintre variante. Apoi pornește **YukiTube** din launcher sau cu `yukitube` din terminal.

### Instalare pe Windows 10/11

Nu instalezi nimic: Firefox și telecomanda sunt în arhivă, nu ai nevoie de drepturi de administrator.

1. Click dreapta pe `yukitube-<versiune>-windows-x64.zip` → **Extract All… (Extrage tot)**, de exemplu în Documente, pe Desktop sau pe un stick USB (nu în `C:\Program Files`).
2. Opțional: dublu-click pe **`Creeaza-scurtaturi.cmd`** în folderul `YukiTube` dezarhivat, pentru scurtături în meniul Start și pe Desktop.
3. Dublu-click pe **`YukiTube.exe`**. Dacă SmartScreen afișează „Windows protected your PC”, apasă **More info → Run anyway** (doar la prima pornire).

Dezinstalare: rulează `Sterge-scurtaturi.cmd`, apoi șterge folderul `YukiTube`.

### Prima pornire (ambele sisteme)

Se deschide doar telecomanda; nu trebuie apăsat nimic. Prima pornire durează câteva secunde în plus („Pregătesc YukiTube…”), cât YukiTube se pregătește singur. Caută cu 🔍 (sau `Ctrl+F`) și apasă pe un rezultat ca să-l redai. Ca să te autentifici în YouTube, apasă **butonul de cont** (👤): se deschide fereastra YouTube la autentificarea Google; închide-o când ai terminat. Butonul ↗ (sau meniul ⋮) arată sau ascunde fereastra YouTube. Telecomanda se redimensionează trăgând de margini. Când închizi telecomanda, se oprește și YouTube.

Instrucțiunile complete, pas cu pas, sunt în fiecare arhivă: `INSTALARE.md` (Linux) / `INSTALARE.txt` (Windows).

---

## Detalii tehnice (pentru dezvoltatori)

YukiTube rulează Firefox pe un profil separat (autentificarea, istoricul și extensiile nu se amestecă cu Firefox-ul tău obișnuit), fără bara de taburi, cu trei add-on-uri instalate din start:

- **uBlock Origin** (GPL-3.0, Raymond Hill): blochează reclamele, inclusiv pe cele video de pe YouTube.
- **YouTube NonStop** (MIT, Nikos Ioannou): închide singur dialogul „Continui vizionarea?”.
- **Violentmonkey** (MIT): rulează userscript-ul „YukiTube Bridge”, puntea dintre tab-ul YouTube și telecomandă.

Toate sunt versiunile semnate de pe addons.mozilla.org, verificate cu SHA-256 la instalare. După aceea, Firefox le actualizează singur.

### Cum lucrează împreună

```
yukitube / YukiTube.exe
 ├─ pregătește profilul Firefox (add-on-uri, user.js, userChrome.css, userContent.css)
 └─ pornește telecomanda cu --firefox <exe> --profile <profil>
     (dacă rulează deja, îi trimite link-ul sau căutarea: POST /yt/open)

telecomanda (remote/app, Python + PySide6)
 ├─ pornește Firefox headless pe profil (firefox_host.py)
 └─ 127.0.0.1:8975 ──  YukiTube Bridge (userscript în Violentmonkey)
      GET  /yt/ping            lansatorul vede dacă telecomanda rulează
      GET  /yukitube.user.js   Violentmonkey actualizează puntea de aici
      POST /yt/up              puntea trimite starea și primește comenzi (GM_xmlhttpRequest)
      POST /yt/open            o a doua lansare: link sau căutare
```

Puntea își trimite versiunea (`bridge`) la fiecare mesaj; telecomanda nu dă comenzi punților fără versiune. Cererile HTTP cer antetul `X-YukiTube`, ca paginile web să nu le poată trimite.

De ce userscript și nu extensia din `remote/browser/extension`: Firefox-ul obișnuit refuză extensiile nesemnate, iar puntea trebuie să ruleze în Firefox-ul lui YukiTube. Violentmonkey e semnat pe AMO, așa că totul merge pe un Firefox normal, fără setări de dezvoltator. Lansatorul pornește doar telecomanda, cu `--firefox <exe> --profile <profil>`; telecomanda pornește Firefox **headless** pe profil (`remote/app/firefox_host.py`) și îl repornește cu fereastră doar când trebuie arătată (autentificare, „Arată fereastra YouTube”), apoi înapoi headless când fereastra e închisă. O a doua lansare (`yukitube <link|cuvinte>`) îi trimite telecomenzii care rulează deja link-ul sau căutarea. La prima pornire, și când puntea are o versiune nouă, telecomanda pregătește întâi profilul (`remote/app/provision.py`), într-un fir separat: pornește Firefox **headless** pe profil, cu Marionette (`--marionette`, portul ales de Firefox prin `marionette.port = 0` din `user.js`), deschide pagina de opțiuni a Violentmonkey și îi trimite userscript-ul prin comanda lui internă `ParseScript` (aceeași pe care o folosește butonul „Install”), șterge punțile rămase de la versiuni mai vechi, apoi închide Firefox. Nu apare nicio pagină de confirmare. Un marcaj în profil (`.yukitube-bridge-installed`, cu versiunea punții) face ca asta să se întâmple o singură dată pe versiune; dacă nu a reușit (jurnal: `~/.local/state/yukitube/remote.log`), se reîncearcă la următoarea pornire. Din meniul telecomenzii (⋮ → „Conectează YukiTube”) se poate instala și manual, prin pagina Violentmonkey.

În Firefox, Violentmonkey rulează puntea izolată de pagină, iar YouTube ignoră `video.play()`/`pause()` și click-urile simulate. De aceea puntea folosește API-ul player-ului YouTube prin `unsafeWindow`, deschide videoclipurile prin navigarea internă YouTube (`yt-navigate`, fără reîncărcare) și își păstrează identificatorul tab-ului în `sessionStorage`. YouTube NonStop amână orice pauză care nu urmează unui click sau unei taste în pagină, așa că o pauză venită de la telecomandă e terminată cu pauza originală pe care NonStop o păstrează (`yns_pause`). `user.js` permite redarea automată, ca un videoclip deschis din telecomandă să pornească singur.

Link-urile pe care le deschide telecomanda (rezultatele căutării, „Deschide YouTube”) trec prin lansator, deci ajung în fereastra YukiTube, nu în browserul implicit.

Extensia `remote/browser/extension` (MV3) a rămas pentru cine vrea să controleze cu telecomanda un Chrome/Edge/Brave obișnuit.

### Arch Linux

```sh
bin/install
```

Construiește pachetul `yukitube` și îl instalează cu `makepkg -fsi` (instalează și `pyside6`). Aplicația apare apoi în launcher (`Super + Space`). Din terminal:

```sh
yukitube                                   # YouTube + telecomanda
yukitube https://youtu.be/dQw4w9WgXcQ      # un link
yukitube muzică de studiu                  # o căutare
yukitube --remote                          # doar telecomanda
YUKITUBE_REMOTE=0 yukitube                 # fără telecomandă
```

Fereastra (`share/userChrome.css`) și YouTube-ul din ea (`share/userContent.css`) poartă culorile telecomenzii: mov închis, roz și cyan neon. Profilul stă în `~/.local/share/yukitube/profile`, jurnalul telecomenzii în `~/.local/state/yukitube/remote.log`.

Din checkout, fără instalare: `bin/yukitube` (telecomanda pornește din `remote/app` cu `python3`, care are nevoie de PySide6).

### Scurtături

| Tastă | Ce face |
| --- | --- |
| `Alt+←` / `Alt+→` | Înapoi / înainte |
| `Ctrl+L` | Bara de adrese: lipește un link sau caută |
| `Ctrl+R` / `F5` | Reîncarcă |
| `Ctrl+W` | Închide pagina curentă |
| `F11` | Ecran complet |
| `Ctrl+=` / `Ctrl+-` / `Ctrl+0` | Zoom |
| `Ctrl+Q` | Ieșire (Linux) |
| `Space`, `K`, `J`, `L`, `F`, `M` | Playerul YouTube: pauză, înapoi/înainte 10 s, ecran complet, sunet |
| `?` | Toate scurtăturile YouTube |

Scurtăturile telecomenzii sunt în README-urile din arhive (`dist-docs/`).

### Structura

- `bin/yukitube`: lansatorul pentru Linux. `portable/launcher/`: `YukiTube.exe` pentru Windows (Go), aceeași logică.
- `share/addons.tsv`: add-on-urile, cu link-ul și SHA-256 pentru fiecare.
- `share/user.js`: setările profilului (pagina de start, fără taburi, temă întunecată, add-on-urile activate fără întrebări). Se rescrie la fiecare pornire; restul setărilor le poți schimba liber.
- `share/userChrome.css`: ascunde bara de taburi și dă ferestrei culorile retrowave. `share/userContent.css`: aceleași culori pe YouTube (doar variabilele de culoare ale YouTube și câteva accente, nu layout-ul).
- `remote/tools/make_icons.py`: generează toate iconițele din logo, `remote/app/assets/logo.svg` (pisica Yuki în fața soarelui retrowave): PNG/ICO pentru telecomandă, extensie și Windows; pentru Linux, SVG-ul însuși.
- `remote/app/`: telecomanda (`yukitube_remote.py` interfața, `firefox_host.py` Firefox-ul ascuns, `provision.py` pregătirea profilului, `hyprland.py` fereastra plutitoare pe Hyprland, `logo.py` logo-ul, `wsserver.py` serverul local, `ytsearch.py` căutarea fără cheie API).
- `remote/browser/`: puntea (`agent-core.js` rulează în tab-ul YouTube; `userscript-*.js` o împachetează ca userscript; `extension/` ca extensie MV3).
- `windows/`: iconița și `shortcuts.ps1` (scurtăturile din meniul Start pentru varianta portabilă).
- `dist-docs/`: README-urile și instrucțiunile de instalare din arhive.

Ca să actualizezi versiunile fixate ale add-on-urilor, schimbă link-ul și hash-ul în `share/addons.tsv` și în `pkgbuild/PKGBUILD` (API-ul AMO le dă: `https://addons.mozilla.org/api/v5/addons/addon/violentmonkey/`).

### Arhive de distribuție

```sh
bin/dist
```

Creează în `dist/` fișierele release-ului, plus `yukitube-<versiune>-SHA256SUMS`:

- `yukitube-<versiune>-1-any.pkg.tar.zst`: pachetul Arch (telecomanda din surse, pe Python-ul și PySide6-ul sistemului).
- `yukitube-<versiune>-linux-x86_64.tar.xz`: lansatorul, telecomanda compilată cu PyInstaller, `install.sh` pentru orice distribuție (fără sudo), `README.md`, `INSTALARE.md`.
- `yukitube-<versiune>-windows-x64.zip`: varianta portabilă, folderul `YukiTube\` cu `YukiTube.exe`, un Firefox pentru Windows în `App\Firefox` (fără actualizator, crash reporter, AI local și WebGPU), telecomanda în `App\Remote` (Python embeddable + PySide6), extensiile, `Creeaza-scurtaturi.cmd`, `README.txt`, `INSTALARE.txt`. Nu instalează nimic; profilul stă în `Data\`, lângă exe.

Versiunile fixate (Firefox, Python, PySide6, Go) și hash-urile lor sunt la începutul lui `bin/dist`. E nevoie de `uv`, `mise` (pentru Go), `makepkg`, `zip`, `bsdtar`, `curl` și `binutils`. Descărcările stau în `~/.cache/yukitube`.
