"""The YukiTube Firefox, run by the remote.

YukiTube is the remote: YouTube plays in a Firefox that runs headless (no
window at all) on YukiTube's own profile. A window is shown only when one is
needed, to sign in to Google or when asked for ("Arată YouTube"): Firefox
cannot switch between the two, so it is restarted, visible, on the page to
show, and when that window is closed, or hidden again, it goes back to
running headless.

On the first launch, and when the bridge has a new version, the profile gets
the bridge userscript first (see provision.py), in a thread, while the
remote already shows.
"""
import os
import shlex
import sys
import threading
import time

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal

import provision

HOME = "https://www.youtube.com/"


class FirefoxHost(QObject):
    state_changed = Signal()   # starting / running / visible changed
    prepared = Signal(bool)    # first-launch preparation finished (ok)

    def __init__(self, firefox, profile, userscript, parent=None):
        super().__init__(parent)
        self.firefox = firefox
        self.profile = profile
        self.userscript = userscript
        self.proc = None
        self.visible = False       # the running Firefox has a window
        self.preparing = False
        self._next = None          # (visible, url) to start once the current one is gone
        self._quitting = False
        self._fails = 0
        self._started_at = 0.0

    # ------------------------------------------------------------- public
    def running(self):
        return self.proc is not None and self.proc.state() != QProcess.NotRunning

    def start(self, url=None):
        """First start: prepares the profile if needed, then runs headless."""
        if provision.is_current(self.profile, self.userscript):
            self._launch(False, url)
            return
        self.preparing = True
        self.state_changed.emit()
        done = []

        def work():
            ok = provision.install_bridge(self.firefox, self.profile, self.userscript,
                                          log=lambda m: print("prepare:", m, file=sys.stderr))
            done.append(ok)

        t = threading.Thread(target=work, daemon=True)
        t.start()

        def poll():
            if t.is_alive():
                return
            timer.stop()
            self.preparing = False
            self.prepared.emit(bool(done and done[0]))
            self._launch(False, url)
        timer = QTimer(self)
        timer.timeout.connect(poll)
        timer.start(200)

    def show(self, url=None):
        """Restarts Firefox with a window, on `url`."""
        self._switch(True, url or HOME)

    def hide(self, url=None):
        """Back to headless, on `url` (to keep playing what was showing)."""
        self._switch(False, url or HOME)

    def navigate_headless(self, url):
        """Opens `url` in the hidden Firefox (when no bridge can)."""
        self._switch(self.visible, url)

    def stop(self):
        """On quitting the remote: Firefox goes too."""
        self._quitting = True
        self._next = None
        if self.running():
            self._terminate()
            self.proc.waitForFinished(5000)
            if self.running():
                self._kill(self.proc)
                self.proc.waitForFinished(2000)

    # ------------------------------------------------------------ private
    def _switch(self, visible, url):
        if self.preparing:
            return
        if not self.running():
            self._launch(visible, url)
            return
        self._next = (visible, url)
        self._terminate()

    @staticmethod
    def _kill(p):
        if provision.WIN:
            # The launcher waits for the browser (-wait-for-browser); both go.
            provision.win_kill_tree(p.processId())
        p.kill()

    def _terminate(self):
        p = self.proc
        if provision.WIN:
            # A headless Firefox has no window to close: it is ended at once.
            # A visible one gets a normal close first.
            provision.win_kill_tree(p.processId(), force=not self.visible)
        else:
            p.terminate()
        QTimer.singleShot(8000, lambda: self._kill(p) if p.state() != QProcess.NotRunning else None)

    def _free_profile(self):
        """A Firefox left over from a remote that did not exit cleanly still
        has the profile, and Firefox would refuse a second one ("already
        running"); it goes. On Linux its pid is in the lock."""
        if not provision.profile_in_use(self.profile):
            return
        if provision.WIN:
            provision.win_free_profile(self.profile)
            return
        lock = os.path.join(self.profile, "lock")
        try:
            pid = int(os.readlink(lock).rsplit("+", 1)[1])
            os.kill(pid, 15)
            for _ in range(50):
                time.sleep(0.1)
                os.kill(pid, 0)
        except (OSError, ValueError, IndexError):
            pass

    def _launch(self, visible, url):
        self._free_profile()
        args = provision.WIN_ARGS + ["--profile", self.profile]
        if visible:
            args = ["--name", "yukitube", "--class", "yukitube"] + args if sys.platform != "win32" else args
        else:
            args = ["--headless"] + args
        args += shlex.split(os.environ.get("YUKITUBE_FIREFOX_ARGS", ""))
        if url:
            args.append(url)
        p = QProcess(self)
        # The whole session environment (XDG_RUNTIME_DIR and the rest: without
        # it Firefox finds no PipeWire/PulseAudio and plays without sound). A
        # QProcess's own processEnvironment() is empty until set, and setting
        # one with only our variable would leave Firefox with nothing else.
        env = QProcessEnvironment.systemEnvironment()
        env.remove("MOZ_HEADLESS")
        # The Linux release's remote is a PyInstaller build, which points the
        # libraries at its own folder; Firefox needs the system's.
        if env.contains("LD_LIBRARY_PATH_ORIG"):
            env.insert("LD_LIBRARY_PATH", env.value("LD_LIBRARY_PATH_ORIG"))
        elif getattr(sys, "frozen", False):
            env.remove("LD_LIBRARY_PATH")
        # No crash reporter: the Windows build leaves it out.
        env.insert("MOZ_CRASHREPORTER_DISABLE", "1")
        p.setProcessEnvironment(env)
        p.setProgram(self.firefox)
        p.setArguments(args)
        p.setProcessChannelMode(QProcess.ForwardedErrorChannel)
        p.setStandardOutputFile(QProcess.nullDevice())
        p.finished.connect(lambda *_: self._on_finished(p))
        self.proc = p
        self.visible = visible
        self._started_at = time.monotonic()
        p.start()
        self.state_changed.emit()

    def _on_finished(self, p):
        if p is not self.proc:
            return
        was_visible = self.visible
        self.proc = None
        self.visible = False
        if self._quitting:
            return
        if self._next:
            nxt, self._next = self._next, None
            self._fails = 0
            self._launch(*nxt)
            return
        if was_visible:
            # The user closed the YouTube window: keep running, hidden.
            self._launch(False, HOME)
            return
        # The hidden Firefox stopped on its own: start it again, but not in a
        # tight loop if it keeps failing.
        self._fails = self._fails + 1 if time.monotonic() - self._started_at < 30 else 1
        if self._fails <= 3:
            QTimer.singleShot(2000 * self._fails, lambda: None if self.running() else self._launch(False, HOME))
        self.state_changed.emit()
