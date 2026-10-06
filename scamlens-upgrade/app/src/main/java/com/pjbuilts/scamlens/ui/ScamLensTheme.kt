package com.pjbuilts.scamlens.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val Cream = Color(0xFFFFF9F0)
val Ink = Color(0xFF15201E)
val Forest = Color(0xFF0B6B5D)
val SoftForest = Color(0xFFDDF1EB)
val Amber = Color(0xFFF29D49)
val SoftAmber = Color(0xFFFFE8CE)
val Danger = Color(0xFFB3261E)
val SoftDanger = Color(0xFFFFDAD6)
val Slate = Color(0xFF4E5E59)

private val ScamLensColors = lightColorScheme(
    primary = Forest,
    onPrimary = Color.White,
    secondary = Amber,
    onSecondary = Ink,
    background = Cream,
    onBackground = Ink,
    surface = Color(0xFFFFFCF7),
    onSurface = Ink,
    error = Danger,
    onError = Color.White
)

@Composable
fun ScamLensTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = ScamLensColors, content = content)
}
