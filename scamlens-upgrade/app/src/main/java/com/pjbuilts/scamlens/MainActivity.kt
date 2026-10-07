package com.pjbuilts.scamlens

import android.Manifest
import android.app.role.RoleManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.pjbuilts.scamlens.data.HistoryItem
import com.pjbuilts.scamlens.data.LocalStore
import com.pjbuilts.scamlens.domain.*
import com.pjbuilts.scamlens.services.ProtectionNotifier
import com.pjbuilts.scamlens.ui.*
import kotlinx.coroutines.delay
import java.text.DateFormat
import java.util.Date

class MainActivity : ComponentActivity() {
    private var protectionRefresh by mutableIntStateOf(0)

    override fun onResume() {
        super.onResume()
        protectionRefresh++
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val shared = if (intent?.action == Intent.ACTION_SEND) intent.getStringExtra(Intent.EXTRA_TEXT).orEmpty()
        else intent?.getStringExtra("scan_text").orEmpty()
        val phone = intent?.getStringExtra(ProtectionNotifier.EXTRA_NUMBER).orEmpty()
        setContent {
            ScamLensTheme {
                var intro by remember { mutableStateOf(true) }
                LaunchedEffect(Unit) { delay(850); intro = false }
                if (intro) Intro() else App(shared, phone, protectionRefresh)
            }
        }
    }
}

private enum class Tab(val title: String, val icon: String) {
    HOME("Home","⌂"), SCAN("Scan","◎"), PROTECT("Protect","◈"), HISTORY("History","↺"), SETTINGS("Settings","⚙")
}

private data class ProtectionStatus(
    val callGuardAvailable: Boolean,
    val callGuardActive: Boolean,
    val notificationAccessActive: Boolean,
    val warningNotificationsAllowed: Boolean
)

private fun readProtectionStatus(ctx: Context): ProtectionStatus {
    val callAvailable: Boolean
    val callActive: Boolean
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
        val roleManager = ctx.getSystemService(RoleManager::class.java)
        callAvailable = roleManager?.isRoleAvailable(RoleManager.ROLE_CALL_SCREENING) == true
        callActive = callAvailable && roleManager?.isRoleHeld(RoleManager.ROLE_CALL_SCREENING) == true
    } else {
        callAvailable = false
        callActive = false
    }

    val notificationAccess = NotificationManagerCompat.getEnabledListenerPackages(ctx).contains(ctx.packageName)
    val warningNotifications = Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
        ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED

    return ProtectionStatus(
        callGuardAvailable = callAvailable,
        callGuardActive = callActive,
        notificationAccessActive = notificationAccess,
        warningNotificationsAllowed = warningNotifications
    )
}

@Composable private fun Intro() {
    Box(Modifier.fillMaxSize().safeDrawingPadding(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("PJBUILTS", color = Forest, fontWeight = FontWeight.Bold, letterSpacing = 2.sp)
            Spacer(Modifier.height(16.dp))
            Text("ScamLens", fontSize = 42.sp, fontWeight = FontWeight.Black)
            Text("Think before you trust.", color = Slate)
            Spacer(Modifier.height(24.dp))
            LinearProgressIndicator(Modifier.width(180.dp))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun App(initialText: String, initialPhone: String, protectionRefresh: Int) {
    val ctx = LocalContext.current
    val store = remember { LocalStore(ctx) }
    var tab by remember { mutableStateOf(if (initialText.isNotBlank() || initialPhone.isNotBlank()) Tab.SCAN else Tab.HOME) }
    var refresh by remember { mutableIntStateOf(0) }

    Scaffold(
        topBar = { TopAppBar(title = {
            Column { Text("ScamLens", fontWeight = FontWeight.Black); Text("by PJBUILTS", fontSize = 11.sp, color = Slate) }
        }) },
        bottomBar = {
            NavigationBar(Modifier.navigationBarsPadding()) {
                Tab.entries.forEach { t ->
                    NavigationBarItem(tab == t, { tab = t }, { Text(t.icon) }, label = { Text(t.title, fontSize = 10.sp) })
                }
            }
        }
    ) { pad ->
        Box(Modifier.padding(pad).fillMaxSize()) {
            when(tab) {
                Tab.HOME -> Home(store, refresh, protectionRefresh) { tab = it }
                Tab.SCAN -> Scan(store, initialText, initialPhone) { refresh++ }
                Tab.PROTECT -> Protect(store, protectionRefresh) { refresh++ }
                Tab.HISTORY -> History(store, refresh) { refresh++ }
                Tab.SETTINGS -> SettingsPage(store) { refresh++ }
            }
        }
    }
}

@Composable private fun Home(store: LocalStore, refresh: Int, protectionRefresh: Int, open: (Tab)->Unit) {
    val ctx = LocalContext.current
    val hist = remember(refresh) { store.getHistory(8) }
    val status = remember(refresh, protectionRefresh) { readProtectionStatus(ctx) }
    val notificationGuardActive = store.notificationGuardEnabled && status.notificationAccessActive
    val fullyProtected = status.callGuardActive && notificationGuardActive && status.warningNotificationsAllowed

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item {
            Text("Protection centre", fontSize = 30.sp, fontWeight = FontWeight.Black)
            Text("ScamLens now reacts with a verdict, evidence and actions — not a score alone.", color = Slate)
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = if (fullyProtected) SoftForest else SoftAmber)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(if (fullyProtected) "LIVE PROTECTION ACTIVE" else "PROTECTION NEEDS ATTENTION",
                        fontWeight = FontWeight.Black, color = if (fullyProtected) Forest else Color(0xFF8A4B00))
                    Text("Incoming Call Guard + Notification Guard", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    Text(if (status.callGuardActive) "✓ Call Guard active" else "○ Call Guard not active", color = Slate)
                    Text(if (notificationGuardActive) "✓ Notification Guard active" else "○ Notification Guard not active", color = Slate)
                    if (!status.warningNotificationsAllowed) Text("○ Warning notification permission needed", color = Slate)
                    Spacer(Modifier.height(4.dp))
                    Button({ open(Tab.PROTECT) }) { Text(if (fullyProtected) "Protection active ✓" else "Finish protection setup") }
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Metric("Recent", hist.size.toString(), Modifier.weight(1f))
                Metric("High concern", hist.count { it.score >= 50 }.toString(), Modifier.weight(1f))
            }
        }
        item {
            Text("Quick tools", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Card { Column(Modifier.padding(16.dp)) {
                Text("Message · Link · Screenshot · QR · Phone", fontWeight = FontWeight.Bold)
                Text("One place to check suspicious content before you click, pay or reply.", color = Slate)
                Spacer(Modifier.height(10.dp)); OutlinedButton({ open(Tab.SCAN) }) { Text("Open scanner") }
            }}
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = SoftAmber)) {
                Text("Low score ≠ safe. It only means no strong evidence was found in the data ScamLens could inspect.",
                    Modifier.padding(16.dp), fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

@Composable private fun Metric(label: String, value: String, mod: Modifier) {
    Card(mod) { Column(Modifier.padding(14.dp)) {
        Text(value, fontSize = 30.sp, fontWeight = FontWeight.Black, color = Forest); Text(label, color = Slate)
    }}
}

@Composable private fun Scan(store: LocalStore, initialText: String, initialPhone: String, changed: ()->Unit) {
    val ctx = LocalContext.current
    var input by remember { mutableStateOf(initialText) }
    var result by remember { mutableStateOf<ScanResult?>(if (initialText.isBlank()) null else RiskEngine.analyse(initialText, ScanSource.SHARED)) }
    var phone by remember { mutableStateOf(initialPhone) }
    var phoneResult by remember { mutableStateOf<PhoneRiskResult?>(null) }
    var info by remember { mutableStateOf("") }

    fun analyseText(text: String, src: ScanSource) {
        if (text.isBlank()) return
        val r = RiskEngine.analyse(text, src); result = r; store.addScan(r); changed()
    }
    fun analysePhone() {
        val n = PhoneRiskEngine.normalize(phone)
        phoneResult = PhoneRiskEngine.analyse(phone, store.isReported(n), store.isBlocked(n), store.isAllowed(n), 0, store.autoBlockHighRisk)
    }

    val screenshot = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) try {
            val image = InputImage.fromFilePath(ctx, uri)
            TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(image)
                .addOnSuccessListener { t -> input = t.text; analyseText(t.text, ScanSource.SCREENSHOT); info = "Screenshot read and analysed on device." }
                .addOnFailureListener { info = "Could not read that screenshot." }
        } catch (_: Exception) { info = "Could not open that screenshot." }
    }

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Analyse suspicious content", fontSize = 27.sp, fontWeight = FontWeight.Black) }
        item {
            OutlinedTextField(input, { input = it }, Modifier.fillMaxWidth(), minLines = 5,
                label = { Text("Message or URL") }, placeholder = { Text("Paste a suspicious message or link…") })
        }
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button({ analyseText(input, ScanSource.MANUAL) }, Modifier.weight(1f)) { Text("Analyse") }
                OutlinedButton({ screenshot.launch("image/*") }, Modifier.weight(1f)) { Text("Screenshot") }
            }
        }
        item {
            OutlinedButton({
                GmsBarcodeScanning.getClient(ctx).startScan()
                    .addOnSuccessListener { b -> b.rawValue?.takeIf { it.isNotBlank() }?.let { v ->
                        input = v; analyseText(v, ScanSource.QR); info = "QR checked. ScamLens did not open it automatically."
                    }}
                    .addOnFailureListener { info = "QR scan cancelled or unavailable." }
            }, Modifier.fillMaxWidth()) { Text("Scan QR safely") }
        }
        if (info.isNotBlank()) item { Text(info, color = Slate, fontSize = 12.sp) }
        result?.let { r -> item { ResultCard(r) } }

        item { HorizontalDivider(); Spacer(Modifier.height(4.dp)); Text("Phone check", fontSize = 22.sp, fontWeight = FontWeight.Bold) }
        item { Text("Uses local evidence only. No fake crowd-report counts.", color = Slate) }
        item { OutlinedTextField(phone, { phone = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Phone number") }) }
        item { Button({ analysePhone() }, Modifier.fillMaxWidth()) { Text("Check caller") } }
        phoneResult?.let { pr -> item {
            PhoneCard(pr,
                trust = { store.allowNumber(pr.normalizedNumber); analysePhone(); changed() },
                report = { store.reportNumber(pr.normalizedNumber); analysePhone(); changed() },
                block = { store.reportNumber(pr.normalizedNumber); store.blockNumber(pr.normalizedNumber); analysePhone(); changed() })
        }}
    }
}

@Composable private fun ResultCard(r: ScanResult) {
    val bg = bg(r.verdict); val fg = fg(r.verdict)
    Card(colors = CardDefaults.cardColors(containerColor = bg)) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
            Text(r.verdictLabel.uppercase(), fontWeight = FontWeight.Black, color = fg, fontSize = 13.sp)
            Text(r.headline, fontSize = 25.sp, fontWeight = FontWeight.Black, color = fg)
            Text(r.evidenceSummary, color = Slate)
            LinearProgressIndicator(progress = { r.score / 100f }, modifier = Modifier.fillMaxWidth())
            Text(r.scoreLabel + " · " + r.category, color = Slate, fontSize = 12.sp)
            if (r.signals.isNotEmpty()) {
                Text("Why ScamLens reacted", fontWeight = FontWeight.Bold)
                r.signals.take(6).forEach { s -> Text("• " + s.title + " · " + s.strengthLabel + ": " + s.detail) }
            }
            Text("What to do now", fontWeight = FontWeight.Bold)
            r.actions.take(4).forEach { a -> Text("• " + a) }
        }
    }
}

@Composable private fun PhoneCard(r: PhoneRiskResult, trust: ()->Unit, report: ()->Unit, block: ()->Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = bg(r.verdict))) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
            Text(r.verdictLabel.uppercase(), fontWeight = FontWeight.Black, color = fg(r.verdict), fontSize = 13.sp)
            Text(r.headline, fontSize = 24.sp, fontWeight = FontWeight.Black)
            Text(r.displayNumber, fontSize = 18.sp, fontWeight = FontWeight.Bold)
            Text(r.scoreLabel, color = Slate, fontSize = 12.sp)
            r.reasons.forEach { Text("• " + it) }
            Text("What to do now", fontWeight = FontWeight.Bold)
            Text(r.recommendedAction, fontWeight = FontWeight.SemiBold)
            if (r.normalizedNumber.isNotBlank()) Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                TextButton(trust) { Text("Trust") }; TextButton(report) { Text("Report") }; Button(block) { Text("Report + block") }
            }
        }
    }
}

@Composable private fun Protect(store: LocalStore, protectionRefresh: Int, changed: ()->Unit) {
    val ctx = LocalContext.current
    var localRefresh by remember { mutableIntStateOf(0) }
    var roleText by remember { mutableStateOf("") }
    var notifText by remember { mutableStateOf("") }
    val status = remember(protectionRefresh, localRefresh) { readProtectionStatus(ctx) }

    val roleLauncher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) {
        localRefresh++
        roleText = if (readProtectionStatus(ctx).callGuardActive)
            "Call Guard is active. ScamLens is Android's selected call-screening app."
        else "Call Guard is not active yet."
    }
    val listenerLauncher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) {
        localRefresh++
        notifText = if (readProtectionStatus(ctx).notificationAccessActive)
            "Notification access granted."
        else "Notification access is still not granted."
    }
    val notifLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        localRefresh++
        notifText = if (it) "Warning notifications enabled." else "Warning notification permission not granted."
    }

    val notificationGuardActive = store.notificationGuardEnabled && status.notificationAccessActive
    val fullyProtected = status.callGuardActive && notificationGuardActive && status.warningNotificationsAllowed

    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Live protection", fontSize = 28.sp, fontWeight = FontWeight.Black)
            Text(if (fullyProtected) "ScamLens is actively connected to Android protection access."
                 else "Complete the items below. Status refreshes automatically when you return to ScamLens.", color = Slate)
        }

        item {
            Card(colors = CardDefaults.cardColors(containerColor = if (status.callGuardActive) SoftForest else SoftAmber)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text("Incoming Call Guard", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    Text(if (status.callGuardActive) "ACTIVE ✓" else "NOT ACTIVE", fontWeight = FontWeight.Black,
                        color = if (status.callGuardActive) Forest else Color(0xFF8A4B00))
                    Text("Shows UNVERIFIED, SUSPECTED SCAM or HIGH RISK with reasons and Block/Trust actions.", color = Slate)

                    if (status.callGuardActive) {
                        OutlinedButton({}, enabled = false) { Text("Call Guard active ✓") }
                    } else if (status.callGuardAvailable) {
                        Button({
                            val rm = ctx.getSystemService(RoleManager::class.java)
                            roleLauncher.launch(rm.createRequestRoleIntent(RoleManager.ROLE_CALL_SCREENING))
                        }) { Text("Enable Call Guard") }
                    } else {
                        Text(if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q)
                            "Android 10+ is required for Call Guard."
                            else "Call screening is unavailable on this device.", color = Slate)
                    }

                    if (roleText.isNotBlank()) Text(roleText, color = Slate, fontSize = 12.sp)
                }
            }
        }

        item {
            Card(colors = CardDefaults.cardColors(containerColor = if (notificationGuardActive) SoftForest else SoftAmber)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text("Notification Guard", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    Text(if (notificationGuardActive) "ACTIVE ✓"
                         else if (status.notificationAccessActive) "ACCESS GRANTED · GUARD PAUSED"
                         else "SYSTEM ACCESS REQUIRED",
                        fontWeight = FontWeight.Black,
                        color = if (notificationGuardActive) Forest else Color(0xFF8A4B00))
                    Text("Checks visible notification text locally and warns when meaningful scam signals are found.", color = Slate)

                    if (status.notificationAccessActive) {
                        OutlinedButton({}, enabled = false) { Text("Notification access granted ✓") }
                    } else {
                        OutlinedButton({
                            listenerLauncher.launch(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
                        }) { Text("Grant notification access") }
                    }

                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        if (status.warningNotificationsAllowed) {
                            Text("✓ Warning notifications allowed", color = Forest, fontWeight = FontWeight.SemiBold)
                        } else {
                            OutlinedButton({ notifLauncher.launch(Manifest.permission.POST_NOTIFICATIONS) }) {
                                Text("Allow warning notifications")
                            }
                        }
                    }
                    if (notifText.isNotBlank()) Text(notifText, color = Slate, fontSize = 12.sp)
                }
            }
        }

        item {
            Toggle(
                "Notification Guard",
                if (status.notificationAccessActive) "Android access is granted. Turn ScamLens analysis on or off here."
                else "Grant Android notification access above, then keep this enabled.",
                store.notificationGuardEnabled
            ) {
                store.notificationGuardEnabled = it
                localRefresh++
                changed()
            }
        }
        item { Toggle("Warn on unverified incoming calls","Show a heads-up status even when the evidence score is low.",store.warnEveryUnverifiedCall) { store.warnEveryUnverifiedCall=it; changed() } }
        item { Toggle("Auto-block 85+ local risk","Reject only very-high-risk calls or numbers already on your block list.",store.autoBlockHighRisk) { store.autoBlockHighRisk=it; changed() } }
        item { Card { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("Reaction levels", fontWeight = FontWeight.Bold)
            Text("UNVERIFIED — caller identity not confirmed", color = Slate)
            Text("CAUTION — meaningful suspicious evidence", color = Slate)
            Text("SUSPECTED SCAM — multiple/strong scam signals", color = Slate)
            Text("HIGH RISK — strong evidence; block/end and verify independently", color = Slate)
        }}}
        item { Card(colors = CardDefaults.cardColors(containerColor = SoftAmber)) { Text("ScamLens will not invent caller reputation. Unknown callers stay UNVERIFIED until real evidence exists.", Modifier.padding(16.dp), fontWeight = FontWeight.SemiBold) } }
    }
}

@Composable private fun History(store: LocalStore, refresh: Int, changed: ()->Unit) {
    val list = remember(refresh) { store.getHistory() }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
        item { Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) { Text("Private history", fontSize = 28.sp, fontWeight = FontWeight.Black); Text("Stored on this device.", color = Slate) }
            if (list.isNotEmpty()) TextButton({ store.clearHistory(); changed() }) { Text("Clear") }
        }}
        if (list.isEmpty()) item { Card { Text("No checks yet.", Modifier.padding(18.dp), color = Slate) } }
        else items(list) { h -> HistoryItemCard(h) }
    }
}

@Composable private fun HistoryItemCard(h: HistoryItem) {
    Card { Column(Modifier.padding(14.dp)) {
        Row(Modifier.fillMaxWidth()) { Text(h.kind, fontWeight = FontWeight.Bold, color = Forest); Spacer(Modifier.weight(1f)); Text("Evidence " + h.score + "/100", color = Slate, fontSize = 12.sp) }
        Text(h.verdict, fontWeight = FontWeight.Black); Text(h.category, color = Slate)
        if (h.preview.isNotBlank()) Text(h.preview, maxLines = 2)
        Text(DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT).format(Date(h.time)), fontSize = 11.sp, color = Slate)
    }}
}

@Composable private fun SettingsPage(store: LocalStore, changed: ()->Unit) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Settings", fontSize = 28.sp, fontWeight = FontWeight.Black); Text("Protection behaviour and privacy.", color = Slate) }
        item { Toggle("Notification Guard","Analyse visible notification text locally.",store.notificationGuardEnabled) { store.notificationGuardEnabled=it; changed() } }
        item { Toggle("Warn on unverified calls","Show a clear caller status even at low evidence risk.",store.warnEveryUnverifiedCall) { store.warnEveryUnverifiedCall=it; changed() } }
        item { Toggle("Auto-block 85+ local risk","Optional. Keep off if you want to review every call.",store.autoBlockHighRisk) { store.autoBlockHighRisk=it; changed() } }
        item { Card { Column(Modifier.padding(16.dp)) {
            Text("Privacy", fontWeight = FontWeight.Bold)
            Text("Core scoring and screenshot OCR run locally. History is short, redacted and device-local.", color = Slate)
        }}}
        item { Text("ScamLens 1.2.1 · PJBUILTS", color = Slate) }
    }
}

@Composable private fun Toggle(title: String, sub: String, checked: Boolean, change: (Boolean)->Unit) {
    Card { Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) { Text(title, fontWeight = FontWeight.Bold); Text(sub, color = Slate, fontSize = 12.sp) }
        Spacer(Modifier.width(10.dp)); Switch(checked, change)
    }}
}

private fun bg(v: Verdict): Color = when(v) {
    Verdict.NO_STRONG_SIGNALS -> SoftForest
    Verdict.USE_CAUTION -> SoftAmber
    else -> SoftDanger
}
private fun fg(v: Verdict): Color = when(v) {
    Verdict.NO_STRONG_SIGNALS -> Forest
    Verdict.USE_CAUTION -> Color(0xFF8A4B00)
    else -> Danger
}
