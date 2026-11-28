# YukiTube

**🇬🇧 A small music & video player for YouTube, for Linux, Windows 10/11 and Android.**
**🇷🇴 Un player mic de muzică și video pentru YouTube, pentru Linux, Windows 10/11 și Android.**

Made by **[eudunitrwe](https://github.com/eudunitrwe)** with the help of **[Claude Code](https://claude.com/claude-code)**.
Făcut de **[eudunitrwe](https://github.com/eudunitrwe)** cu ajutorul **[Claude Code](https://claude.com/claude-code)**.

### ⬇️ [Download / Descarcă](https://github.com/eudunitrwe/yukitube/releases/latest)

---

## 🇬🇧 English

### What it does

- Plays YouTube from a compact player window — no ads, no "Video paused. Continue watching?".
- **Search** (🔍 or `Ctrl+F`) and play with one click.
- **Playlists** (☰♪): your own (Liked videos, Watch later and the rest) and the ones YouTube suggests for you; ☰ on a playlist shows its songs.
- **Video mode** (📺): the window grows and shows the video; the ⛶ button in its bottom right corner (or a double-click) makes it full screen.
- **Music for you:** recommendations based on what you listen to.
- Play/pause, previous/next, seek, volume, speed, loop, like.
- Sign in with your **Google account** (👤) for your playlists and personal recommendations.
- **Skins:** Retrowave, classic 90s, Windows 11 light/dark, Nord, Arch_D.
- Languages: English, Română, Русский.
- **Updates itself** from GitHub (⚙ Settings → Check now / Update now).

### Install on Linux

From the [latest release](https://github.com/eudunitrwe/yukitube/releases/latest), use **one** of these:

**Arch Linux** — `yukitube-<version>-1-any.pkg.tar.zst`:

```sh
sudo pacman -U yukitube-<version>-1-any.pkg.tar.zst      # uninstall: sudo pacman -R yukitube
```

**Any distro** (x86_64; Ubuntu 22.04+, Debian 12+, Fedora 35+…) — `yukitube-<version>-linux-x86_64.tar.xz`, no sudo:

```sh
tar -xJf yukitube-<version>-linux-x86_64.tar.xz
cd yukitube-<version>-linux-x86_64
./install.sh                                            # uninstall: ./install.sh --uninstall
```

The installer tells you if anything is missing. Then start **YukiTube** from your app launcher or with `yukitube`.

### Install on Windows 10/11

From the [latest release](https://github.com/eudunitrwe/yukitube/releases/latest), use **one** of these (everything is included):

- **Installer:** run `yukitube-<version>-windows-x64-setup.exe`. It adds a **YukiTube** shortcut on the Desktop and in the Start menu. Uninstall from Settings → Apps.
- **Portable:** extract `yukitube-<version>-windows-x64.zip` (right-click → **Extract All…**) and double-click **`YukiTube.exe`**. To uninstall, delete the folder.

If SmartScreen says "Windows protected your PC", click **More info → Run anyway**.

The first start takes a few seconds longer while YukiTube sets itself up.

### Install on Android (8.0 and newer)

From the [latest release](https://github.com/eudunitrwe/yukitube/releases/latest), download `yukitube-<version>-android.apk` on your phone and open it. If Android asks, allow your browser to **install unknown apps**, then tap **Install**.

YukiTube keeps playing with the screen off or in another app (controls in the notification and on the lock screen). Back or Home leaves it playing; to quit, use ⚙ Settings → Quit YukiTube, the ✕ in the notification, or swipe it away from the recent apps. Share a YouTube link to YukiTube to play it. Updates install from ⚙ Settings → Update now.

---

## 🇷🇴 Română

### Ce face

- Redă YouTube într-o fereastră mică de player — fără reclame, fără „Continui vizionarea?”.
- **Căutare** (🔍 sau `Ctrl+F`) și redare dintr-un click.
- **Playlisturi** (☰♪): ale tale (Videoclipuri apreciate, De vizionat mai târziu și celelalte) și cele propuse de YouTube pentru tine; ☰ de pe un playlist îi arată melodiile.
- **Mod video** (📺): fereastra se mărește și arată videoclipul; butonul ⛶ din colțul lui din dreapta-jos (sau dublu-click) îl face pe tot ecranul.
- **Muzică pentru tine:** recomandări după ce asculți.
- Pauză/redare, anterior/următor, derulare, volum, viteză, repetare, like.
- Conectare cu **contul Google** (👤) pentru playlisturile tale și recomandări personale.
- **Skin-uri:** Retrowave, clasic anii ’90, Windows 11 luminos/întunecat, Nord, Arch_D.
- Limbi: English, Română, Русский.
- **Se actualizează singur** din GitHub (⚙ Setări → Verifică acum / Actualizează acum).

### Instalare pe Linux

Din [ultima versiune](https://github.com/eudunitrwe/yukitube/releases/latest), folosește **una** dintre variante:

**Arch Linux** — `yukitube-<versiune>-1-any.pkg.tar.zst`:

```sh
sudo pacman -U yukitube-<versiune>-1-any.pkg.tar.zst     # dezinstalare: sudo pacman -R yukitube
```

**Orice distribuție** (x86_64; Ubuntu 22.04+, Debian 12+, Fedora 35+…) — `yukitube-<versiune>-linux-x86_64.tar.xz`, fără sudo:

```sh
tar -xJf yukitube-<versiune>-linux-x86_64.tar.xz
cd yukitube-<versiune>-linux-x86_64
./install.sh                                            # dezinstalare: ./install.sh --uninstall
```

Installerul îți spune dacă lipsește ceva. Apoi pornește **YukiTube** din launcher sau cu `yukitube`.

### Instalare pe Windows 10/11

Din [ultima versiune](https://github.com/eudunitrwe/yukitube/releases/latest), folosește **una** dintre variante (totul e inclus):

- **Installer:** rulează `yukitube-<versiune>-windows-x64-setup.exe`. Pune o scurtătură **YukiTube** pe Desktop și în meniul Start. Dezinstalare din Setări → Aplicații.
- **Portabil:** dezarhivează `yukitube-<versiune>-windows-x64.zip` (click dreapta → **Extract All…**) și dă dublu-click pe **`YukiTube.exe`**. Dezinstalare: șterge folderul.

Dacă SmartScreen afișează „Windows protected your PC”, apasă **More info → Run anyway**.

Prima pornire durează câteva secunde în plus, cât YukiTube se pregătește singur.

### Instalare pe Android (8.0 sau mai nou)

Din [ultima versiune](https://github.com/eudunitrwe/yukitube/releases/latest), descarcă `yukitube-<versiune>-android.apk` pe telefon și deschide-l. Dacă Android cere, permite-i browserului să **instaleze aplicații necunoscute**, apoi apasă **Instalează**.

YukiTube cântă și cu ecranul stins sau din altă aplicație (butoane în notificare și pe ecranul de blocare). Înapoi sau Acasă îl lasă să cânte; ca să-l închizi: ⚙ Setări → Închide YukiTube, ✕ din notificare, sau glisează-l din aplicațiile recente. Partajează un link YouTube către YukiTube ca să-l redai. Actualizările se instalează din ⚙ Setări → Actualizează acum.
