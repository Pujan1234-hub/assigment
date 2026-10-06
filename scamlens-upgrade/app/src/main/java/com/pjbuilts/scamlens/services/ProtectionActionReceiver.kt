package com.pjbuilts.scamlens.services

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.pjbuilts.scamlens.data.LocalStore

class ProtectionActionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val number = intent.getStringExtra(ProtectionNotifier.EXTRA_NUMBER).orEmpty()
        if (number.isBlank()) return
        val store = LocalStore(context)
        when (intent.action) {
            ProtectionNotifier.ACTION_BLOCK -> {
                store.reportNumber(number)
                store.blockNumber(number)
            }
            ProtectionNotifier.ACTION_TRUST -> store.allowNumber(number)
        }
    }
}
