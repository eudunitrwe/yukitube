# YukiTube pentru Linux

YouTube într-o fereastră proprie de Firefox, fără reclame și fără „Video întrerupt. Continui vizionarea?”.

YukiTube pornește Firefox pe un profil separat, doar pentru YouTube. Autentificarea, istoricul și extensiile nu se amestecă cu Firefox-ul tău obișnuit. Bara de taburi e ascunsă, ca să arate ca o aplicație. Linia de sub bara de adrese ia culoarea accent a temei curente.

Extensii incluse (versiunile semnate de pe addons.mozilla.org; după instalare, Firefox le actualizează singur):

- **uBlock Origin** 1.77.0 (GPL-3.0, Raymond Hill): blochează reclamele, inclusiv pe cele video de pe YouTube.
- **YouTube NonStop** 0.9.2 (MIT, Nikos Ioannou): închide singur dialogul „Continui vizionarea?”.

Instalarea e descrisă în `INSTALARE.md`.

## Folosire

Din launcher (caută „YukiTube”) sau din terminal:

```sh
yukitube                                  # YouTube
yukitube https://youtu.be/dQw4w9WgXcQ     # un link YouTube
yukitube muzică de studiu                 # o căutare
```

## Scurtături

| Tastă | Ce face |
| --- | --- |
| `Alt+←` / `Alt+→` | Înapoi / înainte |
| `Ctrl+L` | Bara de adrese: lipește un link sau caută |
| `Ctrl+R` / `F5` | Reîncarcă |
| `F11` | Ecran complet |
| `Ctrl+=` / `Ctrl+-` / `Ctrl+0` | Zoom |
| `Ctrl+Q` | Ieșire |
| `Space`, `K`, `J`, `L`, `F`, `M` | Playerul YouTube: pauză, înapoi/înainte 10 s, ecran complet, sunet |
| `?` | Toate scurtăturile YouTube |

Butonul uBlock Origin din dreapta barei de adrese deschide panoul lui.

## Unde stau datele

Profilul (autentificare, istoric, setări uBlock) e în `~/.local/share/yukitube/profile`. Dezinstalarea nu îl șterge; îl ștergi tu dacă vrei să pornești de la zero.

## Licență

YukiTube: MIT (vezi `LICENSE`). Extensiile își păstrează licențele lor.
