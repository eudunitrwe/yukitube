YukiTube 0.4 pentru Windows 10 / 11 (64 de biți)
================================================

Un player YouTube fără reclame și fără „Video întrerupt. Continui
vizionarea?”. Folosești doar telecomanda YukiTube (căutare, redare, volum,
cont Google), iar YouTube cântă într-un Firefox ascuns, în spatele ei.
Fereastra YouTube apare doar când o ceri.

Versiunea este portabilă: are tot ce îi trebuie în folderul ei (propriul
Firefox 160.0.1 în română, telecomanda, extensiile și profilul tău). Nu
trebuie să instalezi nimic, nici măcar Firefox sau Python. Poți ține
folderul pe un stick USB.

Extensii incluse (versiunile semnate de pe addons.mozilla.org; după prima
pornire, Firefox le actualizează singur):

  - uBlock Origin 1.77.0 (GPL-3.0, Raymond Hill): blochează reclamele,
    inclusiv pe cele video.
  - YouTube NonStop 0.9.2 (MIT, Nikos Ioannou): închide singur dialogul
    „Continui vizionarea?”.
  - Violentmonkey 2.50.0 (MIT): rulează „YukiTube Bridge”, puntea prin
    care telecomanda vorbește cu YouTube.

CUM ÎL INSTALEZI ȘI ÎL PORNEȘTI E DESCRIS PAS CU PAS ÎN INSTALARE.txt.


CE E ÎN FOLDER

  YukiTube.exe                Pornește YukiTube.
  Creeaza-scurtaturi.cmd      Pune YukiTube în meniul Start și pe Desktop.
  Sterge-scurtaturi.cmd       Scoate scurtăturile.
  App\Firefox\                Firefox-ul folosit de YukiTube (fără
                              actualizator și alte piese de care YukiTube
                              nu are nevoie). Nu îl porni direct.
  App\Remote\                 Telecomanda YukiTube (Python + Qt incluse).
  App\share\                  Extensiile și setările.
  Data\                       Profilul tău: autentificare, istoric, setări
                              uBlock. Apare la prima pornire.


TELECOMANDA

Când o închizi (⋮ > Ieșire, sau X), se oprește și YouTube. Punctul de
lângă logo devine verde când YouTube e conectat.

  ▶ / ❚❚           play / pauză
  ⏮ ⏭              anterior / următorul
  ⏪ ⏩              −10 s / +10 s
  ■                 stop: oprește și revine la început
  bara de progres   seek (click sau trage)
  🔊 + slider       volum / mut (rotița mouse-ului schimbă volumul)
  1×                viteza de redare
  SKIP ▸            sare peste reclamă, când YouTube permite
  omulețul          contul Google: autentificare, schimbă contul,
                    deconectare
  paleta            skin-ul: Retrowave (neon) sau Clasic (anii ’90)
  🔍                caută pe YouTube; click pe rezultat îl redă
  ↗                 arată / ascunde fereastra YouTube
  ⋮                 mereu deasupra, skin, transparență, ajutor
  Ctrl + rotiță     transparența ferestrei (implicit 55%)

Tastatură (cu telecomanda activă): Space/K play-pauză, S stop, ← → ±5 s,
J −10 s, ↑ ↓ volum, M mut, L repetă, N următorul, P anterior,
Ctrl+F sau / caută, Esc închide căutarea.


DE ȘTIUT

  - Firefox-ul din folder nu se actualizează singur; versiunile noi de
    YukiTube vin cu Firefox nou. Extensiile se actualizează singure.
  - Cache-ul Firefox e limitat la 100 MB pentru pagini și 100 MB pentru
    media, ca folderul Data să nu crească mult.
  - Telecomanda ascultă doar pe 127.0.0.1:8975 (doar calculatorul tău);
    Windows Firewall nu ar trebui să întrebe nimic.
  - Setările telecomenzii (poziție, skin, transparență) stau în registry, la
    HKCU\Software\YukiTube\remote. Windows mai păstrează câteva fișiere mici
    de-ale lui Firefox în %APPDATA%\Mozilla și %LOCALAPPDATA%\Mozilla.
    Datele tale (profilul) rămân doar în Data\.


LICENȚE

YukiTube: MIT (vezi LICENSE.txt). Firefox: Mozilla Public
License 2.0. Python: PSF License. Qt / PySide6: LGPL-3.0. Fonturile
telecomenzii: SIL Open Font License 1.1. Extensiile își păstrează
licențele lor.
