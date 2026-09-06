package com.sathiai.app

import android.app.Activity
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val StudyBgA = Color(0xFF060A17)
private val StudyBgB = Color(0xFF10162A)
private val StudyPanelA = Color(0xFF151D32)
private val StudyPanelB = Color(0xFF1B2540)
private val StudyPurpleA = Color(0xFF7A5CFF)
private val StudyCyanA = Color(0xFF42D8FF)
private val StudyGreenA = Color(0xFF65F1A8)
private val StudyYellowA = Color(0xFFFFD76A)
private val StudyTextA = Color(0xFFF6F8FF)
private val StudySoftA = Color(0xFFAEB8D2)
private val StudyStrokeA = Color(0xFF2B3659)

private enum class StudyPageV5 {
    HOME,
    LESSON_LIST,
    LESSON_DETAIL,
    IMPORTANT_QUESTIONS,
    MODEL_PAPER,
    MCQ,
    PRACTICAL,
    REVISION,
    ANSWER_CHECK
}

private enum class AnswerLanguageV5 {
    NEPALI,
    ENGLISH
}

private data class GradeInfoV5(
    val grade: Int,
    val exam: String,
    val sourceUrl: String,
    val compulsory: List<String>,
    val optional: List<String>
)

private val gradeDataV5 = listOf(
    GradeInfoV5(
        grade = 8,
        exam = "आधारभूत तह कक्षा ८ मुख्य परीक्षा तयारी",
        sourceUrl = "https://moecdc.gov.np/content/202/basic-education-courses--2077--class-6-8--mandatory/",
        compulsory = listOf(
            "नेपाली",
            "अङ्ग्रेजी",
            "गणित",
            "विज्ञान तथा प्रविधि",
            "सामाजिक अध्ययन तथा मानव मूल्य शिक्षा",
            "स्वास्थ्य, शारीरिक शिक्षा तथा सिर्जनात्मक कला"
        ),
        optional = listOf(
            "स्थानीय विषय / स्थानीय पाठ्यक्रम",
            "मातृभाषा / विद्यालयअनुसार थप विषय"
        )
    ),
    GradeInfoV5(
        grade = 9,
        exam = "कक्षा ९ वार्षिक परीक्षा तथा SEE आधार तयारी",
        sourceUrl = "https://moecdc.gov.np/content/201/secondary-education-curssions--2078--class-9-10--mandatory/",
        compulsory = listOf(
            "नेपाली",
            "अङ्ग्रेजी",
            "गणित",
            "विज्ञान तथा प्रविधि",
            "सामाजिक अध्ययन"
        ),
        optional = listOf(
            "ऐच्छिक गणित",
            "कम्प्युटर विज्ञान",
            "लेखा",
            "अर्थशास्त्र",
            "स्वास्थ्य तथा शारीरिक शिक्षा",
            "अन्य विद्यालयमा उपलब्ध ऐच्छिक विषय"
        )
    ),
    GradeInfoV5(
        grade = 10,
        exam = "SEE पूर्ण तयारी",
        sourceUrl = "https://moecdc.gov.np/pages/specification-table-5/",
        compulsory = listOf(
            "नेपाली",
            "अङ्ग्रेजी",
            "गणित",
            "विज्ञान तथा प्रविधि",
            "सामाजिक अध्ययन"
        ),
        optional = listOf(
            "ऐच्छिक गणित",
            "कम्प्युटर विज्ञान",
            "लेखा",
            "अर्थशास्त्र",
            "स्वास्थ्य तथा शारीरिक शिक्षा",
            "अन्य विद्यालयमा उपलब्ध ऐच्छिक विषय"
        )
    ),
    GradeInfoV5(
        grade = 11,
        exam = "कक्षा ११ वार्षिक परीक्षा तयारी",
        sourceUrl = "https://moecdc.gov.np/",
        compulsory = listOf(
            "नेपाली",
            "अङ्ग्रेजी",
            "सामाजिक अध्ययन तथा जीवनोपयोगी शिक्षा"
        ),
        optional = listOf(
            "गणित",
            "भौतिक विज्ञान",
            "रसायन विज्ञान",
            "जीव विज्ञान",
            "कम्प्युटर विज्ञान",
            "लेखाशास्त्र",
            "अर्थशास्त्र",
            "व्यवसाय अध्ययन",
            "होटल व्यवस्थापन",
            "समाजशास्त्र / मनोविज्ञान",
            "अन्य छनोटअनुसारका विषय"
        )
    ),
    GradeInfoV5(
        grade = 12,
        exam = "NEB कक्षा १२ बोर्ड परीक्षा पूर्ण तयारी",
        sourceUrl = "https://moecdc.gov.np/",
        compulsory = listOf(
            "नेपाली",
            "अङ्ग्रेजी",
            "सामाजिक अध्ययन तथा जीवनोपयोगी शिक्षा"
        ),
        optional = listOf(
            "गणित",
            "भौतिक विज्ञान",
            "रसायन विज्ञान",
            "जीव विज्ञान",
            "कम्प्युटर विज्ञान",
            "लेखाशास्त्र",
            "अर्थशास्त्र",
            "व्यवसाय अध्ययन",
            "होटल व्यवस्थापन",
            "समाजशास्त्र / मनोविज्ञान",
            "अन्य छनोटअनुसारका विषय"
        )
    )
)

@Composable
fun StudyModuleScreen(
    engine: AssistantEngine,
    speak: (String) -> Unit,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val onlineRepo = remember { StudyOnlineRepository(context) }

    var page by remember { mutableStateOf(StudyPageV5.HOME) }
    var selectedGrade by remember { mutableStateOf<Int?>(null) }
    var selectedSubject by remember { mutableStateOf<String?>(null) }
    var selectedLesson by remember { mutableStateOf<StudyLessonItem?>(null) }

    var answerLanguage by remember {
        mutableStateOf(AnswerLanguageV5.NEPALI)
    }

    var lessons by remember {
        mutableStateOf<List<StudyLessonItem>>(emptyList())
    }
    var lessonSources by remember {
        mutableStateOf<List<StudyOnlineSource>>(emptyList())
    }

    var questions by remember {
        mutableStateOf<List<StudyQuestionItem>>(emptyList())
    }
    var questionSources by remember {
        mutableStateOf<List<StudyOnlineSource>>(emptyList())
    }

    var expandedAnswers by remember {
        mutableStateOf<Set<Int>>(emptySet())
    }

    var contentText by remember { mutableStateOf("") }
    var customQuestion by remember { mutableStateOf("") }
    var studentAnswer by remember { mutableStateOf("") }
    var thinking by remember { mutableStateOf(false) }
    var loadingTitle by remember { mutableStateOf("") }
    var onlineBadge by remember { mutableStateOf("") }

    val grade = gradeDataV5.firstOrNull {
        it.grade == selectedGrade
    }

    fun isEnglishAnswer(): Boolean {
        return answerLanguage == AnswerLanguageV5.ENGLISH
    }

    fun languageRule(): String {
        return if (isEnglishAnswer()) {
            """
Answer in clear student-friendly English.
Understand Nepali script, Roman Nepali and English input.
For Nepali subject, keep necessary Nepali examples in Devanagari.
""".trimIndent()
        } else {
            """
मुख्य उत्तर नेपालीमा देऊ।
विद्यार्थीले Roman Nepali मा लेखे पनि नेपालीकै अर्थमा बुझ।
अङ्ग्रेजी विषयमा आवश्यक original sentence, vocabulary, grammar example वा writing sample English मा राख्न मिल्छ, तर explanation नेपालीमा देऊ।
""".trimIndent()
        }
    }

    fun runUi(block: () -> Unit) {
        (context as? Activity)?.runOnUiThread(block)
    }

    fun callAi(
        title: String,
        prompt: String,
        onDone: (String) -> Unit
    ) {
        thinking = true
        loadingTitle = title
        onlineBadge = ""

        engine.ask(
            question = prompt,
            onResult = { reply ->
                runUi {
                    thinking = false
                    onDone(reply.text)
                }
            },
            onError = { error ->
                runUi {
                    thinking = false
                    contentText = error
                }
            }
        )
    }

    fun loadLessons(forceRefresh: Boolean = false) {
        val g = grade ?: return
        val subject = selectedSubject ?: return

        thinking = true
        loadingTitle = "चालु पाठ्यक्रमका पाठ खोज्दैछ…"
        onlineBadge = "अनलाइन स्रोत जाँच्दै"

        onlineRepo.loadLessons(
            grade = g.grade,
            subject = subject,
            englishAnswer = isEnglishAnswer(),
            forceRefresh = forceRefresh,
            onResult = { result ->
                runUi {
                    thinking = false
                    lessons = result.lessons
                    lessonSources = result.sources
                    onlineBadge =
                        if (result.fromCache) "⚡ सुरक्षित सूची"
                        else "● अनलाइन स्रोतबाट जाँचिएको"
                    page = StudyPageV5.LESSON_LIST
                }
            },
            onError = { error ->
                runUi {
                    thinking = false
                    contentText = error
                    onlineBadge = ""
                }
            }
        )
    }

    fun loadImportantQuestions(forceRefresh: Boolean = false) {
        val g = grade ?: return
        val subject = selectedSubject ?: return

        thinking = true
        loadingTitle = "अनलाइन प्रश्नपत्र र मोडेल प्रश्न खोज्दैछ…"
        expandedAnswers = emptySet()
        onlineBadge = "अनलाइन स्रोत जाँच्दै"

        onlineRepo.loadImportantQuestions(
            grade = g.grade,
            subject = subject,
            englishAnswer = isEnglishAnswer(),
            forceRefresh = forceRefresh,
            onResult = { result ->
                runUi {
                    thinking = false
                    questions = result.questions
                    questionSources = result.sources
                    onlineBadge =
                        if (result.fromCache) "⚡ सुरक्षित प्रश्न बैंक"
                        else "● अनलाइन स्रोतमा आधारित"
                    page = StudyPageV5.IMPORTANT_QUESTIONS
                }
            },
            onError = { error ->
                runUi {
                    thinking = false
                    contentText = error
                    onlineBadge = ""
                }
            }
        )
    }

    fun openLesson(lesson: StudyLessonItem) {
        val g = grade ?: return
        val subject = selectedSubject ?: return

        selectedLesson = lesson
        page = StudyPageV5.LESSON_DETAIL
        contentText = ""

        val prompt = """
SATHI AI नेपाल शिक्षा शिक्षक मोड।

कक्षा: ${g.grade}
विषय: $subject
पाठ/अध्याय: ${lesson.title}
अनलाइन स्रोत: ${lesson.sourceTitle}

${languageRule()}

विद्यार्थीलाई यो पाठ zero बाट step-by-step सिकाऊ।

Structure:
१. पाठको लक्ष्य
२. आधारभूत अवधारणा
३. मुख्य परिभाषा/सूत्र/नियम
४. सजिलो उदाहरण
५. step-by-step व्याख्या वा समाधान
६. परीक्षा टिप्स
७. ५ अभ्यास प्रश्न
८. अभ्यास उत्तर छुट्टै अन्त्यमा
९. ५ प्रश्नको mini test

नियम:
- अभिवादन नगरी सीधै पढाउन सुरु गर।
- कक्षा ${g.grade} को स्तरअनुसार मात्र।
- गणित/विज्ञान/लेखा भए calculation का आवश्यक सबै step देखाऊ।
- पाठ्यक्रमबाहिरको कुरा नबनाऊ।
""".trimIndent()

        callAi(
            title = "पाठ step-by-step तयार हुँदैछ",
            prompt = prompt
        ) { answer ->
            contentText = answer
            speak(answer)
        }
    }

    fun loadModelPaper() {
        val g = grade ?: return
        val subject = selectedSubject ?: return

        page = StudyPageV5.MODEL_PAPER
        contentText = ""

        val prompt = """
खोज: चालु नेपाल CDC/NEB पाठ्यक्रम, specification grid र online model/past-paper patterns जाँचेर कक्षा ${g.grade} "$subject" को अभ्यास नमुना प्रश्नपत्र बनाऊ।

${languageRule()}

नियम:
- वास्तविक/लीक प्रश्नपत्र भनेर नलेख।
- परीक्षा उपयोगी, वास्तविक question-pattern मा आधारित practice paper बनाऊ।
- marks/time official स्रोतमा पुष्टि नभए अनुमान नगर।
- curriculum बारे meta question नबनाऊ।
- अन्त्यमा उत्तर सङ्केत छुट्टै देऊ।
""".trimIndent()

        callAi("नमुना प्रश्नपत्र तयार हुँदैछ", prompt) {
            contentText = it
        }
    }

    fun loadMcq() {
        val g = grade ?: return
        val subject = selectedSubject ?: return

        page = StudyPageV5.MCQ
        contentText = ""

        val prompt = """
कक्षा ${g.grade} "$subject" विषयको exam preparation का लागि 25 वटा उपयोगी MCQ बनाऊ।

${languageRule()}

विभिन्न पाठ/skills बाट balanced प्रश्न बनाऊ।
Curriculum/CDC/NEB के हो भन्ने meta प्रश्न नबनाऊ।
प्रत्येकमा क), ख), ग), घ) विकल्प राख।
सबै प्रश्नपछि answer key र छोटो कारण देऊ।
""".trimIndent()

        callAi("बहुविकल्पीय अभ्यास तयार हुँदैछ", prompt) {
            contentText = it
        }
    }

    fun loadPractical() {
        val g = grade ?: return
        val subject = selectedSubject ?: return

        page = StudyPageV5.PRACTICAL
        contentText = ""

        val prompt = """
कक्षा ${g.grade} "$subject" विषयको curriculum-level practical/project training तयार गर।

${languageRule()}

हरेक practical मा:
- उद्देश्य
- सामग्री
- सुरक्षा
- प्रक्रिया
- observation
- result/conclusion
- record/file मा के लेख्ने
- viva का ५ प्रश्न र उत्तर

असुरक्षित प्रयोग नदेऊ।
""".trimIndent()

        callAi("प्रायोगिक अभ्यास तयार हुँदैछ", prompt) {
            contentText = it
        }
    }

    fun loadRevision() {
        val g = grade ?: return
        val subject = selectedSubject ?: return

        page = StudyPageV5.REVISION
        contentText = ""

        val prompt = """
कक्षा ${g.grade} "$subject" विषयको main exam अघिको quick revision sheet बनाऊ।

${languageRule()}

समेट:
- पाठअनुसार मुख्य कुरा
- परिभाषा
- सूत्र/नियम
- याद गर्नुपर्ने तथ्य
- common mistakes
- १० quick-check प्रश्न र छोटा उत्तर
""".trimIndent()

        callAi("दोहोर्‍याइ नोट तयार हुँदैछ", prompt) {
            contentText = it
        }
    }

    fun checkStudentAnswer() {
        val g = grade ?: return
        val subject = selectedSubject ?: return
        if (studentAnswer.isBlank()) return

        page = StudyPageV5.ANSWER_CHECK
        contentText = ""

        val prompt = """
कक्षा ${g.grade} "$subject" विषयको विद्यार्थीको उत्तर जाँच।

${languageRule()}

विद्यार्थीको उत्तर:
$studentAnswer

देऊ:
१. सही भाग
२. गलत/कमजोर भाग
३. छुटेको मुख्य point
४. सुधारिएको model answer
५. exam मा राम्रो बनाउन ३ सुझाव
६. स्तर: कमजोर / ठीक / राम्रो / उत्कृष्ट
""".trimIndent()

        callAi("उत्तर जाँच हुँदैछ", prompt) {
            contentText = it
        }
    }

    when (page) {
        StudyPageV5.HOME -> {
            StudyHomeV5(
                selectedGrade = selectedGrade,
                selectedSubject = selectedSubject,
                answerLanguage = answerLanguage,
                grade = grade,
                customQuestion = customQuestion,
                studentAnswer = studentAnswer,
                thinking = thinking,
                loadingTitle = loadingTitle,
                onBack = onBack,
                onGrade = {
                    selectedGrade = it
                    selectedSubject = null
                    lessons = emptyList()
                    questions = emptyList()
                    contentText = ""
                },
                onSubject = {
                    selectedSubject = it
                    lessons = emptyList()
                    questions = emptyList()
                    contentText = ""
                },
                onLanguage = { answerLanguage = it },
                onCustomChange = { customQuestion = it },
                onStudentAnswerChange = { studentAnswer = it },
                onLessons = { loadLessons(false) },
                onImportant = { loadImportantQuestions(false) },
                onModelPaper = { loadModelPaper() },
                onMcq = { loadMcq() },
                onPractical = { loadPractical() },
                onRevision = { loadRevision() },
                onCheckAnswer = { checkStudentAnswer() },
                onAskCustom = {
                    val g = grade
                    val subject = selectedSubject

                    if (g != null && subject != null && customQuestion.isNotBlank()) {
                        page = StudyPageV5.LESSON_DETAIL
                        selectedLesson = null
                        contentText = ""

                        val prompt = """
SATHI AI नेपाल शिक्षा मोड।
कक्षा: ${g.grade}
विषय: $subject

विद्यार्थीको input:
$customQuestion

${languageRule()}

Roman Nepali भए नेपाली अर्थमा बुझ।
Zero बाट step-by-step सिकाऊ।
अभिवादन नगरी सीधै विषयबाट सुरु गर।
""".trimIndent()

                        callAi("SATHI ले पढाउँदैछ", prompt) {
                            contentText = it
                            speak(it)
                        }
                    }
                },
                onOfficialSource = {
                    grade?.let {
                        try {
                            context.startActivity(
                                Intent(
                                    Intent.ACTION_VIEW,
                                    Uri.parse(it.sourceUrl)
                                )
                            )
                        } catch (_: Exception) {
                        }
                    }
                }
            )
        }

        StudyPageV5.LESSON_LIST -> {
            LessonListPageV5(
                grade = grade,
                subject = selectedSubject,
                lessons = lessons,
                sources = lessonSources,
                badge = onlineBadge,
                onBack = { page = StudyPageV5.HOME },
                onRefresh = { loadLessons(true) },
                onLesson = { openLesson(it) }
            )
        }

        StudyPageV5.IMPORTANT_QUESTIONS -> {
            QuestionBankPageV5(
                grade = grade,
                subject = selectedSubject,
                questions = questions,
                sources = questionSources,
                badge = onlineBadge,
                expanded = expandedAnswers,
                onBack = { page = StudyPageV5.HOME },
                onRefresh = { loadImportantQuestions(true) },
                onToggle = { no ->
                    expandedAnswers =
                        if (expandedAnswers.contains(no)) {
                            expandedAnswers - no
                        } else {
                            expandedAnswers + no
                        }
                },
                onShowAll = {
                    expandedAnswers = questions.map { it.no }.toSet()
                },
                onHideAll = { expandedAnswers = emptySet() }
            )
        }

        StudyPageV5.LESSON_DETAIL,
        StudyPageV5.MODEL_PAPER,
        StudyPageV5.MCQ,
        StudyPageV5.PRACTICAL,
        StudyPageV5.REVISION,
        StudyPageV5.ANSWER_CHECK -> {
            TextContentPageV5(
                title = when (page) {
                    StudyPageV5.LESSON_DETAIL ->
                        selectedLesson?.title ?: "SATHI पढाइ"
                    StudyPageV5.MODEL_PAPER -> "अभ्यास नमुना प्रश्नपत्र"
                    StudyPageV5.MCQ -> "बहुविकल्पीय अभ्यास"
                    StudyPageV5.PRACTICAL -> "प्रायोगिक अभ्यास"
                    StudyPageV5.REVISION -> "छिटो दोहोर्‍याइ"
                    StudyPageV5.ANSWER_CHECK -> "उत्तर जाँच"
                    else -> "SATHI पढाइ"
                },
                subtitle = "कक्षा ${grade?.grade ?: ""} • ${selectedSubject ?: ""}",
                text = contentText,
                thinking = thinking,
                loadingTitle = loadingTitle,
                onBack = {
                    if (
                        page == StudyPageV5.LESSON_DETAIL &&
                        selectedLesson != null &&
                        lessons.isNotEmpty()
                    ) {
                        page = StudyPageV5.LESSON_LIST
                    } else {
                        page = StudyPageV5.HOME
                    }
                }
            )
        }
    }
}

@Composable
private fun StudyHomeV5(
    selectedGrade: Int?,
    selectedSubject: String?,
    answerLanguage: AnswerLanguageV5,
    grade: GradeInfoV5?,
    customQuestion: String,
    studentAnswer: String,
    thinking: Boolean,
    loadingTitle: String,
    onBack: () -> Unit,
    onGrade: (Int) -> Unit,
    onSubject: (String) -> Unit,
    onLanguage: (AnswerLanguageV5) -> Unit,
    onCustomChange: (String) -> Unit,
    onStudentAnswerChange: (String) -> Unit,
    onLessons: () -> Unit,
    onImportant: () -> Unit,
    onModelPaper: () -> Unit,
    onMcq: () -> Unit,
    onPractical: () -> Unit,
    onRevision: () -> Unit,
    onCheckAnswer: () -> Unit,
    onAskCustom: () -> Unit,
    onOfficialSource: () -> Unit
) {
    StudyPageContainerV5 {
        StudyHeaderV5(
            title = "SATHI पढाइ",
            subtitle = "नेपालको कक्षा ८–१२ परीक्षा तयारी",
            onBack = onBack
        )

        Spacer(Modifier.height(18.dp))

        Text("उत्तर भाषा", color = StudyTextA, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))

        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            ChoiceChipV5(
                text = "नेपाली",
                selected = answerLanguage == AnswerLanguageV5.NEPALI,
                modifier = Modifier.weight(1f)
            ) { onLanguage(AnswerLanguageV5.NEPALI) }

            ChoiceChipV5(
                text = "English",
                selected = answerLanguage == AnswerLanguageV5.ENGLISH,
                modifier = Modifier.weight(1f)
            ) { onLanguage(AnswerLanguageV5.ENGLISH) }
        }

        Spacer(Modifier.height(5.dp))
        Text(
            "लेख्न मिल्ने: नेपाली • Roman Nepali • English",
            color = StudyCyanA,
            fontSize = 11.sp
        )

        Spacer(Modifier.height(20.dp))
        Text(
            "१. कक्षा छान्नुहोस्",
            color = StudyTextA,
            fontWeight = FontWeight.Bold,
            fontSize = 18.sp
        )
        Spacer(Modifier.height(9.dp))

        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(7.dp)
        ) {
            (8..12).forEach { g ->
                GradeChipV5(
                    grade = g,
                    selected = selectedGrade == g,
                    modifier = Modifier.weight(1f)
                ) { onGrade(g) }
            }
        }

        if (grade != null) {
            Spacer(Modifier.height(18.dp))
            Surface(
                color = StudyPanelA,
                shape = RoundedCornerShape(18.dp),
                border = BorderStroke(1.dp, StudyStrokeA),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(Modifier.padding(15.dp)) {
                    Text(
                        "कक्षा ${grade.grade}",
                        color = StudyTextA,
                        fontWeight = FontWeight.Black,
                        fontSize = 20.sp
                    )
                    Text(grade.exam, color = StudyYellowA, fontSize = 12.sp)
                    Spacer(Modifier.height(9.dp))
                    OutlinedButton(
                        onClick = onOfficialSource,
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("आधिकारिक CDC स्रोत") }
                }
            }

            Spacer(Modifier.height(20.dp))
            Text(
                "२. विषय छान्नुहोस्",
                color = StudyTextA,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp
            )
            Spacer(Modifier.height(9.dp))
            Text(
                "अनिवार्य विषय",
                color = StudyCyanA,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.height(6.dp))

            grade.compulsory.forEach { subject ->
                SubjectRowV5(subject, selectedSubject == subject) {
                    onSubject(subject)
                }
                Spacer(Modifier.height(6.dp))
            }

            if (grade.optional.isNotEmpty()) {
                Spacer(Modifier.height(10.dp))
                Text(
                    "ऐच्छिक / छनोटअनुसार",
                    color = StudyYellowA,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(6.dp))

                grade.optional.forEach { subject ->
                    SubjectRowV5(subject, selectedSubject == subject) {
                        onSubject(subject)
                    }
                    Spacer(Modifier.height(6.dp))
                }
            }
        }

        if (grade != null && selectedSubject != null) {
            Spacer(Modifier.height(22.dp))

            Surface(
                color = Color(0xFF102C25),
                shape = RoundedCornerShape(17.dp),
                border = BorderStroke(1.dp, Color(0xFF245546)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    "✓ 'सबै पाठ' र 'महत्त्वपूर्ण प्रश्न' अब अनलाइन स्रोत जाँचेर तयार हुन्छन्।",
                    color = StudyGreenA,
                    fontSize = 12.sp,
                    modifier = Modifier.padding(13.dp)
                )
            }

            Spacer(Modifier.height(18.dp))
            Text(
                "३. परीक्षा तयारी",
                color = StudyTextA,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp
            )
            Spacer(Modifier.height(9.dp))

            ToolGridV5(
                tools = listOf(
                    Triple("📚", "सबै पाठ", onLessons),
                    Triple("⭐", "अनलाइन महत्त्वपूर्ण प्रश्न", onImportant),
                    Triple("📝", "नमुना प्रश्नपत्र", onModelPaper),
                    Triple("🔘", "बहुविकल्पीय अभ्यास", onMcq),
                    Triple("🧪", "प्रायोगिक अभ्यास", onPractical),
                    Triple("⚡", "छिटो दोहोर्‍याइ", onRevision)
                )
            )

            Spacer(Modifier.height(22.dp))
            Text(
                "४. आफ्नो प्रश्न",
                color = StudyTextA,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp
            )
            Text(
                "Roman Nepali पनि बुझ्छ — “malai pahilo lesson bata sikau”",
                color = StudyCyanA,
                fontSize = 11.sp
            )
            Spacer(Modifier.height(8.dp))

            OutlinedTextField(
                value = customQuestion,
                onValueChange = onCustomChange,
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("प्रश्न, पाठ वा topic लेख्नुहोस्…") },
                minLines = 3,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = StudyTextA,
                    unfocusedTextColor = StudyTextA,
                    focusedBorderColor = StudyPurpleA,
                    unfocusedBorderColor = StudyStrokeA
                ),
                shape = RoundedCornerShape(16.dp)
            )
            Spacer(Modifier.height(8.dp))
            Button(
                onClick = onAskCustom,
                enabled = customQuestion.isNotBlank() && !thinking,
                modifier = Modifier.fillMaxWidth()
            ) { Text("SATHI लाई सोध्नुहोस्") }

            Spacer(Modifier.height(20.dp))
            Text(
                "५. आफ्नो उत्तर जाँच",
                color = StudyTextA,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = studentAnswer,
                onValueChange = onStudentAnswerChange,
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("तपाईंले लेखेको उत्तर यहाँ राख्नुहोस्…") },
                minLines = 4,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = StudyTextA,
                    unfocusedTextColor = StudyTextA,
                    focusedBorderColor = StudyPurpleA,
                    unfocusedBorderColor = StudyStrokeA
                ),
                shape = RoundedCornerShape(16.dp)
            )
            Spacer(Modifier.height(8.dp))
            OutlinedButton(
                onClick = onCheckAnswer,
                enabled = studentAnswer.isNotBlank() && !thinking,
                modifier = Modifier.fillMaxWidth()
            ) { Text("मेरो उत्तर जाँच") }
        }

        if (thinking) {
            Spacer(Modifier.height(20.dp))
            LoadingCardV5(loadingTitle)
        }

        Spacer(Modifier.height(36.dp))
    }
}

@Composable
private fun LessonListPageV5(
    grade: GradeInfoV5?,
    subject: String?,
    lessons: List<StudyLessonItem>,
    sources: List<StudyOnlineSource>,
    badge: String,
    onBack: () -> Unit,
    onRefresh: () -> Unit,
    onLesson: (StudyLessonItem) -> Unit
) {
    StudyPageContainerV5 {
        StudyHeaderV5(
            title = "सबै पाठ",
            subtitle = "कक्षा ${grade?.grade ?: ""} • ${subject ?: ""}",
            onBack = onBack
        )
        Spacer(Modifier.height(16.dp))
        SourceBadgeV5(badge, sources.size, onRefresh)
        Spacer(Modifier.height(12.dp))
        Text(
            "कुनै पाठ थिच्नुहोस् — नयाँ page मा zero बाट step-by-step सिकाइ खुल्छ।",
            color = StudyCyanA,
            fontSize = 12.sp
        )
        Spacer(Modifier.height(12.dp))

        lessons.forEach { lesson ->
            Surface(
                modifier = Modifier.fillMaxWidth().clickable { onLesson(lesson) },
                color = StudyPanelA,
                shape = RoundedCornerShape(18.dp),
                border = BorderStroke(1.dp, StudyStrokeA)
            ) {
                Row(
                    Modifier.padding(15.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        Modifier.size(42.dp).background(StudyPurpleA, CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Text("${lesson.no}", color = Color.White, fontWeight = FontWeight.Black)
                    }
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text(lesson.title, color = StudyTextA, fontWeight = FontWeight.Bold)
                        if (lesson.summary.isNotBlank()) {
                            Spacer(Modifier.height(3.dp))
                            Text(
                                lesson.summary,
                                color = StudySoftA,
                                fontSize = 11.sp,
                                lineHeight = 16.sp,
                                maxLines = 3,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                        if (lesson.sourceTitle.isNotBlank()) {
                            Spacer(Modifier.height(5.dp))
                            Text(
                                "स्रोत: ${lesson.sourceTitle}",
                                color = StudyGreenA,
                                fontSize = 9.sp,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                    Text("›", color = StudyCyanA, fontSize = 22.sp)
                }
            }
            Spacer(Modifier.height(8.dp))
        }
        Spacer(Modifier.height(30.dp))
    }
}

@Composable
private fun QuestionBankPageV5(
    grade: GradeInfoV5?,
    subject: String?,
    questions: List<StudyQuestionItem>,
    sources: List<StudyOnlineSource>,
    badge: String,
    expanded: Set<Int>,
    onBack: () -> Unit,
    onRefresh: () -> Unit,
    onToggle: (Int) -> Unit,
    onShowAll: () -> Unit,
    onHideAll: () -> Unit
) {
    val context = LocalContext.current

    StudyPageContainerV5 {
        StudyHeaderV5(
            title = "अनलाइन महत्त्वपूर्ण प्रश्न",
            subtitle = "कक्षा ${grade?.grade ?: ""} • ${subject ?: ""}",
            onBack = onBack
        )
        Spacer(Modifier.height(16.dp))
        SourceBadgeV5(badge, sources.size, onRefresh)
        Spacer(Modifier.height(12.dp))

        Surface(
            color = Color(0xFF102C25),
            shape = RoundedCornerShape(16.dp),
            border = BorderStroke(1.dp, Color(0xFF245546)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                "यी प्रश्न online model/past-paper/question-pattern स्रोतबाट सङ्कलन वा त्यसैको नजिकको अभ्यास रूप हुन्। Curriculum बारे बेकार meta प्रश्न हटाइएको छ। उत्तर पहिले लुकाइएको छ।",
                color = StudyGreenA,
                fontSize = 12.sp,
                lineHeight = 18.sp,
                modifier = Modifier.padding(13.dp)
            )
        }

        Spacer(Modifier.height(12.dp))
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedButton(onClick = onShowAll, modifier = Modifier.weight(1f)) {
                Text("सबै उत्तर देखाऊ")
            }
            OutlinedButton(onClick = onHideAll, modifier = Modifier.weight(1f)) {
                Text("सबै उत्तर लुकाऊ")
            }
        }
        Spacer(Modifier.height(14.dp))

        questions.forEach { item ->
            val open = expanded.contains(item.no)
            Surface(
                color = StudyPanelA,
                shape = RoundedCornerShape(19.dp),
                border = BorderStroke(1.dp, if (open) StudyPurpleA else StudyStrokeA),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(Modifier.padding(15.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            Modifier.size(34.dp).background(StudyPanelB, CircleShape),
                            contentAlignment = Alignment.Center
                        ) {
                            Text("${item.no}", color = StudyCyanA, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                        }
                        Spacer(Modifier.width(9.dp))
                        QuestionTagV5(item.priority)
                        Spacer(Modifier.width(6.dp))
                        if (item.type.isNotBlank()) QuestionTagV5(item.type)
                    }

                    Spacer(Modifier.height(10.dp))
                    Text(
                        item.question,
                        color = StudyTextA,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 15.sp,
                        lineHeight = 22.sp
                    )

                    if (item.sourceTitle.isNotBlank()) {
                        Spacer(Modifier.height(9.dp))
                        Surface(
                            modifier = Modifier.clickable {
                                if (item.sourceUrl.isNotBlank()) {
                                    try {
                                        context.startActivity(
                                            Intent(Intent.ACTION_VIEW, Uri.parse(item.sourceUrl))
                                        )
                                    } catch (_: Exception) {}
                                }
                            },
                            color = Color(0xFF10243A),
                            shape = RoundedCornerShape(50.dp)
                        ) {
                            Text(
                                "↗ स्रोत: ${item.sourceTitle}",
                                color = StudyCyanA,
                                fontSize = 9.sp,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                                modifier = Modifier.padding(horizontal = 9.dp, vertical = 6.dp)
                            )
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    Button(
                        onClick = { onToggle(item.no) },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (open) Color(0xFF323A55) else StudyPurpleA
                        ),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(if (open) "उत्तर लुकाउनुहोस्" else "उत्तर हेर्नुहोस्")
                    }

                    if (open) {
                        Spacer(Modifier.height(12.dp))
                        Surface(
                            color = Color(0xFF10192D),
                            shape = RoundedCornerShape(15.dp),
                            border = BorderStroke(1.dp, Color(0xFF263A5B)),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(Modifier.padding(14.dp)) {
                                Text("उत्तर", color = StudyGreenA, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                Spacer(Modifier.height(6.dp))
                                Text(item.answer, color = StudyTextA, fontSize = 14.sp, lineHeight = 21.sp)
                            }
                        }
                    }
                }
            }
            Spacer(Modifier.height(9.dp))
        }
        Spacer(Modifier.height(30.dp))
    }
}

@Composable
private fun TextContentPageV5(
    title: String,
    subtitle: String,
    text: String,
    thinking: Boolean,
    loadingTitle: String,
    onBack: () -> Unit
) {
    StudyPageContainerV5 {
        StudyHeaderV5(title, subtitle, onBack)
        Spacer(Modifier.height(20.dp))
        if (thinking) {
            LoadingCardV5(loadingTitle)
        } else {
            Surface(
                color = StudyPanelA,
                shape = RoundedCornerShape(20.dp),
                border = BorderStroke(1.dp, StudyStrokeA),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text,
                    color = StudyTextA,
                    fontSize = 16.sp,
                    lineHeight = 24.sp,
                    modifier = Modifier.padding(17.dp)
                )
            }
        }
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun StudyPageContainerV5(content: @Composable ColumnScope.() -> Unit) {
    Box(
        Modifier.fillMaxSize().background(
            Brush.verticalGradient(listOf(StudyBgA, StudyBgB))
        )
    ) {
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),
            content = content
        )
    }
}

@Composable
private fun StudyHeaderV5(title: String, subtitle: String, onBack: () -> Unit) {
    Row(
        Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Surface(
            modifier = Modifier.size(43.dp).clickable { onBack() },
            shape = CircleShape,
            color = StudyPanelA,
            border = BorderStroke(1.dp, StudyStrokeA)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text("←", color = StudyTextA, fontSize = 23.sp)
            }
        }
        Spacer(Modifier.width(11.dp))
        Column {
            Text(title, color = StudyTextA, fontSize = 24.sp, fontWeight = FontWeight.Black)
            Text(subtitle, color = StudySoftA, fontSize = 11.sp)
        }
    }
}

@Composable
private fun SourceBadgeV5(badge: String, sourceCount: Int, onRefresh: () -> Unit) {
    Surface(
        color = Color(0xFF102C25),
        shape = RoundedCornerShape(15.dp),
        border = BorderStroke(1.dp, Color(0xFF245546)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    if (badge.isBlank()) "● अनलाइन स्रोत" else badge,
                    color = StudyGreenA,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp
                )
                Text("$sourceCount स्रोत जाँचिएको", color = StudySoftA, fontSize = 10.sp)
            }
            TextButton(onClick = onRefresh) { Text("फेरि खोज") }
        }
    }
}

@Composable
private fun QuestionTagV5(text: String) {
    Surface(color = Color(0xFF25213F), shape = RoundedCornerShape(50.dp)) {
        Text(
            text,
            color = StudyYellowA,
            fontSize = 9.sp,
            maxLines = 1,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 5.dp)
        )
    }
}

@Composable
private fun LoadingCardV5(title: String) {
    Surface(
        color = StudyPanelA,
        shape = RoundedCornerShape(18.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            Modifier.padding(18.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            CircularProgressIndicator(color = StudyCyanA)
            Spacer(Modifier.height(10.dp))
            Text(title, color = StudyTextA, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
private fun ToolGridV5(tools: List<Triple<String, String, () -> Unit>>) {
    tools.chunked(2).forEach { row ->
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            row.forEach { tool ->
                Surface(
                    modifier = Modifier.weight(1f).height(105.dp).clickable { tool.third() },
                    color = StudyPanelA,
                    shape = RoundedCornerShape(18.dp),
                    border = BorderStroke(1.dp, StudyStrokeA)
                ) {
                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.Center) {
                        Text(tool.first, fontSize = 22.sp)
                        Spacer(Modifier.height(7.dp))
                        Text(
                            tool.second,
                            color = StudyTextA,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            lineHeight = 17.sp
                        )
                    }
                }
            }
            if (row.size == 1) Spacer(Modifier.weight(1f))
        }
        Spacer(Modifier.height(8.dp))
    }
}

@Composable
private fun SubjectRowV5(subject: String, selected: Boolean, onClick: () -> Unit) {
    Surface(
        modifier = Modifier.fillMaxWidth().clickable { onClick() },
        color = if (selected) Color(0xFF263A5B) else StudyPanelB,
        shape = RoundedCornerShape(14.dp),
        border = BorderStroke(1.dp, if (selected) StudyCyanA else StudyStrokeA)
    ) {
        Row(Modifier.padding(horizontal = 13.dp, vertical = 11.dp)) {
            Text(if (selected) "✓" else "•", color = StudyCyanA)
            Spacer(Modifier.width(9.dp))
            Text(
                subject,
                color = StudyTextA,
                fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium
            )
        }
    }
}

@Composable
private fun GradeChipV5(
    grade: Int,
    selected: Boolean,
    modifier: Modifier,
    onClick: () -> Unit
) {
    Surface(
        modifier = modifier.height(48.dp).clickable { onClick() },
        color = if (selected) StudyPurpleA else StudyPanelA,
        shape = RoundedCornerShape(14.dp),
        border = BorderStroke(1.dp, if (selected) StudyPurpleA else StudyStrokeA)
    ) {
        Box(contentAlignment = Alignment.Center) {
            Text("$grade", color = Color.White, fontWeight = FontWeight.Black)
        }
    }
}

@Composable
private fun ChoiceChipV5(
    text: String,
    selected: Boolean,
    modifier: Modifier,
    onClick: () -> Unit
) {
    Surface(
        modifier = modifier.height(45.dp).clickable { onClick() },
        color = if (selected) Color(0xFF2B2559) else StudyPanelA,
        shape = RoundedCornerShape(13.dp),
        border = BorderStroke(1.dp, if (selected) StudyPurpleA else StudyStrokeA)
    ) {
        Box(contentAlignment = Alignment.Center) {
            Text(
                text,
                color = StudyTextA,
                fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium
            )
        }
    }
}
