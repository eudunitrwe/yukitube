YukiTube 0.3 pentru Windows 10 / 11 (64 de biți)
================================================

YouTube într-o fereastră proprie, fără reclame și fără
„Video întrerupt. Continui vizionarea?”, în stil retrowave, cu o
telecomandă mică și transparentă care controlează YouTube-ul din fereastra
YukiTube. (Telecomanda se numea înainte NeonTube.) Fereastra și YouTube-ul
din ea poartă culorile telecomenzii: mov închis, roz și cyan neon.

Versiunea este portabilă: are tot ce îi trebuie în folderul ei (propriul
Firefox 160.0.1 în română, telecomanda, extensiile și profilul tău). Nu
trebuie să instalezi nimic, nici măcar Firefox sau Python. Poți ține
folderul pe un stick USB.

Extensii incluse (versiunile semnate de pe addons.mozilla.org; după prima
pornire, Firefox le actualizează singur):

  - uBlock Origin 1.77.0 (GPL-3.0, Raymond Hill): blochează reclamele,
    inclusiv pe cele video de pe YouTube.
  - YouTube NonStop 0.9.2 (MIT, Nikos Ioannou): închide singur dialogul
    „Continui vizionarea?”.
  - Violentmonkey 2.50.0 (MIT): rulează „YukiTube Bridge”, puntea prin
    care telecomanda vorbește cu YouTube.

CUM ÎL INSTALEZI ȘI ÎL PORNEȘTI E DESCRIS PAS CU PAS ÎN INSTALARE.txt.


CE E ÎN FOLDER

  YukiTube.exe                Pornește YukiTube (YouTube + telecomanda).
  Creeaza-scurtaturi.cmd      Pune YukiTube în meniul Start și pe Desktop.
  Sterge-scurtaturi.cmd       Scoate scurtăturile.
  App\Firefox\                Firefox-ul folosit de YukiTube. Nu îl porni
                              direct.
  App\Remote\                 Telecomanda YukiTube (Python + Qt incluse).
  App\share\                  Extensiile și setările.
  Data\                       Profilul tău: autentificare, istoric, setări
                              uBlock. Apare la prima pornire.


TELECOMANDA

Pornește odată cu YukiTube și rămâne deschisă și după ce închizi
fereastra YouTube (o închizi din meniul ⋮ > Ieșire). Punctul de lângă
logo devine verde când tab-ul YouTube e conectat.

  ▶ / ❚❚           play / pauză
  ⏮ ⏭              anterior / următorul
  ⏪ ⏩              −10 s / +10 s
  ■                 stop: oprește și revine la început
  🔗                lipește telecomanda în colțul ferestrei YouTube și o
                    urmează când muți fereastra; încă un click o dezlipește
  bara de progres   seek (click sau trage)
  🔊 + slider       volum / mut (rotița mouse-ului schimbă volumul)
  1×                viteza de redare
  SKIP ▸            sare peste reclamă, când YouTube permite
  🔍                caută pe YouTube; click pe rezultat îl redă în YukiTube
  ⋮                 mereu deasupra, transparență, „Conectează YukiTube”
  Ctrl + rotiță     transparența ferestrei

Tastatură (cu telecomanda activă): Space/K play-pauză, S stop,
D lipește/dezlipește, ← → ±5 s,
J −10 s, ↑ ↓ volum, M mut, L repetă, N următorul, P anterior,
Ctrl+F sau / caută, Esc închide căutarea.

Doar telecomanda, fără fereastra YouTube: scurtătura
„YukiTube - telecomanda” din meniul Start, sau YukiTube.exe --remote.


SCURTĂTURI ÎN FEREASTRA YOUTUBE

  Alt+Stânga / Alt+Dreapta    Înapoi / înainte
  Ctrl+L                      Bara de adrese: lipește un link sau caută
  Ctrl+R / F5                 Reîncarcă
  Ctrl+W                      Închide pagina curentă (de ex. pagina
                              Violentmonkey după instalarea punții)
  F11                         Ecran complet
  Ctrl+= / Ctrl+- / Ctrl+0    Zoom
  Space, K, J, L, F, M        Playerul YouTube: pauză, înapoi/înainte
                              10 s, ecran complet, sunet
  ?                           Toate scurtăturile YouTube


DE ȘTIUT

  - Firefox-ul din folder se actualizează singur, ca orice Firefox.
  - Pe bara de activități (taskbar), fereastra YouTube apare cu iconița
    Firefox, pentru că este tot Firefox.
  - Telecomanda ascultă doar pe 127.0.0.1:8975 (doar calculatorul tău);
    Windows Firewall nu ar trebui să întrebe nimic.
  - Setările telecomenzii (poziție, transparență) stau în registry, la
    HKCU\Software\YukiTube\remote. Windows mai păstrează câteva fișiere mici
    de-ale lui Firefox în %APPDATA%\Mozilla și %LOCALAPPDATA%\Mozilla.
    Datele tale (profilul) rămân doar în Data\.


LICENȚE

YukiTube: MIT (vezi LICENSE.txt). Firefox: Mozilla Public
License 2.0. Python: PSF License. Qt / PySide6: LGPL-3.0. Fonturile
telecomenzii: SIL Open Font License 1.1. Extensiile își păstrează
licențele lor.
