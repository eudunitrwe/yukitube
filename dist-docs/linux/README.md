# YukiTube 0.3 pentru Linux

YouTube într-o fereastră proprie de Firefox, fără reclame și fără „Video întrerupt. Continui vizionarea?”, în stil **retrowave**, cu o telecomandă mică și transparentă care controlează YouTube-ul din fereastra YukiTube. (Telecomanda se numea înainte NeonTube.)

YukiTube pornește Firefox pe un profil separat, doar pentru YouTube. Autentificarea, istoricul și extensiile nu se amestecă cu Firefox-ul tău obișnuit. Bara de taburi e ascunsă, ca să arate ca o aplicație. Fereastra și YouTube-ul din ea poartă culorile telecomenzii: mov închis, roz și cyan neon, cu logo-ul soarelui retrowave.

Extensii incluse (versiunile semnate de pe addons.mozilla.org; după instalare, Firefox le actualizează singur):

- **uBlock Origin** 1.77.0 (GPL-3.0, Raymond Hill): blochează reclamele, inclusiv pe cele video de pe YouTube.
- **YouTube NonStop** 0.9.2 (MIT, Nikos Ioannou): închide singur dialogul „Continui vizionarea?”.
- **Violentmonkey** 2.50.0 (MIT): rulează „YukiTube Bridge”, puntea prin care telecomanda vorbește cu YouTube.

**Instalarea e descrisă pas cu pas în `INSTALARE.md`.**

## Folosire

Din launcher (caută „YukiTube”) sau din terminal:

```sh
yukitube                                  # YouTube + telecomanda
yukitube https://youtu.be/dQw4w9WgXcQ     # un link YouTube
yukitube muzică de studiu                 # o căutare
yukitube --remote                         # doar telecomanda
YUKITUBE_REMOTE=0 yukitube                # YouTube fără telecomandă
```

În launcher, click dreapta pe YukiTube (sau acțiunile aplicației) are și „Doar telecomanda”.

## Telecomanda

Pornește odată cu YukiTube și rămâne deschisă și după ce închizi fereastra YouTube (o închizi din meniul ⋮ → Ieșire). Punctul de lângă logo devine **verde** când tab-ul YouTube e conectat.

| Buton / gest | Acțiune |
|---|---|
| ▶ / ❚❚ | play / pauză |
| ⏮ ⏭ | anterior / următorul |
| ⏪ ⏩ | −10 s / +10 s |
| ■ | stop: oprește și revine la început |
| 🔗 | lipește telecomanda în colțul ferestrei YouTube; o urmează când muți fereastra (Hyprland). Încă un click, sau mutarea telecomenzii cu mouse-ul, o dezlipește |
| 🔁 | repetă videoclipul curent |
| bara de progres | seek (click sau trage) |
| 🔊 + slider | volum / mut (rotița mouse-ului peste telecomandă schimbă volumul) |
| 👍 | like (dacă ești autentificat) |
| `1×` | viteza de redare |
| `SKIP ▸` | sare peste reclamă, când YouTube permite |
| 👤 | contul Google: te autentifici în YouTube; când ești conectat arată poza contului (meniu: schimbă contul, deconectare) |
| 🔍 | caută pe YouTube (singurul loc de căutare: căsuța YouTube e ascunsă); click pe rezultat îl redă în YukiTube |
| ⇕ / dublu-click pe fundal | mod compact / complet |
| ⋮ / click dreapta pe fundal | mereu deasupra, transparență, „Conectează YukiTube”, ajutor |
| Ctrl + rotiță | transparența ferestrei |

Tastatură (cu telecomanda activă): `Space`/`K` play-pauză · `S` stop · `D` lipește/dezlipește · `←` `→` ±5 s · `J` −10 s · `↑` `↓` volum · `M` mut · `L` repetă · `N` următorul · `P` anterior · `Ctrl+F` sau `/` caută · `Esc` închide căutarea.

Telecomanda se redimensionează trăgând de margini: lățimea oricând, înălțimea cât e deschisă căutarea (mai multe rezultate). Mărimea se ține minte. Pe Hyprland telecomanda plutește singură (nu intră în tiling); ca să rămână și pe toate workspace-urile, poți adăuga `windowrule = pin, class:^(yukitube-remote)$` (sintaxa exactă depinde de versiunea Hyprland).

## Scurtături în fereastra YouTube

| Tastă | Ce face |
| --- | --- |
| `Alt+←` / `Alt+→` | Înapoi / înainte |
| `Ctrl+L` | Bara de adrese: lipește un link sau caută |
| `Ctrl+R` / `F5` | Reîncarcă |
| `Ctrl+W` | Închide pagina curentă (de ex. pagina Violentmonkey după instalarea punții) |
| `F11` | Ecran complet |
| `Ctrl+=` / `Ctrl+-` / `Ctrl+0` | Zoom |
| `Ctrl+Q` | Ieșire |
| `Space`, `K`, `J`, `L`, `F`, `M` | Playerul YouTube: pauză, înapoi/înainte 10 s, ecran complet, sunet |
| `?` | Toate scurtăturile YouTube |

## Unde stau datele

- Profilul Firefox (autentificare, istoric, setări uBlock, puntea YukiTube): `~/.local/share/yukitube/profile`.
- Setările telecomenzii: `~/.config/YukiTube/remote.conf` (la prima pornire preia setările vechiului NeonTube).
- Jurnalul telecomenzii: `~/.local/state/yukitube/remote.log`.

Dezinstalarea nu le șterge; le ștergi tu dacă vrei să pornești de la zero.

## Licență

YukiTube: MIT (vezi `LICENSE`). Fonturile telecomenzii (Orbitron, Share Tech Mono): SIL Open Font License 1.1. Extensiile își păstrează licențele lor.
