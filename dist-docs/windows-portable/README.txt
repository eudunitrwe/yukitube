YukiTube Portabil pentru Windows 10 / 11
========================================

YouTube într-o fereastră proprie, fără reclame și fără
„Video întrerupt. Continui vizionarea?”.

Versiunea portabilă are tot ce îi trebuie în folderul ei: propriul Firefox
(160.0.1, în română), extensiile și profilul tău. Nu trebuie să instalezi
nimic, nici măcar Firefox. Poți ține folderul pe un stick USB și îl poți
folosi pe orice calculator cu Windows 10 sau 11 (64 de biți).

Extensii incluse (versiunile semnate de pe addons.mozilla.org; după prima
pornire, Firefox le actualizează singur):

  - uBlock Origin 1.77.0 (GPL-3.0, Raymond Hill): blochează reclamele,
    inclusiv pe cele video de pe YouTube.
  - YouTube NonStop 0.9.2 (MIT, Nikos Ioannou): închide singur dialogul
    „Continui vizionarea?”.

Cum îl pornești e descris în INSTRUCTIUNI.txt.


CE E ÎN FOLDER

  YukiTube.exe        Pornește YukiTube.
  App\Firefox\        Firefox-ul folosit de YukiTube. Nu îl porni direct.
  App\share\          Extensiile și setările.
  Data\               Profilul tău: autentificare, istoric, setări uBlock.
                      Apare la prima pornire.


SCURTĂTURI

  Alt+Stânga / Alt+Dreapta    Înapoi / înainte
  Ctrl+L                      Bara de adrese: lipește un link sau caută
  Ctrl+R / F5                 Reîncarcă
  F11                         Ecran complet
  Ctrl+= / Ctrl+- / Ctrl+0    Zoom
  Space, K, J, L, F, M        Playerul YouTube: pauză, înapoi/înainte
                              10 s, ecran complet, sunet
  ?                           Toate scurtăturile YouTube

Butonul uBlock Origin din dreapta barei de adrese deschide panoul lui.


DE ȘTIUT

  - Firefox-ul din folder se actualizează singur, ca orice Firefox.
  - Pe bara de activități (taskbar), fereastra apare cu iconița Firefox,
    pentru că este tot Firefox.
  - Windows mai păstrează câteva fișiere mici de-ale lui Firefox în
    %APPDATA%\Mozilla și %LOCALAPPDATA%\Mozilla. Datele tale (profilul)
    rămân doar în Data\.


LICENȚE

YukiTube: MIT (vezi LICENSE.txt). Firefox: Mozilla Public License 2.0.
Extensiile își păstrează licențele lor.
