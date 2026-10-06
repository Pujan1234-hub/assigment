package com.pjbuilts.scamlens.domain

enum class RiskLevel { LOW, MEDIUM, HIGH, CRITICAL }

data class RiskSignal(
    val title: String,
    val detail: String,
    val points: Int,
    val source: String = "On-device"
)

data class ScanResult(
    val rawInput: String,
    val score: Int,
    val level: RiskLevel,
    val verdict: String,
    val category: String,
    val signals: List<RiskSignal>,
    val actions: List<String>,
    val liveIntelChecked: Boolean = false,
    val liveIntelMatch: Boolean = false
)

data class HistoryEntry(
    val kind: String,
    val title: String,
    val verdict: String,
    val score: Int,
    val createdAt: Long
)
