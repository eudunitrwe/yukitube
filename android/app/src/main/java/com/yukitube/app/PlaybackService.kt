package com.yukitube.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.graphics.Bitmap
import android.media.AudioManager
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.support.v4.media.MediaMetadataCompat
import android.support.v4.media.session.MediaSessionCompat
import android.support.v4.media.session.PlaybackStateCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import androidx.core.content.ContextCompat
import androidx.media.session.MediaButtonReceiver
import coil.imageLoader
import coil.request.ImageRequest
import coil.request.SuccessResult
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import androidx.media.app.NotificationCompat as MediaNotificationCompat

/**
 * Keeps YukiTube playing in the background: the media notification, the
 * lock-screen and headset controls, headphones unplugged = pause.
 */
class PlaybackService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private lateinit var session: MediaSessionCompat
    private var art: Bitmap? = null
    private var artId = ""
    private var last = PlayerState()
    private var wake: PowerManager.WakeLock? = null
    private val engine get() = YukiApp.engine

    private val noisy = object : BroadcastReceiver() {
        override fun onReceive(c: Context, i: Intent) {
            if (i.action == AudioManager.ACTION_AUDIO_BECOMING_NOISY) engine.cmd("pause")
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL, getString(R.string.notif_channel), NotificationManager.IMPORTANCE_LOW).apply {
                setShowBadge(false)
            },
        )
        session = MediaSessionCompat(this, "YukiTube").apply {
            setCallback(object : MediaSessionCompat.Callback() {
                override fun onPlay() = engine.cmd("play")
                override fun onPause() = engine.cmd("pause")
                override fun onSkipToNext() = engine.cmd("next")
                override fun onSkipToPrevious() = engine.cmd("prev")
                override fun onSeekTo(pos: Long) = engine.seek(pos / 1000.0)
                override fun onStop() = quit(this@PlaybackService)
            })
            setSessionActivity(openApp())
            isActive = true
        }
        startForegroundNow()
        ContextCompat.registerReceiver(this, noisy, IntentFilter(AudioManager.ACTION_AUDIO_BECOMING_NOISY),
            ContextCompat.RECEIVER_NOT_EXPORTED)
        scope.launch { engine.state.collect { update(it) } }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_QUIT) {
            quit(this)
            return START_NOT_STICKY
        }
        MediaButtonReceiver.handleIntent(session, intent)
        return START_NOT_STICKY
    }

    /** Swiping YukiTube away from the recent apps quits it. */
    override fun onTaskRemoved(rootIntent: Intent?) {
        quit(this)
    }

    override fun onDestroy() {
        scope.cancel()
        try { unregisterReceiver(noisy) } catch (e: Exception) {}
        wake?.let { if (it.isHeld) it.release() }
        session.isActive = false
        session.release()
        engine.serviceStopped()
        super.onDestroy()
    }

    private fun startForegroundNow() {
        val n = build(last)
        ServiceCompat.startForeground(this, NOTIF_ID, n,
            if (Build.VERSION.SDK_INT >= 29) ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK else 0)
    }

    private fun update(s: PlayerState) {
        val changed = s.id != last.id || s.title != last.title || s.paused != last.paused || s.channel != last.channel
        val seeked = kotlin.math.abs(s.time - last.timeNow()) > 2
        last = s
        holdWake(!s.paused)
        session.setMetadata(
            MediaMetadataCompat.Builder()
                .putString(MediaMetadataCompat.METADATA_KEY_TITLE, s.title)
                .putString(MediaMetadataCompat.METADATA_KEY_ARTIST, s.channel)
                .putLong(MediaMetadataCompat.METADATA_KEY_DURATION, (s.duration * 1000).toLong())
                .putBitmap(MediaMetadataCompat.METADATA_KEY_ALBUM_ART, if (artId == s.id) art else null)
                .build(),
        )
        if (changed || seeked) {
            session.setPlaybackState(
                PlaybackStateCompat.Builder()
                    .setActions(
                        PlaybackStateCompat.ACTION_PLAY or PlaybackStateCompat.ACTION_PAUSE or
                            PlaybackStateCompat.ACTION_PLAY_PAUSE or PlaybackStateCompat.ACTION_SKIP_TO_NEXT or
                            PlaybackStateCompat.ACTION_SKIP_TO_PREVIOUS or PlaybackStateCompat.ACTION_SEEK_TO or
                            PlaybackStateCompat.ACTION_STOP,
                    )
                    .setState(
                        if (s.paused) PlaybackStateCompat.STATE_PAUSED else PlaybackStateCompat.STATE_PLAYING,
                        (s.time * 1000).toLong(), if (s.paused) 0f else s.rate.toFloat(),
                    )
                    .build(),
            )
        }
        if (changed) {
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).notify(NOTIF_ID, build(s))
        }
        if (s.id.isNotEmpty() && s.id != artId) loadArt(s.id, s.thumb)
    }

    private fun loadArt(id: String, url: String) {
        artId = id
        art = null
        scope.launch {
            val r = imageLoader.execute(ImageRequest.Builder(this@PlaybackService).data(url).allowHardware(false).build())
            val b = ((r as? SuccessResult)?.drawable as? android.graphics.drawable.BitmapDrawable)?.bitmap
            if (b != null && artId == id) {
                art = b
                val s = last
                last = PlayerState() // forces the next update to redraw
                update(s)
            }
        }
    }

    private fun build(s: PlayerState): Notification {
        val playing = !s.paused
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_notif)
            .setContentTitle(s.title.ifEmpty { getString(R.string.app_name) })
            .setContentText(s.channel)
            .setLargeIcon(if (artId == s.id) art else null)
            .setContentIntent(openApp())
            .setDeleteIntent(MediaButtonReceiver.buildMediaButtonPendingIntent(this, PlaybackStateCompat.ACTION_STOP))
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setOnlyAlertOnce(true)
            .setOngoing(playing)
            .setSilent(true)
            .addAction(R.drawable.ic_prev, getString(R.string.prev),
                MediaButtonReceiver.buildMediaButtonPendingIntent(this, PlaybackStateCompat.ACTION_SKIP_TO_PREVIOUS))
            .addAction(
                if (playing) R.drawable.ic_pause else R.drawable.ic_play,
                getString(if (playing) R.string.pause else R.string.play),
                MediaButtonReceiver.buildMediaButtonPendingIntent(this, PlaybackStateCompat.ACTION_PLAY_PAUSE),
            )
            .addAction(R.drawable.ic_next, getString(R.string.next),
                MediaButtonReceiver.buildMediaButtonPendingIntent(this, PlaybackStateCompat.ACTION_SKIP_TO_NEXT))
            .addAction(R.drawable.ic_close, getString(R.string.exit), quitIntent())
            .setStyle(
                MediaNotificationCompat.MediaStyle()
                    .setMediaSession(session.sessionToken)
                    .setShowActionsInCompactView(0, 1, 2),
            )
            .build()
    }

    private fun openApp(): PendingIntent = PendingIntent.getActivity(
        this, 0, Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
        PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
    )

    private fun quitIntent(): PendingIntent = PendingIntent.getService(
        this, 1, Intent(this, PlaybackService::class.java).setAction(ACTION_QUIT),
        PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
    )

    // Audio focus: the page's own media session (Chromium) takes and gives it
    // back; a second request here would pause it.

    /** The CPU stays awake while something plays (the page decodes it). */
    private fun holdWake(on: Boolean) {
        val w = wake ?: (getSystemService(POWER_SERVICE) as PowerManager)
            .newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "YukiTube:playback").also {
                it.setReferenceCounted(false)
                wake = it
            }
        if (on && !w.isHeld) w.acquire(6 * 60 * 60 * 1000L)
        if (!on && w.isHeld) w.release()
    }

    companion object {
        private const val CHANNEL = "playback"
        private const val NOTIF_ID = 1
        const val ACTION_QUIT = "com.yukitube.app.QUIT"

        /** Quits YukiTube: the page stops, the service and the window close. */
        fun quit(ctx: Context) {
            YukiApp.engine.stopAll()
            MainActivity.finishAll()
            ctx.stopService(Intent(ctx, PlaybackService::class.java))
            // The page goes with it, like the desktop app's hidden player.
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(
                { android.os.Process.killProcess(android.os.Process.myPid()) }, 400)
        }
    }
}
