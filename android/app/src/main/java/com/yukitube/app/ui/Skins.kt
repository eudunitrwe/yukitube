package com.yukitube.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/** The desktop app's skins, in the same colors. */
data class Skin(
    val key: String,
    val name: String,
    val bg: Color,
    val bg2: Color,
    val card: Color,
    val line: Color,
    val text: Color,
    val muted: Color,
    val accent: Color,
    val accent2: Color,
    val onAccent: Color,
    val radius: Dp,
    /** Neon glow around the title and the play button. */
    val glow: Boolean = false,
    val light: Boolean = false,
)

private fun c(hex: String) = Color(android.graphics.Color.parseColor(hex))

val SKINS = listOf(
    Skin("retrowave", "Retrowave", c("#0e0220"), c("#1d0638"), c("#1c0638"), c("#4a1650"), c("#f6ecff"), c("#bfa3e0"),
        c("#ff2a6d"), c("#05d9e8"), c("#ffffff"), 18.dp, glow = true),
    Skin("classic", "Classic 90s", c("#3b3d4a"), c("#23242c"), c("#070c07"), c("#6b6e80"), c("#22ff22"), c("#a7aac2"),
        c("#e8c547"), c("#3cff3c"), c("#000000"), 4.dp),
    Skin("win11_light", "Windows 11 Light", c("#f3f3f3"), c("#eeeeee"), c("#ffffff"), c("#dcdcdc"), c("#1b1b1b"), c("#5d5d5d"),
        c("#005fb8"), c("#0067c0"), c("#ffffff"), 8.dp, light = true),
    Skin("win11_dark", "Windows 11 Dark", c("#202020"), c("#1c1c1c"), c("#2d2d2d"), c("#3a3a3a"), c("#ffffff"), c("#c5c5c5"),
        c("#4cc2ff"), c("#99ebff"), c("#000000"), 8.dp),
    Skin("nord", "Nord", c("#323a48"), c("#2a303c"), c("#3b4252"), c("#434c5e"), c("#eceff4"), c("#a4afc2"),
        c("#88c0d0"), c("#8fbcbb"), c("#2e3440"), 12.dp),
    Skin("arch_d", "Arch_D", c("#2d353b"), c("#272e33"), c("#343f44"), c("#475258"), c("#d3c6aa"), c("#9da9a0"),
        c("#a7c080"), c("#83c092"), c("#232a2e"), 10.dp),
)

fun skinOf(key: String) = SKINS.firstOrNull { it.key == key } ?: SKINS[0]

val LocalSkin = staticCompositionLocalOf { SKINS[0] }

@Composable
fun YukiTheme(skin: Skin, content: @Composable () -> Unit) {
    val scheme = if (skin.light) {
        lightColorScheme(
            primary = skin.accent, onPrimary = skin.onAccent, secondary = skin.accent2, background = skin.bg,
            surface = skin.card, onSurface = skin.text, onBackground = skin.text, surfaceVariant = skin.card,
            onSurfaceVariant = skin.muted, outline = skin.line, surfaceContainerHighest = skin.card,
        )
    } else {
        darkColorScheme(
            primary = skin.accent, onPrimary = skin.onAccent, secondary = skin.accent2, background = skin.bg,
            surface = skin.card, onSurface = skin.text, onBackground = skin.text, surfaceVariant = skin.card,
            onSurfaceVariant = skin.muted, outline = skin.line, surfaceContainerHighest = skin.card,
        )
    }
    CompositionLocalProvider(LocalSkin provides skin) {
        MaterialTheme(colorScheme = scheme, content = content)
    }
}
