package com.pjbuilts.scamlens.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Colors = lightColorScheme(
    primary = Color(0xFF168D82),
    onPrimary = Color.White,
    secondary = Color(0xFF8B5A18),
    background = Color(0xFFFBF8F1),
    onBackground = Color(0xFF0B1B2B),
    surface = Color(0xFFFFFDF8),
    onSurface = Color(0xFF0B1B2B),
    error = Color(0xFFB42318)
)

@Composable
fun ScamLensTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = Colors, content = content)
}
