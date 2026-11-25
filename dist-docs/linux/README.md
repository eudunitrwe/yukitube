# YukiTube 0.4 pentru Linux

Un player YouTube fără reclame și fără „Video întrerupt. Continui vizionarea?”. Folosești doar **telecomanda YukiTube** (căutare, redare, volum, cont Google), iar YouTube cântă într-un Firefox ascuns, în spatele ei, pe un profil separat: autentificarea, istoricul și extensiile nu se amestecă cu Firefox-ul tău obișnuit. Fereastra YouTube apare doar când o ceri.

Extensii incluse (versiunile semnate de pe addons.mozilla.org; după instalare, Firefox le actualizează singur):

- **uBlock Origin** 1.77.0 (GPL-3.0, Raymond Hill): blochează reclamele, inclusiv pe cele video.
- **YouTube NonStop** 0.9.2 (MIT, Nikos Ioannou): închide singur dialogul „Continui vizionarea?”.
- **Violentmonkey** 2.50.0 (MIT): rulează „YukiTube Bridge”, puntea prin care telecomanda vorbește cu YouTube.

**Instalarea e descrisă pas cu pas în `INSTALARE.md`.**

## Folosire

Din launcher (caută „YukiTube”) sau din terminal:

```sh
yukitube                                  # telecomanda (YouTube pornește ascuns)
yukitube https://youtu.be/dQw4w9WgXcQ     # redă un link YouTube
yukitube muzică de studiu                 # caută în telecomandă
yukitube --remote                         # doar telecomanda, pentru alt browser
```

Dacă YukiTube rulează deja, link-ul sau căutarea ajung în telecomanda deschisă. Când închizi telecomanda, se oprește și YouTube.

## Telecomanda

| Buton / gest | Acțiune |
|---|---|
| ▶ / ❚❚ | play / pauză |
| ⏮ ⏭ | anterior / următorul |
| ⏪ ⏩ | −10 s / +10 s |
| ■ | stop: oprește și revine la început |
| 🔁 | repetă videoclipul curent |
| bara de progres | seek (click sau trage) |
| 🔊 + slider | volum / mut (rotița mouse-ului peste telecomandă schimbă volumul) |
| 👍 | like (dacă ești autentificat) |
| `1×` | viteza de redare |
| `SKIP ▸` | sare peste reclamă, când YouTube permite |
| 👤 | contul Google: autentificare; când ești conectat arată poza contului (meniu: schimbă contul, deconectare) |
| 🎨 | skin-ul: **Retrowave** (neon) sau **Clasic (anii ’90)** (carcasă de metal, display LCD verde) |
| 🔍 | caută pe YouTube; click pe rezultat îl redă |
| ↗ | arată / ascunde fereastra YouTube |
| ⇕ / dublu-click pe fundal | mod compact / complet |
| ⋮ / click dreapta pe fundal | mereu deasupra, skin, limba (English / Română / Русский; implicit engleză), transparență, ajutor |
| Ctrl + rotiță | transparența ferestrei (implicit 55%) |

Tastatură (cu telecomanda activă): `Space`/`K` play-pauză · `S` stop · `←` `→` ±5 s · `J` −10 s · `↑` `↓` volum · `M` mut · `L` repetă · `N` următorul · `P` anterior · `Ctrl+F` sau `/` caută · `Esc` închide căutarea.

Pe Hyprland telecomanda plutește singură (nu intră în tiling); ca să rămână pe toate workspace-urile, poți adăuga `windowrule = pin, class:^(yukitube-remote)$` (sintaxa exactă depinde de versiunea Hyprland).

## Unde stau datele

- Profilul Firefox (autentificare, istoric, setări uBlock, puntea YukiTube): `~/.local/share/yukitube/profile`. Cache-ul lui e limitat la 100 MB pentru pagini și 100 MB pentru media.
- Setările telecomenzii (poziție, skin, transparență): `~/.config/YukiTube/remote.conf`.
- Jurnalul telecomenzii: `~/.local/state/yukitube/remote.log`.

Dezinstalarea nu le șterge; le ștergi tu dacă vrei să pornești de la zero.

## Licență

YukiTube: MIT (vezi `LICENSE`). Fonturile telecomenzii (Orbitron, Share Tech Mono): SIL Open Font License 1.1. Extensiile își păstrează licențele lor.
