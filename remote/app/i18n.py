"""The remote's interface languages: English (the default), Romanian, Russian.

T("key", name=value) gives the current language's text; set_lang() switches.
"""

LANGS = {"en": "English", "ro": "Română", "ru": "Русский"}
LANG = "en"

STRINGS = {
    # header and buttons
    "tab_chip_tip": {"en": "Switch the YouTube tab being controlled", "ro": "Schimbă tab-ul YouTube controlat",
                     "ru": "Выбрать вкладку YouTube для управления"},
    "account_signin": {"en": "Sign in with Google", "ro": "Conectează contul Google", "ru": "Войти в аккаунт Google"},
    "account_signed_in": {"en": "Google account connected", "ro": "Cont Google conectat",
                          "ru": "Аккаунт Google подключён"},
    "skin_tip": {"en": "Change skin", "ro": "Schimbă skin-ul", "ru": "Сменить скин"},
    "search_tip": {"en": "Search  (Ctrl+F)", "ro": "Caută  (Ctrl+F)", "ru": "Поиск  (Ctrl+F)"},
    "search_close": {"en": "Close the search  (Esc)", "ro": "Închide căutarea  (Esc)", "ru": "Закрыть поиск  (Esc)"},
    "compact": {"en": "Compact mode", "ro": "Mod compact", "ru": "Компактный режим"},
    "full": {"en": "Full mode", "ro": "Mod complet", "ru": "Полный режим"},
    "menu": {"en": "Menu", "ro": "Meniu", "ru": "Меню"},
    "minimize": {"en": "Minimize", "ro": "Minimizează", "ru": "Свернуть"},
    "close": {"en": "Close", "ro": "Închide", "ru": "Закрыть"},
    "like": {"en": "Like", "ro": "Like", "ru": "Нравится"},
    "speed_tip": {"en": "Playback speed", "ro": "Viteza de redare", "ru": "Скорость воспроизведения"},
    "skip_tip": {"en": "Skip the ad (when possible)", "ro": "Sari peste reclamă (dacă se poate)",
                 "ru": "Пропустить рекламу (если можно)"},
    "youtube_window_tip": {"en": "Show / hide the YouTube window", "ro": "Arată / ascunde fereastra YouTube",
                           "ru": "Показать / скрыть окно YouTube"},
    "thumb_tip": {"en": "Show the tab in the browser", "ro": "Arată tab-ul în browser",
                  "ru": "Показать вкладку в браузере"},
    "play_tip": {"en": "Play / Pause  (Space)", "ro": "Play / Pauză  (Space)", "ru": "Воспроизведение / пауза  (Space)"},
    "loop_tip": {"en": "Repeat the video  (L)", "ro": "Repetă videoclipul  (L)", "ru": "Повторять видео  (L)"},
    "prev_tip": {"en": "Previous  (P)", "ro": "Anterior  (P)", "ru": "Предыдущее  (P)"},
    "rew_tip": {"en": "Back 10 s  (←)", "ro": "Înapoi 10 s  (←)", "ru": "Назад 10 с  (←)"},
    "fwd_tip": {"en": "Forward 10 s  (→)", "ro": "Înainte 10 s  (→)", "ru": "Вперёд 10 с  (→)"},
    "next_tip": {"en": "Next  (N)", "ro": "Următorul  (N)", "ru": "Следующее  (N)"},
    "stop_tip": {"en": "Stop  (S)", "ro": "Stop  (S)", "ru": "Стоп  (S)"},
    "mute_tip": {"en": "Mute  (M)", "ro": "Mut  (M)", "ru": "Без звука  (M)"},
    "volume_tip": {"en": "Volume {v}%", "ro": "Volum {v}%", "ru": "Громкость {v}%"},
    "search_placeholder": {"en": "Search YouTube…", "ro": "Caută pe YouTube…", "ru": "Поиск на YouTube…"},

    # tray
    "play_pause": {"en": "Play / Pause", "ro": "Play / Pauză", "ru": "Воспроизведение / пауза"},
    "next": {"en": "Next", "ro": "Următorul", "ru": "Следующее"},
    "prev": {"en": "Previous", "ro": "Anterior", "ru": "Предыдущее"},
    "toggle_remote": {"en": "Show / hide the player", "ro": "Arată / ascunde telecomanda",
                      "ru": "Показать / скрыть плеер"},
    "quit": {"en": "Quit", "ro": "Ieșire", "ru": "Выход"},

    # menu
    "always_on_top": {"en": "Always on top", "ro": "Mereu deasupra", "ru": "Поверх всех окон"},
    "skin": {"en": "Skin", "ro": "Skin", "ru": "Скин"},
    "skin_retrowave": {"en": "Retrowave", "ro": "Retrowave", "ru": "Ретровейв"},
    "skin_classic": {"en": "Classic (90s)", "ro": "Clasic (anii ’90)", "ru": "Классика (90-е)"},
    "skin_win11_light": {"en": "Windows 11 (Light)", "ro": "Windows 11 (Luminos)", "ru": "Windows 11 (светлая)"},
    "skin_win11_dark": {"en": "Windows 11 (Dark)", "ro": "Windows 11 (Întunecat)", "ru": "Windows 11 (тёмная)"},
    "skin_nord": {"en": "Nord", "ro": "Nord", "ru": "Nord"},
    "skin_arch_d": {"en": "Arch_D", "ro": "Arch_D", "ru": "Arch_D"},
    "language": {"en": "Language", "ro": "Limba", "ru": "Язык"},
    "code_anim": {"en": "Code animation", "ro": "Animație cod", "ru": "Анимация кода"},
    "grid_anim": {"en": "Grid animation", "ro": "Animație grilă", "ru": "Анимация сетки"},
    "transparency": {"en": "Transparency", "ro": "Transparență", "ru": "Прозрачность"},
    "opaque": {"en": "{pct}% opaque", "ro": "{pct}% opac", "ru": "Непрозрачность {pct}%"},
    "show_youtube": {"en": "Show the YouTube window", "ro": "Arată fereastra YouTube",
                     "ru": "Показать окно YouTube"},
    "hide_youtube": {"en": "Hide the YouTube window", "ro": "Ascunde fereastra YouTube", "ru": "Скрыть окно YouTube"},
    "open_youtube": {"en": "Open YouTube", "ro": "Deschide YouTube", "ru": "Открыть YouTube"},
    "install_bridge": {"en": "Connect YukiTube (install the bridge)",
                       "ro": "Conectează YukiTube (instalează puntea)",
                       "ru": "Подключить YukiTube (установить мост)"},
    "how_connect": {"en": "How do I connect a browser?", "ro": "Cum conectez browserul?",
                    "ru": "Как подключить браузер?"},
    "about": {"en": "About {app} {version}", "ro": "Despre {app} {version}", "ru": "О программе {app} {version}"},
    "auto_tab": {"en": "Automatic (the tab that plays)", "ro": "Automat (tab-ul care cântă)",
                 "ru": "Автоматически (вкладка, которая играет)"},

    # dialogs
    "connect_title": {"en": "{app} — connecting", "ro": "{app} — conectare", "ru": "{app} — подключение"},
    "connect_help": {
        "en": "YukiTube sets up its bridge by itself. If the dot does not turn green:\n"
              "menu ⋮ → “Connect YukiTube (install the bridge)”, then click “Install”\n"
              "on the Violentmonkey page.\n\n"
              "Another browser (Chrome, Edge, your usual Firefox…): install Violentmonkey\n"
              "or Tampermonkey, then open in that browser\n"
              "http://127.0.0.1:{port}/yukitube.user.js and click Install.\n\n"
              "Then reload the YouTube tab. The dot in the corner turns green.",
        "ro": "YukiTube își instalează singur puntea. Dacă punctul nu se face verde:\n"
              "meniul ⋮ → „Conectează YukiTube (instalează puntea)”, apoi apasă\n"
              "„Install” în pagina Violentmonkey.\n\n"
              "Alt browser (Chrome, Edge, Firefox obișnuit…): instalează Violentmonkey\n"
              "sau Tampermonkey, apoi deschide în acel browser\n"
              "http://127.0.0.1:{port}/yukitube.user.js și apasă Install.\n\n"
              "Apoi reîncarcă tab-ul YouTube. Punctul din colț devine verde.",
        "ru": "YukiTube сам устанавливает мост. Если точка не становится зелёной:\n"
              "меню ⋮ → «Подключить YukiTube (установить мост)», затем нажмите\n"
              "«Install» на странице Violentmonkey.\n\n"
              "Другой браузер (Chrome, Edge, обычный Firefox…): установите Violentmonkey\n"
              "или Tampermonkey, затем откройте в этом браузере\n"
              "http://127.0.0.1:{port}/yukitube.user.js и нажмите Install.\n\n"
              "Затем перезагрузите вкладку YouTube. Точка в углу станет зелёной."},
    "about_text": {
        "en": "<b>{app} {version}</b><br>The YukiTube player.<br><br>Local port: 127.0.0.1:{port}<br>"
              "Shortcuts: Space, S (stop), ←/→, ↑/↓, M, L, N, P, Ctrl+F, Ctrl+wheel = transparency",
        "ro": "<b>{app} {version}</b><br>Playerul YukiTube.<br><br>Port local: 127.0.0.1:{port}<br>"
              "Scurtături: Space, S (stop), ←/→, ↑/↓, M, L, N, P, Ctrl+F, Ctrl+rotiță = transparență",
        "ru": "<b>{app} {version}</b><br>Плеер YukiTube.<br><br>Локальный порт: 127.0.0.1:{port}<br>"
              "Клавиши: Space, S (стоп), ←/→, ↑/↓, M, L, N, P, Ctrl+F, Ctrl+колесо = прозрачность"},
    "port_busy": {
        "en": "Cannot start the local server on port {port}.\nThe YukiTube player is probably already running.\n\n{err}",
        "ro": "Nu pot porni serverul local pe portul {port}.\nProbabil telecomanda YukiTube rulează deja.\n\n{err}",
        "ru": "Не удаётся запустить локальный сервер на порту {port}.\nВероятно, плеер YukiTube уже запущен.\n\n{err}"},
    "signin_hint": {
        "en": "Sign in in the YouTube window; it closes by itself once you are signed in.",
        "ro": "Autentifică-te în fereastra YouTube; se închide singură după ce ești conectat.",
        "ru": "Войдите в окне YouTube; оно закроется само после входа."},

    # account menu
    "signed_in_as": {"en": "✓ Signed in with Google", "ro": "✓ Conectat cu contul Google",
                     "ru": "✓ Вход через Google выполнен"},
    "switch_account": {"en": "Switch account", "ro": "Schimbă contul", "ru": "Сменить аккаунт"},
    "sign_out": {"en": "Sign out", "ro": "Deconectare", "ru": "Выйти"},

    # search results
    "play_here": {"en": "Play in the current tab", "ro": "Redă în tab-ul curent", "ru": "Воспроизвести в текущей вкладке"},
    "open_new_tab": {"en": "Open in a new tab", "ro": "Deschide într-un tab nou", "ru": "Открыть в новой вкладке"},
    "copy_link": {"en": "Copy the link", "ro": "Copiază link-ul", "ru": "Копировать ссылку"},
    "searching": {"en": "Searching “{q}”…", "ro": "Caut „{q}”…", "ru": "Ищу «{q}»…"},
    "search_failed": {"en": "Search failed: {err}", "ro": "Căutarea a eșuat: {err}", "ru": "Поиск не удался: {err}"},
    "no_results_err": {"en": "no results", "ro": "niciun rezultat", "ru": "нет результатов"},
    "search_timeout": {"en": "Search failed (timeout).", "ro": "Căutarea a eșuat (timeout).",
                       "ru": "Поиск не удался (тайм-аут)."},
    "no_results": {"en": "No results. {err}", "ro": "Niciun rezultat. {err}", "ru": "Нет результатов. {err}"},
    "hint_tab": {"en": "click = play · Ctrl/middle = new tab", "ro": "click = redă în tab · Ctrl/mijloc = tab nou",
                 "ru": "клик = играть · Ctrl/средняя = новая вкладка"},
    "hint_browser": {"en": "click = open in the browser", "ro": "click = deschide în browser",
                     "ru": "клик = открыть в браузере"},
    "results_for": {"en": "Results: {n} for “{q}”  ·  {hint}", "ro": "Rezultate: {n} pentru „{q}”  ·  {hint}",
                    "ru": "Результатов: {n} по запросу «{q}»  ·  {hint}"},

    # status
    "dot_connected": {"en": "Connected · {browser} · {n} tab(s)", "ro": "Conectat · {browser} · {n} tab(uri)",
                      "ru": "Подключено · {browser} · вкладок: {n}"},
    "dot_browser": {"en": "Browser connected · open YouTube", "ro": "Browser conectat · deschide YouTube",
                    "ru": "Браузер подключён · откройте YouTube"},
    "dot_waiting": {"en": "Waiting for YouTube…", "ro": "Aștept YouTube…", "ru": "Жду YouTube…"},
    "no_video": {"en": "No video open", "ro": "Niciun videoclip deschis", "ru": "Видео не открыто"},
    "search_hint": {"en": "Search for something and click a result ✦", "ro": "Caută ceva și apasă pe rezultat ✦",
                    "ru": "Найдите что-нибудь и нажмите на результат ✦"},
    "preparing": {"en": "Preparing YukiTube…", "ro": "Pregătesc YukiTube…", "ru": "Готовлю YukiTube…"},
    "starting": {"en": "Starting YouTube…", "ro": "Pornesc YouTube…", "ru": "Запускаю YouTube…"},
    "first_start": {"en": "First start: this takes a few seconds", "ro": "Prima pornire: durează câteva secunde",
                    "ru": "Первый запуск: это займёт несколько секунд"},
    "one_moment": {"en": "One moment…", "ro": "O clipă…", "ru": "Минутку…"},
    "no_tab": {"en": "No YouTube tab connected", "ro": "Niciun tab YouTube conectat",
               "ru": "Нет подключённой вкладки YouTube"},
    "install_bridge_hint": {"en": "Install the YukiTube bridge (menu ⋮)", "ro": "Instalează puntea YukiTube (meniul ⋮)",
                            "ru": "Установите мост YukiTube (меню ⋮)"},
    "open_in_browser": {"en": "Open YouTube in the browser", "ro": "Deschide YouTube în browser",
                        "ru": "Откройте YouTube в браузере"},
    # settings
    "settings": {"en": "Settings", "ro": "Setări", "ru": "Настройки"},
    "settings_menu": {"en": "Settings…", "ro": "Setări…", "ru": "Настройки…"},
    "settings_language": {"en": "Language", "ro": "Limba", "ru": "Язык"},
    "settings_autostart": {"en": "Start YukiTube with the computer", "ro": "Pornește YukiTube odată cu calculatorul",
                           "ru": "Запускать YukiTube вместе с компьютером"},
    "settings_shortcut": {"en": "Shortcut on the desktop", "ro": "Scurtătură pe desktop",
                          "ru": "Ярлык на рабочем столе"},
    "settings_shortcut_all": {"en": "The installer put it there for all users; uninstalling YukiTube removes it.",
                              "ro": "A pus-o instalatorul, pentru toți utilizatorii; dispare la dezinstalare.",
                              "ru": "Его создал установщик для всех пользователей; он удаляется вместе с YukiTube."},
    "settings_recs": {"en": "Show recommendations", "ro": "Arată recomandările", "ru": "Показывать рекомендации"},
    "settings_updates": {"en": "Updates", "ro": "Actualizări", "ru": "Обновления"},
    "settings_auto_update": {"en": "Look for a new version at start", "ro": "Caută o versiune nouă la pornire",
                             "ru": "Искать новую версию при запуске"},
    "settings_check_now": {"en": "Check now", "ro": "Verifică acum", "ru": "Проверить сейчас"},
    "settings_version": {"en": "Installed: {app} {v}", "ro": "Instalat: {app} {v}", "ru": "Установлено: {app} {v}"},
    "settings_close": {"en": "Close", "ro": "Închide", "ru": "Закрыть"},
    "settings_failed": {"en": "That did not work. Check that YukiTube can write to your user folders.",
                        "ro": "Nu a mers. Verifică dacă YukiTube poate scrie în folderele tale.",
                        "ru": "Не получилось. Проверьте, что YukiTube может записывать в ваши папки."},
    "check_updates": {"en": "Check for updates", "ro": "Caută actualizări", "ru": "Проверить обновления"},

    # updates
    "upd_checking": {"en": "Looking for a new version…", "ro": "Caut o versiune nouă…", "ru": "Ищу новую версию…"},
    "upd_none": {"en": "You have the latest version ({v}).", "ro": "Ai ultima versiune ({v}).",
                 "ru": "У вас последняя версия ({v})."},
    "upd_failed": {"en": "Could not look for updates: {err}", "ro": "Nu am putut căuta actualizări: {err}",
                   "ru": "Не удалось проверить обновления: {err}"},
    "upd_available": {"en": "✦ YukiTube {v} is out", "ro": "✦ A apărut YukiTube {v}", "ru": "✦ Вышел YukiTube {v}"},
    "upd_notify": {"en": "A new version, YukiTube {v}, is available. Download it from the player.",
                   "ro": "A apărut o versiune nouă, YukiTube {v}. O poți descărca din player.",
                   "ru": "Доступна новая версия YukiTube {v}. Её можно скачать в плеере."},
    "upd_download": {"en": "Download", "ro": "Descarcă", "ru": "Скачать"},
    "upd_later": {"en": "Later", "ro": "Mai târziu", "ru": "Позже"},
    "upd_downloading": {"en": "Downloading YukiTube {v}… {pct}%", "ro": "Descarc YukiTube {v}… {pct}%",
                        "ru": "Скачиваю YukiTube {v}… {pct}%"},
    "upd_cancel": {"en": "Cancel", "ro": "Anulează", "ru": "Отмена"},
    "upd_ready": {"en": "YukiTube {v} is downloaded", "ro": "YukiTube {v} e descărcat", "ru": "YukiTube {v} скачан"},
    "upd_ready_tip": {"en": "It is installed when YukiTube restarts, or at its next start.",
                      "ro": "Se instalează când repornești YukiTube, sau la următoarea pornire.",
                      "ru": "Он установится при перезапуске YukiTube или при следующем запуске."},
    "upd_retry_tip": {"en": "Last time it was not installed (no permission given?). Restart to try again.",
                      "ro": "Data trecută nu s-a instalat (nu s-a dat permisiunea?). Repornește ca să încerci din nou.",
                      "ru": "В прошлый раз установка не удалась (нет разрешения?). Перезапустите, чтобы повторить."},
    "upd_restart": {"en": "Restart now", "ro": "Repornește acum", "ru": "Перезапустить"},
    "upd_next_start": {"en": "At next start", "ro": "La următoarea pornire", "ru": "При следующем запуске"},
    "upd_dl_failed": {"en": "Download failed: {err}", "ro": "Descărcarea a eșuat: {err}",
                      "ru": "Загрузка не удалась: {err}"},
    "upd_retry": {"en": "Retry", "ro": "Reîncearcă", "ru": "Повторить"},
    "upd_open_page": {"en": "Open the page", "ro": "Deschide pagina", "ru": "Открыть страницу"},
    "upd_page_tip": {"en": "This copy of YukiTube cannot update itself; download the new version from GitHub.",
                     "ro": "Această copie YukiTube nu se poate actualiza singură; descarcă versiunea nouă de pe GitHub.",
                     "ru": "Эта копия YukiTube не обновляется сама; скачайте новую версию с GitHub."},
    "upd_restart_failed": {"en": "The update could not be started.", "ro": "Actualizarea nu a putut porni.",
                           "ru": "Не удалось запустить обновление."},

    # recommendations
    "recs_title": {"en": "MUSIC FOR YOU", "ro": "MUZICĂ PENTRU TINE", "ru": "МУЗЫКА ДЛЯ ВАС"},
    "recs_for_you": {"en": "from what you listened to lately · your Google account",
                     "ro": "după ce ai ascultat recent · contul tău Google",
                     "ru": "по тому, что вы недавно слушали · ваш аккаунт Google"},
    "recs_history": {"en": "mixes of what you play often", "ro": "mixuri după ce asculți des",
                     "ru": "миксы из того, что вы часто слушаете"},
    "recs_loading": {"en": "Looking for something you'll like…", "ro": "Caut ceva ce o să-ți placă…",
                     "ru": "Ищу то, что вам понравится…"},
    "recs_empty": {"en": "Play a few songs (or sign in with Google) and recommendations appear here.",
                   "ro": "Ascultă câteva melodii (sau conectează contul Google) și aici apar recomandări.",
                   "ru": "Послушайте несколько песен (или войдите в Google) — и здесь появятся рекомендации."},
    "recs_failed": {"en": "Recommendations could not be loaded.", "ro": "Recomandările nu s-au putut încărca.",
                    "ru": "Не удалось загрузить рекомендации."},
    "recs_more": {"en": "More music", "ro": "Altă muzică", "ru": "Другая музыка"},
}


def set_lang(code):
    global LANG
    LANG = code if code in LANGS else "en"


def T(key, **kw):
    entry = STRINGS[key]
    text = entry.get(LANG) or entry["en"]
    return text.format(**kw) if kw else text
