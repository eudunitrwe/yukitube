# YukiTube

YouTube într-o fereastră proprie de Firefox, fără reclame și fără „Video întrerupt. Continui vizionarea?”.

YukiTube rulează Firefox pe un profil separat (autentificarea, istoricul și extensiile nu se amestecă cu Firefox-ul tău obișnuit), fără bara de taburi, cu două add-on-uri instalate din start:

- **uBlock Origin** (GPL-3.0, Raymond Hill): blochează reclamele, inclusiv pe cele video de pe YouTube.
- **YouTube NonStop** (MIT, Nikos Ioannou): închide singur dialogul „Continui vizionarea?”.

Ambele sunt versiunile semnate de pe addons.mozilla.org, verificate cu SHA-256 la instalare. După aceea, Firefox le actualizează singur.

## Arch Linux

```sh
bin/install
```

Construiește pachetul `yukitube` și îl instalează cu `makepkg -fsi`. Aplicația apare apoi în launcher (`Super + Space`). Din terminal:

```sh
yukitube                                   # YouTube
yukitube https://youtu.be/dQw4w9WgXcQ      # un link
yukitube muzică de studiu                  # o căutare
```

Linia de sub bara de adrese ia culoarea accent a temei curente, la fiecare pornire.

Profilul stă în `~/.local/share/yukitube/profile`.

## Windows 10 / 11

Ai nevoie de Firefox (`winget install Mozilla.Firefox`). Apoi, din folderul proiectului:

- dublu-click pe `windows\install.cmd`, sau
- `powershell -ExecutionPolicy Bypass -File windows\install.ps1 -Desktop` (cu `-Desktop` pune și o scurtătură pe desktop).

YukiTube apare în meniul Start. Profilul stă în `%LOCALAPPDATA%\yukitube\profile`. Dezinstalare: `windows\uninstall.ps1` (adaugă `-RemoveData` ca să ștergi și profilul).

## Scurtături

Sunt cele din Firefox și YouTube:

| Tastă | Ce face |
| --- | --- |
| `Alt+←` / `Alt+→` | Înapoi / înainte |
| `Ctrl+L` | Bara de adrese: lipește un link sau caută |
| `Ctrl+R` / `F5` | Reîncarcă |
| `F11` | Ecran complet |
| `Ctrl+=` / `Ctrl+-` / `Ctrl+0` | Zoom |
| `Ctrl+Q` | Ieșire (Linux) |
| `Space`, `K`, `J`, `L`, `F`, `M` | Playerul YouTube: pauză, înapoi/înainte 10 s, ecran complet, sunet |
| `?` | Toate scurtăturile YouTube |

Butonul uBlock Origin din dreapta barei de adrese deschide panoul lui.

## Cum funcționează

- `share/addons.tsv`: add-on-urile, cu link-ul și SHA-256 pentru fiecare.
- `share/user.js`: setările profilului (pagina de start, fără taburi, temă întunecată, add-on-urile activate fără întrebări). Se rescrie la fiecare pornire; restul setărilor le poți schimba liber.
- `share/userChrome.css`: ascunde bara de taburi și colorează bara de adrese.
- `bin/yukitube`: launcherul pentru Linux. `windows/install.ps1`: același lucru pentru Windows, plus scurtătura din Start.

Ca să actualizezi versiunile fixate ale add-on-urilor, schimbă link-ul și hash-ul în `share/addons.tsv` și în `pkgbuild/PKGBUILD` (API-ul AMO le dă: `https://addons.mozilla.org/api/v5/addons/addon/ublock-origin/`).

## Arhive de distribuție

```sh
bin/dist
```

Creează în `dist/` două arhive separate, fiecare cu add-on-urile incluse (instalarea nu descarcă nimic), un README și instrucțiuni de instalare:

- `yukitube-<versiune>-linux.tar.gz`: pachetul Arch, `install.sh` pentru orice distribuție (fără sudo), `README.md`, `INSTALARE.md`
- `yukitube-<versiune>-windows.zip`: `Instaleaza.cmd` și celelalte fișiere pe care dai dublu-click, `README.txt`, `INSTALARE.txt`

Textele din arhive sunt în `dist-docs/`.

## Windows portabil

```sh
bin/dist-portable
```

Creează `dist/yukitube-<versiune>-windows-portable.zip`: `YukiTube.exe` (launcherul din `portable/launcher/`, scris în Go), un Firefox pentru Windows în `App\Firefox` (versiune fixată și verificată cu SHA-256 în script) și extensiile. Profilul stă în `Data\`, lângă exe, deci nu se instalează nimic, nici măcar Firefox. Textele din arhivă sunt în `dist-docs/windows-portable/`. E nevoie de Go (`mise install go@1.27.4`).
