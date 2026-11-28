package com.yukitube.app.ui

import androidx.appcompat.app.AppCompatDelegate
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.basicMarquee
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.PlaylistPlay
import androidx.compose.material.icons.automirrored.rounded.QueueMusic
import androidx.compose.material.icons.rounded.AccountCircle
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material.icons.rounded.Fullscreen
import androidx.compose.material.icons.rounded.FullscreenExit
import androidx.compose.material.icons.rounded.OndemandVideo
import androidx.compose.material.icons.rounded.Pause
import androidx.compose.material.icons.rounded.PlayArrow
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Repeat
import androidx.compose.material.icons.rounded.RepeatOne
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material.icons.rounded.SkipNext
import androidx.compose.material.icons.rounded.SkipPrevious
import androidx.compose.material.icons.rounded.SystemUpdate
import androidx.compose.material.icons.rounded.ThumbUp
import androidx.compose.material.icons.rounded.ThumbUpOffAlt
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.ClipOp
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.boundsInRoot
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.os.LocaleListCompat
import coil.compose.AsyncImage
import com.yukitube.app.BuildConfig
import com.yukitube.app.Engine
import com.yukitube.app.Item
import com.yukitube.app.PlaybackService
import com.yukitube.app.PlayerState
import com.yukitube.app.R
import com.yukitube.app.fmtTime
import kotlinx.coroutines.delay

/** Where the page's WebView goes, in pixels of the window. */
data class WebPlace(val left: Int, val top: Int, val right: Int, val bottom: Int, val corner: Float, val front: Boolean)

private fun Rect.toPlace(corner: Float, front: Boolean) =
    WebPlace(left.toInt(), top.toInt(), right.toInt(), bottom.toInt(), corner, front)

@Composable
fun YukiScreen(ui: UiModel, engine: Engine, placeWeb: (WebPlace) -> Unit) {
    val skin = LocalSkin.current
    val state by engine.state.collectAsState()
    val ready by engine.ready.collectAsState()
    val signingIn by engine.signingIn.collectAsState()
    // The video box: the page shows through this hole in the background.
    var hole by remember { mutableStateOf(Rect.Zero) }
    val showHole = ui.videoMode && state.id.isNotEmpty() && !signingIn && !ui.fullScreen

    LaunchedEffect(ready) { if (ready && ui.recs is Load.Idle) ui.loadRecs() }

    if (ui.fullScreen && !signingIn) {
        FullScreenVideo(ui, engine, state, placeWeb)
        return
    }

    Box(
        Modifier
            .fillMaxSize()
            .drawBehind {
                val brush = Brush.verticalGradient(listOf(skin.bg, skin.bg2))
                if (showHole && hole != Rect.Zero) {
                    clipRect(hole.left, hole.top, hole.right, hole.bottom, ClipOp.Difference) { drawRect(brush) }
                } else drawRect(brush)
            },
    ) {
        Column(Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing)) {
            TopBar(ui, engine, state, ready)
            if (signingIn) {
                SignInBar(engine)
                Box(
                    Modifier.fillMaxSize().onGloballyPositioned { placeWeb(it.boundsInRoot().toPlace(0f, true)) },
                )
                return@Column
            }
            BoxWithConstraints(Modifier.fillMaxSize()) {
                val half = maxWidth * 0.48f
                val wide = maxWidth > maxHeight && maxWidth > 600.dp
                if (wide) {
                    Row(Modifier.fillMaxSize()) {
                        Column(Modifier.width(half).fillMaxSize().padding(horizontal = 12.dp)) {
                            PlayerCard(ui, engine, state, ready, placeWeb) { hole = it }
                        }
                        Box(Modifier.weight(1f).fillMaxSize()) { Panel(ui, engine, state) }
                    }
                } else {
                    Column(Modifier.fillMaxSize()) {
                        Column(Modifier.padding(horizontal = 12.dp)) {
                            PlayerCard(ui, engine, state, ready, placeWeb) { hole = it }
                        }
                        Box(Modifier.weight(1f).fillMaxWidth().imePadding()) { Panel(ui, engine, state) }
                    }
                }
            }
        }
    }
}

// ----------------------------------------------------------------- top bar

@Composable
private fun TopBar(ui: UiModel, engine: Engine, state: PlayerState, ready: Boolean) {
    val skin = LocalSkin.current
    var accountMenu by remember { mutableStateOf(false) }
    Column {
        Row(
            Modifier.fillMaxWidth().padding(start = 12.dp, end = 4.dp, top = 6.dp, bottom = 2.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            androidx.compose.foundation.Image(
                painterResource(R.drawable.logo), null,
                Modifier.size(30.dp).clip(RoundedCornerShape(8.dp)),
            )
            Spacer(Modifier.width(8.dp))
            Text(
                "YukiTube",
                color = skin.text,
                fontWeight = FontWeight.Bold,
                fontSize = 20.sp,
                style = if (skin.glow) TextStyle(shadow = Shadow(skin.accent, Offset.Zero, 18f)) else TextStyle.Default,
            )
            if (!ready) {
                Spacer(Modifier.width(8.dp))
                CircularProgressIndicator(Modifier.size(14.dp), color = skin.accent2, strokeWidth = 2.dp)
            }
            Spacer(Modifier.weight(1f))
            TopIcon(Icons.Rounded.Search, stringResource(R.string.search), ui.tab == Tab.SEARCH) {
                ui.tab = if (ui.tab == Tab.SEARCH) Tab.HOME else Tab.SEARCH
            }
            TopIcon(Icons.AutoMirrored.Rounded.QueueMusic, stringResource(R.string.playlists), ui.tab == Tab.LISTS) {
                if (ui.tab == Tab.LISTS) ui.tab = Tab.HOME else {
                    ui.tab = Tab.LISTS
                    if (ui.lists is Load.Idle) ui.loadLists(state.loggedIn == true)
                }
            }
            TopIcon(Icons.AutoMirrored.Rounded.PlaylistPlay, stringResource(R.string.queue), ui.tab == Tab.QUEUE) {
                if (ui.tab == Tab.QUEUE) ui.tab = Tab.HOME else { ui.tab = Tab.QUEUE; ui.loadQueue() }
            }
            TopIcon(Icons.Rounded.OndemandVideo, stringResource(R.string.video_mode), ui.videoMode) {
                ui.videoMode = !ui.videoMode
            }
            Box {
                if (state.loggedIn == true && state.avatar.isNotEmpty()) {
                    AsyncImage(
                        state.avatar, stringResource(R.string.account_signed_in),
                        Modifier.padding(6.dp).size(28.dp).clip(CircleShape).clickable { accountMenu = true },
                    )
                } else {
                    TopIcon(Icons.Rounded.AccountCircle,
                        stringResource(if (state.loggedIn == true) R.string.account_signed_in else R.string.account_signin),
                        state.loggedIn == true) {
                        if (state.loggedIn == true) accountMenu = true else engine.signIn()
                    }
                }
                DropdownMenu(accountMenu, { accountMenu = false }) {
                    DropdownMenuItem(
                        text = { Text(stringResource(R.string.sign_out)) },
                        onClick = { accountMenu = false; engine.signOut(); ui.recs = Load.Idle; ui.lists = Load.Idle },
                    )
                }
            }
            Box {
                TopIcon(Icons.Rounded.Settings, stringResource(R.string.settings), ui.tab == Tab.SETTINGS) {
                    ui.tab = if (ui.tab == Tab.SETTINGS) Tab.HOME else Tab.SETTINGS
                }
                if (ui.update != null) {
                    Box(Modifier.align(Alignment.TopEnd).padding(8.dp).size(8.dp).background(skin.accent2, CircleShape))
                }
            }
        }
        // The band along the top, in the skin's two accents.
        Box(
            Modifier.fillMaxWidth().height(2.dp)
                .background(Brush.horizontalGradient(listOf(skin.accent, skin.accent2))),
        )
    }
}

@Composable
private fun TopIcon(icon: ImageVector, desc: String, on: Boolean, onClick: () -> Unit) {
    val skin = LocalSkin.current
    Box(
        Modifier.size(40.dp).clip(CircleShape).clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(icon, desc, tint = if (on) skin.accent else skin.muted, modifier = Modifier.size(24.dp))
    }
}

@Composable
private fun SignInBar(engine: Engine) {
    val skin = LocalSkin.current
    Row(Modifier.fillMaxWidth().padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(stringResource(R.string.signin_title), color = skin.text, fontSize = 14.sp, modifier = Modifier.weight(1f))
        TextButton(onClick = { engine.cancelSignIn() }) { Text(stringResource(R.string.close), color = skin.accent) }
    }
}

// ------------------------------------------------------------------ player

@Composable
private fun PlayerCard(
    ui: UiModel, engine: Engine, state: PlayerState, ready: Boolean,
    placeWeb: (WebPlace) -> Unit, onHole: (Rect) -> Unit,
) {
    val skin = LocalSkin.current
    val density = LocalDensity.current
    val corner = with(density) { skin.radius.toPx() }
    val shape = RoundedCornerShape(skin.radius)
    val video = ui.videoMode && state.id.isNotEmpty()
    var now by remember { mutableLongStateOf(System.currentTimeMillis()) }
    LaunchedEffect(state.paused, state.id) {
        while (!state.paused) { delay(500); now = System.currentTimeMillis() }
    }

    Spacer(Modifier.height(10.dp))
    // The cover art; in video mode a hole the page's video shows through.
    Box(
        Modifier
            .fillMaxWidth()
            .aspectRatio(16f / 9f)
            .onGloballyPositioned {
                val r = it.boundsInRoot()
                onHole(r)
                placeWeb(r.toPlace(corner, false))
            }
            .then(if (video) Modifier else Modifier.shadowGlow(skin, shape).clip(shape).background(skin.card))
            .pointerInput(video) {
                detectTapGestures(
                    onTap = { if (video) engine.toggle() },
                    onDoubleTap = { if (video) ui.fullScreen = true },
                )
            },
    ) {
        if (!video) {
            if (state.id.isNotEmpty()) {
                AsyncImage(state.thumb, null, Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            } else {
                androidx.compose.foundation.Image(
                    painterResource(R.drawable.logo), null,
                    Modifier.fillMaxSize(), contentScale = ContentScale.Crop, alpha = 0.55f,
                )
            }
        } else {
            Box(
                Modifier.align(Alignment.BottomEnd).padding(6.dp).size(36.dp)
                    .background(Color(0x88000000), CircleShape).clickable { ui.fullScreen = true },
                contentAlignment = Alignment.Center,
            ) { Icon(Icons.Rounded.Fullscreen, stringResource(R.string.full_screen), tint = Color.White) }
        }
        if (state.ad) {
            Text(
                stringResource(R.string.ad), color = Color.White, fontSize = 12.sp,
                modifier = Modifier.align(Alignment.TopStart).padding(6.dp)
                    .background(Color(0xAA000000), RoundedCornerShape(6.dp)).padding(horizontal = 6.dp, vertical = 2.dp),
            )
        }
    }

    Spacer(Modifier.height(10.dp))
    Text(
        state.title.ifEmpty { stringResource(if (ready) R.string.nothing_playing else R.string.starting) },
        color = skin.text, fontSize = 17.sp, fontWeight = FontWeight.SemiBold, maxLines = 1,
        modifier = Modifier.fillMaxWidth().basicMarquee(),
        style = if (skin.glow) TextStyle(shadow = Shadow(skin.accent.copy(alpha = 0.7f), Offset.Zero, 12f)) else TextStyle.Default,
    )
    Text(
        state.channel.ifEmpty { if (state.id.isEmpty()) stringResource(R.string.nothing_hint) else "" },
        color = skin.muted, fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
    )
    state.next?.let { nx ->
        if (nx.title.isNotEmpty()) {
            Text(
                stringResource(R.string.up_next, nx.title), color = skin.accent2, fontSize = 12.sp, maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(top = 2.dp).clickable { engine.cmd("next") },
            )
        }
    }

    // seek bar
    var dragging by remember { mutableStateOf(false) }
    var dragVal by remember { mutableFloatStateOf(0f) }
    val dur = state.duration.toFloat().coerceAtLeast(0f)
    // (reads `now`, so the position moves on while playing)
    val pos = if (dragging) dragVal else now.let { state.timeNow() }.toFloat().coerceIn(0f, dur.coerceAtLeast(0.01f))
    Slider(
        value = if (dur > 0) pos else 0f,
        onValueChange = { dragging = true; dragVal = it },
        onValueChangeFinished = { engine.seek(dragVal.toDouble()); dragging = false },
        valueRange = 0f..(if (dur > 0) dur else 1f),
        enabled = dur > 0,
        colors = SliderDefaults.colors(
            thumbColor = skin.accent, activeTrackColor = skin.accent, inactiveTrackColor = skin.line,
            disabledInactiveTrackColor = skin.line,
        ),
        modifier = Modifier.height(28.dp),
    )
    Row(Modifier.fillMaxWidth()) {
        Text(fmtTime(pos.toDouble()), color = skin.muted, fontSize = 11.sp)
        Spacer(Modifier.weight(1f))
        Text(if (dur > 0) fmtTime(dur.toDouble()) else "", color = skin.muted, fontSize = 11.sp)
    }

    // controls
    Row(
        Modifier.fillMaxWidth().padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceEvenly,
    ) {
        CtrlIcon(if (state.loop) Icons.Rounded.RepeatOne else Icons.Rounded.Repeat, stringResource(R.string.loop), state.loop) {
            engine.cmd("loop")
        }
        CtrlIcon(Icons.Rounded.SkipPrevious, stringResource(R.string.prev), false, 34) { engine.cmd("prev") }
        Box(
            Modifier.size(62.dp).shadowGlow(skin, CircleShape).clip(CircleShape)
                .background(Brush.linearGradient(listOf(skin.accent, if (skin.glow) skin.accent2 else skin.accent)))
                .clickable { engine.toggle() },
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                if (state.paused) Icons.Rounded.PlayArrow else Icons.Rounded.Pause,
                stringResource(if (state.paused) R.string.play else R.string.pause),
                tint = skin.onAccent, modifier = Modifier.size(38.dp),
            )
        }
        CtrlIcon(Icons.Rounded.SkipNext, stringResource(R.string.next), false, 34) { engine.cmd("next") }
        if (state.liked != null) {
            CtrlIcon(if (state.liked) Icons.Rounded.ThumbUp else Icons.Rounded.ThumbUpOffAlt, stringResource(R.string.like),
                state.liked) { engine.cmd("like") }
        } else {
            SpeedChip(state) { engine.cmd("rate", it) }
        }
    }
}

private fun Modifier.shadowGlow(skin: Skin, shape: androidx.compose.ui.graphics.Shape): Modifier =
    if (skin.glow) this.shadow(14.dp, shape, ambientColor = skin.accent, spotColor = skin.accent) else this

@Composable
private fun CtrlIcon(icon: ImageVector, desc: String, on: Boolean, size: Int = 26, onClick: () -> Unit) {
    val skin = LocalSkin.current
    Box(Modifier.size(48.dp).clip(CircleShape).clickable(onClick = onClick), contentAlignment = Alignment.Center) {
        Icon(icon, desc, tint = if (on) skin.accent else skin.text, modifier = Modifier.size(size.dp))
    }
}

@Composable
private fun SpeedChip(state: PlayerState, set: (Double) -> Unit) {
    val skin = LocalSkin.current
    val speeds = listOf(0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
    val label = (if (state.rate % 1.0 == 0.0) state.rate.toInt().toString() else state.rate.toString()) + "×"
    Box(
        Modifier.size(48.dp).clip(CircleShape).clickable {
            val i = speeds.indexOfFirst { it >= state.rate - 0.01 }.let { if (it < 0) 2 else it }
            set(speeds[(i + 1) % speeds.size])
        },
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color = if (state.rate != 1.0) skin.accent else skin.text, fontSize = 14.sp, fontWeight = FontWeight.Bold)
    }
}

// ------------------------------------------------------------- full screen

@Composable
private fun FullScreenVideo(ui: UiModel, engine: Engine, state: PlayerState, placeWeb: (WebPlace) -> Unit) {
    var controls by remember { mutableStateOf(true) }
    LaunchedEffect(controls, state.paused) {
        if (controls && !state.paused) { delay(3000); controls = false }
    }
    Box(
        Modifier.fillMaxSize()
            .onGloballyPositioned { placeWeb(it.boundsInRoot().toPlace(0f, false)) }
            .pointerInput(Unit) {
                detectTapGestures(onTap = { controls = !controls }, onDoubleTap = { ui.fullScreen = false })
            },
    ) {
        AnimatedVisibility(controls, enter = fadeIn(), exit = fadeOut(), modifier = Modifier.fillMaxSize()) {
            Box(Modifier.fillMaxSize().background(Color(0x55000000))) {
                Text(
                    state.title, color = Color.White, fontSize = 16.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.align(Alignment.TopStart).padding(20.dp).widthIn(max = 600.dp),
                )
                Row(Modifier.align(Alignment.Center), verticalAlignment = Alignment.CenterVertically) {
                    FsIcon(Icons.Rounded.SkipPrevious, 40) { engine.cmd("prev") }
                    Spacer(Modifier.width(24.dp))
                    FsIcon(if (state.paused) Icons.Rounded.PlayArrow else Icons.Rounded.Pause, 56) { engine.toggle() }
                    Spacer(Modifier.width(24.dp))
                    FsIcon(Icons.Rounded.SkipNext, 40) { engine.cmd("next") }
                }
                Box(Modifier.align(Alignment.BottomEnd).padding(16.dp)) {
                    FsIcon(Icons.Rounded.FullscreenExit, 32) { ui.fullScreen = false }
                }
            }
        }
    }
}

@Composable
private fun FsIcon(icon: ImageVector, size: Int, onClick: () -> Unit) {
    Box(
        Modifier.size((size + 24).dp).clip(CircleShape).background(Color(0x66000000)).clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) { Icon(icon, null, tint = Color.White, modifier = Modifier.size(size.dp)) }
}

// ------------------------------------------------------------------ panels

@Composable
private fun Panel(ui: UiModel, engine: Engine, state: PlayerState) {
    when (ui.tab) {
        Tab.HOME -> ItemList(
            header = { SectionHeader(stringResource(R.string.music_for_you)) { ui.recs = Load.Idle; ui.loadRecs() } },
            load = ui.recs, onRetry = { ui.loadRecs() }, current = state.id,
        ) { _, it -> engine.play(it) }
        Tab.SEARCH -> SearchPanel(ui, engine, state)
        Tab.LISTS -> ListsPanel(ui, engine, state)
        Tab.QUEUE -> QueuePanel(ui, engine, state)
        Tab.SETTINGS -> SettingsPanel(ui)
    }
}

@Composable
private fun SectionHeader(title: String, onReload: (() -> Unit)? = null) {
    val skin = LocalSkin.current
    Row(Modifier.fillMaxWidth().padding(start = 16.dp, end = 4.dp, top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(title, color = skin.accent2, fontSize = 12.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.5.sp,
            modifier = Modifier.weight(1f))
        if (onReload != null) {
            Box(Modifier.size(36.dp).clip(CircleShape).clickable { onReload() }, contentAlignment = Alignment.Center) {
                Icon(Icons.Rounded.Refresh, stringResource(R.string.reload), tint = skin.muted, modifier = Modifier.size(20.dp))
            }
        }
    }
}

@Composable
private fun ItemList(
    header: @Composable () -> Unit,
    load: Load<List<Item>>,
    onRetry: () -> Unit,
    current: String,
    extra: (LazyListScope.() -> Unit)? = null,
    trailing: (@Composable (Item) -> Unit)? = null,
    onClick: (Int, Item) -> Unit,
) {
    Column(Modifier.fillMaxSize()) {
        header()
        when (load) {
            is Load.Idle, is Load.Loading -> Centered { CircularProgressIndicator(color = LocalSkin.current.accent) }
            is Load.Failed -> Centered { ErrorText(load.msg, onRetry) }
            is Load.Done -> {
                if (load.v.isEmpty()) Centered { Text(stringResource(R.string.empty), color = LocalSkin.current.muted) }
                else LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 16.dp)) {
                    extra?.invoke(this)
                    itemsIndexed(load.v, key = { i, it -> "$i-${it.id}-${it.list}" }) { i, it ->
                        ItemRow(it, playing = it.id.isNotEmpty() && it.id == current && it.list.isEmpty(),
                            trailing = trailing) { onClick(i, it) }
                    }
                }
            }
        }
    }
}

@Composable
private fun ColumnScope.Centered(content: @Composable () -> Unit) {
    Box(Modifier.fillMaxWidth().weight(1f).padding(24.dp), contentAlignment = Alignment.Center) { content() }
}

@Composable
private fun ErrorText(msg: String, onRetry: () -> Unit) {
    val skin = LocalSkin.current
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(stringResource(R.string.error, msg), color = skin.muted, fontSize = 13.sp)
        TextButton(onClick = onRetry) { Text(stringResource(R.string.reload), color = skin.accent) }
    }
}

@Composable
private fun ItemRow(it: Item, playing: Boolean, label: String = "", trailing: (@Composable (Item) -> Unit)? = null, onClick: () -> Unit) {
    val skin = LocalSkin.current
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onClick)
            .background(if (playing) skin.accent.copy(alpha = 0.14f) else Color.Transparent)
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.width(96.dp).aspectRatio(16f / 9f).clip(RoundedCornerShape(skin.radius / 2)).background(skin.card)) {
            if (it.thumb.isNotEmpty()) AsyncImage(it.thumb, null, Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            if (it.duration.isNotEmpty()) {
                Text(
                    it.duration, color = Color.White, fontSize = 10.sp,
                    modifier = Modifier.align(Alignment.BottomEnd).padding(3.dp)
                        .background(Color(0xCC000000), RoundedCornerShape(3.dp)).padding(horizontal = 3.dp),
                )
            }
        }
        Spacer(Modifier.width(10.dp))
        Column(Modifier.weight(1f)) {
            if (label.isNotEmpty()) Text(label.uppercase(), color = skin.accent2, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            Text(it.title, color = if (playing) skin.accent else skin.text, fontSize = 14.sp, maxLines = 2,
                overflow = TextOverflow.Ellipsis)
            val sub = listOf(it.channel, it.views).filter { s -> s.isNotEmpty() }.joinToString(" · ")
            if (sub.isNotEmpty()) Text(sub, color = skin.muted, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        trailing?.invoke(it)
    }
}

@Composable
private fun SearchPanel(ui: UiModel, engine: Engine, state: PlayerState) {
    val skin = LocalSkin.current
    val focus = remember { FocusRequester() }
    val kb = LocalSoftwareKeyboardController.current
    LaunchedEffect(Unit) { if (ui.results is Load.Idle) focus.requestFocus() }
    Column(Modifier.fillMaxSize()) {
        OutlinedTextField(
            value = ui.query,
            onValueChange = { ui.query = it },
            placeholder = { Text(stringResource(R.string.search_hint)) },
            singleLine = true,
            leadingIcon = { Icon(Icons.Rounded.Search, null) },
            trailingIcon = {
                if (ui.query.isNotEmpty()) {
                    Icon(Icons.Rounded.Close, stringResource(R.string.close), Modifier.clickable { ui.query = "" })
                }
            },
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
            keyboardActions = KeyboardActions(onSearch = { kb?.hide(); ui.search(ui.query) }),
            shape = RoundedCornerShape(skin.radius),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = skin.accent, unfocusedBorderColor = skin.line, cursorColor = skin.accent,
                focusedTextColor = skin.text, unfocusedTextColor = skin.text,
                focusedContainerColor = skin.card, unfocusedContainerColor = skin.card,
                focusedLeadingIconColor = skin.accent, unfocusedLeadingIconColor = skin.muted,
            ),
            modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp).focusRequester(focus),
        )
        if (ui.results !is Load.Idle) {
            ItemList({ SectionHeader(stringResource(R.string.results)) }, ui.results, { ui.search(ui.query) }, state.id) { _, it ->
                kb?.hide()
                engine.play(it)
            }
        }
    }
}

@Composable
private fun ListsPanel(ui: UiModel, engine: Engine, state: PlayerState) {
    val skin = LocalSkin.current
    val opened = ui.openedList
    if (opened != null) {
        ItemList(
            header = {
                Row(Modifier.fillMaxWidth().padding(horizontal = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                    TextButton(onClick = { ui.openedList = null }) {
                        Icon(Icons.AutoMirrored.Rounded.ArrowBack, null, tint = skin.accent2, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(4.dp))
                        Text(stringResource(R.string.lists_back), color = skin.accent2, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                    Spacer(Modifier.weight(1f))
                    TextButton(onClick = { engine.play(opened) }) {
                        Icon(Icons.Rounded.PlayArrow, null, tint = skin.accent, modifier = Modifier.size(18.dp))
                        Text(stringResource(R.string.play_all), color = skin.accent)
                    }
                }
                Text(opened.title, color = skin.text, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(horizontal = 16.dp))
            },
            load = ui.listItems, onRetry = { ui.openList(opened) }, current = state.id,
        ) { i, it -> engine.playInList(opened.list, it, i) }
        return
    }
    Column(Modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Chip(stringResource(R.string.lists_suggested), !ui.listsMine) { ui.loadLists(false) }
            Chip(stringResource(R.string.lists_mine), ui.listsMine) { ui.loadLists(true) }
            Spacer(Modifier.weight(1f))
            Box(Modifier.size(32.dp).clip(CircleShape).clickable { ui.loadLists(ui.listsMine) }, contentAlignment = Alignment.Center) {
                Icon(Icons.Rounded.Refresh, stringResource(R.string.reload), tint = skin.muted, modifier = Modifier.size(20.dp))
            }
        }
        if (ui.listsMine && state.loggedIn != true) {
            Column(Modifier.fillMaxWidth().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                Text(stringResource(R.string.lists_signin), color = skin.muted)
                TextButton(onClick = { engine.signIn() }) { Text(stringResource(R.string.account_signin), color = skin.accent) }
            }
            return
        }
        ItemList(
            header = {}, load = ui.lists, onRetry = { ui.loadLists(ui.listsMine) }, current = "",
            trailing = { pl ->
                Box(Modifier.size(40.dp).clip(CircleShape).clickable { ui.openList(pl) }, contentAlignment = Alignment.Center) {
                    Icon(Icons.AutoMirrored.Rounded.QueueMusic, stringResource(R.string.songs), tint = skin.accent2)
                }
            },
        ) { _, it -> engine.play(it) }
    }
}

@Composable
private fun Chip(text: String, on: Boolean, onClick: () -> Unit) {
    val skin = LocalSkin.current
    Text(
        text, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp,
        color = if (on) skin.onAccent else skin.muted,
        modifier = Modifier.clip(RoundedCornerShape(50)).background(if (on) skin.accent else Color.Transparent)
            .border(1.dp, if (on) skin.accent else skin.line, RoundedCornerShape(50))
            .clickable(onClick = onClick).padding(horizontal = 12.dp, vertical = 6.dp),
    )
}

@Composable
private fun QueuePanel(ui: UiModel, engine: Engine, state: PlayerState) {
    val skin = LocalSkin.current
    // The queue follows the song playing.
    LaunchedEffect(state.id) { if (state.id.isNotEmpty() && ui.queue !is Load.Loading) ui.loadQueue() }
    val q = ui.queue
    val listState = rememberLazyListState()
    Column(Modifier.fillMaxSize()) {
        SectionHeader(stringResource(R.string.queue).uppercase()) { ui.loadQueue() }
        when (q) {
            is Load.Idle, is Load.Loading -> Centered { CircularProgressIndicator(color = skin.accent) }
            is Load.Failed -> Centered {
                if (state.id.isEmpty()) Text(stringResource(R.string.queue_empty), color = skin.muted)
                else ErrorText(q.msg) { ui.loadQueue() }
            }
            is Load.Done -> {
                LaunchedEffect(q) { if (q.v.index > 0) listState.scrollToItem((q.v.index - 1).coerceAtLeast(0)) }
                if (q.v.items.isEmpty()) Centered { Text(stringResource(R.string.queue_empty), color = skin.muted) }
                else LazyColumn(Modifier.fillMaxSize(), state = listState, contentPadding = PaddingValues(bottom = 16.dp)) {
                    itemsIndexed(q.v.items, key = { i, it -> "$i-${it.id}" }) { i, it ->
                        val now = i == q.v.index
                        ItemRow(
                            it, playing = now,
                            label = when {
                                now -> stringResource(R.string.queue_now)
                                it.upNext || (q.v.list.isNotEmpty() && i == q.v.index + 1) -> stringResource(R.string.queue_next)
                                else -> ""
                            },
                        ) {
                            if (q.v.list.isNotEmpty()) engine.playInList(q.v.list, it, i) else engine.play(it)
                        }
                    }
                }
            }
        }
    }
}

@OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
@Composable
private fun SettingsPanel(ui: UiModel) {
    val skin = LocalSkin.current
    val ctx = LocalContext.current
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp)) {
        item {
            Label(stringResource(R.string.skin))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                SKINS.forEach { s ->
                    Row(
                        Modifier.clip(RoundedCornerShape(50)).background(s.bg)
                            .border(2.dp, if (s.key == skin.key) s.accent else s.line, RoundedCornerShape(50))
                            .clickable { ui.chooseSkin(s) }.padding(horizontal = 12.dp, vertical = 7.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Box(Modifier.size(10.dp).background(s.accent, CircleShape))
                        Spacer(Modifier.width(3.dp))
                        Box(Modifier.size(10.dp).background(s.accent2, CircleShape))
                        Spacer(Modifier.width(7.dp))
                        Text(s.name, color = s.text, fontSize = 13.sp)
                    }
                }
            }
            Spacer(Modifier.height(20.dp))

            Label(stringResource(R.string.language))
            val cur = AppCompatDelegate.getApplicationLocales().toLanguageTags().substringBefore("-")
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("" to stringResource(R.string.lang_system), "en" to "English", "ro" to "Română", "ru" to "Русский")
                    .forEach { (tag, name) ->
                        Chip(name, cur == tag) {
                            AppCompatDelegate.setApplicationLocales(
                                if (tag.isEmpty()) LocaleListCompat.getEmptyLocaleList() else LocaleListCompat.forLanguageTags(tag),
                            )
                        }
                    }
            }
            Spacer(Modifier.height(20.dp))

            Label(stringResource(R.string.updates))
            Text(stringResource(R.string.version, BuildConfig.VERSION_NAME), color = skin.text, fontSize = 14.sp)
            val up = ui.update
            if (up != null) {
                Text(stringResource(R.string.update_available, up.version), color = skin.accent2, fontSize = 14.sp)
            }
            val msg = ui.updateMsg
            when {
                msg == "up_to_date" -> Text(stringResource(R.string.up_to_date), color = skin.muted, fontSize = 13.sp)
                msg == "perm" -> Text(stringResource(R.string.update_install_perm), color = skin.muted, fontSize = 13.sp)
                msg.startsWith("!") -> Text(stringResource(R.string.update_failed, msg.drop(1)), color = skin.muted, fontSize = 13.sp)
            }
            if (ui.updateProgress >= 0) {
                Text(stringResource(R.string.downloading, ui.updateProgress), color = skin.muted, fontSize = 13.sp)
                LinearProgressIndicator(
                    progress = { ui.updateProgress / 100f }, color = skin.accent, trackColor = skin.line,
                    modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 6.dp)) {
                Chip(stringResource(R.string.check_now), false) { ui.checkUpdate(quiet = false) }
                if (up != null) {
                    Row(
                        Modifier.clip(RoundedCornerShape(50)).background(skin.accent).clickable { ui.installUpdate(ctx) }
                            .padding(horizontal = 12.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(Icons.Rounded.SystemUpdate, null, tint = skin.onAccent, modifier = Modifier.size(14.dp))
                        Spacer(Modifier.width(4.dp))
                        Text(stringResource(R.string.update_now), color = skin.onAccent, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
            Spacer(Modifier.height(24.dp))

            Text(stringResource(R.string.background_hint), color = skin.muted, fontSize = 13.sp)
            Spacer(Modifier.height(10.dp))
            Chip(stringResource(R.string.exit), false) { PlaybackService.quit(ctx) }
            Spacer(Modifier.height(24.dp))
            Text(stringResource(R.string.credit), color = skin.muted, fontSize = 12.sp)
        }
    }
}

@Composable
private fun Label(text: String) {
    val skin = LocalSkin.current
    Text(text.uppercase(), color = skin.accent2, fontSize = 12.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.5.sp,
        modifier = Modifier.padding(bottom = 8.dp))
}
