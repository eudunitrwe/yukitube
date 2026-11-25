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
    "language": {"en": "Language", "ro": "Limba", "ru": "Язык"},
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
        "en": "When you have signed in, close the YouTube window: YukiTube carries on in the player.",
        "ro": "După ce te autentifici, închide fereastra YouTube: YukiTube continuă în telecomandă.",
        "ru": "После входа закройте окно YouTube: YukiTube продолжит работу в плеере."},

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
}


def set_lang(code):
    global LANG
    LANG = code if code in LANGS else "en"


def T(key, **kw):
    entry = STRINGS[key]
    text = entry.get(LANG) or entry["en"]
    return text.format(**kw) if kw else text
