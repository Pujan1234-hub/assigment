package com.sathiai.app

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale


data class StudyOnlineSource(
    val title: String,
    val url: String,
    val snippet: String = ""
)

data class StudyLessonItem(
    val no: Int,
    val title: String,
    val summary: String,
    val sourceTitle: String = "",
    val sourceUrl: String = ""
)

data class StudyQuestionItem(
    val no: Int,
    val type: String,
    val question: String,
    val answer: String,
    val priority: String = "महत्त्वपूर्ण",
    val sourceTitle: String = "",
    val sourceUrl: String = ""
)

data class StudyQuestionBankResult(
    val questions: List<StudyQuestionItem>,
    val sources: List<StudyOnlineSource>,
    val fromCache: Boolean = false
)

data class StudyLessonResult(
    val lessons: List<StudyLessonItem>,
    val sources: List<StudyOnlineSource>,
    val fromCache: Boolean = false
)

class StudyOnlineRepository(context: Context) {

    private val prefs = context.applicationContext.getSharedPreferences(
        "sathi_study_online_v1",
        Context.MODE_PRIVATE
    )

    fun loadImportantQuestions(
        grade: Int,
        subject: String,
        englishAnswer: Boolean,
        forceRefresh: Boolean = false,
        onResult: (StudyQuestionBankResult) -> Unit,
        onError: (String) -> Unit
    ) {
        val cacheKey = "questions_${grade}_${subject}_${if (englishAnswer) "en" else "np"}"

        if (!forceRefresh) {
            readQuestionCache(cacheKey, 24 * 60 * 60 * 1000L)?.let {
                onResult(it.copy(fromCache = true))
                return
            }
        }

        Thread {
            try {
                val sources = searchQuestionSources(grade, subject)

                if (sources.isEmpty()) {
                    onError("अनलाइनमा उपयोगी परीक्षा स्रोत भेटिएन। फेरि प्रयास गर्नुहोस्।")
                    return@Thread
                }

                val extracted = buildQuestionBank(
                    grade = grade,
                    subject = subject,
                    englishAnswer = englishAnswer,
                    sources = sources
                )

                if (extracted.isEmpty()) {
                    onError("अनलाइन स्रोतबाट वास्तविक परीक्षा ढाँचाका प्रश्न छुट्याउन सकिएन।")
                    return@Thread
                }

                val result = StudyQuestionBankResult(
                    questions = extracted,
                    sources = sources.take(6)
                )

                writeQuestionCache(cacheKey, result)
                onResult(result)
            } catch (_: Exception) {
                onError("अनलाइन प्रश्न बैंक खोल्दा समस्या आयो।")
            }
        }.start()
    }

    fun loadLessons(
        grade: Int,
        subject: String,
        englishAnswer: Boolean,
        forceRefresh: Boolean = false,
        onResult: (StudyLessonResult) -> Unit,
        onError: (String) -> Unit
    ) {
        val cacheKey = "lessons_${grade}_${subject}_${if (englishAnswer) "en" else "np"}"

        if (!forceRefresh) {
            readLessonCache(cacheKey, 7 * 24 * 60 * 60 * 1000L)?.let {
                onResult(it.copy(fromCache = true))
                return
            }
        }

        Thread {
            try {
                val sources = searchLessonSources(grade, subject)

                if (sources.isEmpty()) {
                    onError("चालु पाठ्यक्रमका पाठहरूको स्रोत भेटिएन।")
                    return@Thread
                }

                val lessons = buildLessonList(
                    grade = grade,
                    subject = subject,
                    englishAnswer = englishAnswer,
                    sources = sources
                )

                if (lessons.isEmpty()) {
                    onError("पाठहरूको सूची प्रमाणित गर्न सकिएन।")
                    return@Thread
                }

                val result = StudyLessonResult(
                    lessons = lessons,
                    sources = sources.take(5)
                )

                writeLessonCache(cacheKey, result)
                onResult(result)
            } catch (_: Exception) {
                onError("पाठ्यक्रम खोज्दा समस्या आयो।")
            }
        }.start()
    }

    private fun searchQuestionSources(grade: Int, subject: String): List<StudyOnlineSource> {
        val subjectQuery = searchSubjectName(subject)
        val examQuery = when (grade) {
            10 -> "SEE class 10"
            12 -> "NEB class 12 board"
            11 -> "NEB class 11 annual"
            9 -> "class 9 annual exam Nepal"
            else -> "class 8 basic level exam Nepal"
        }

        val query = "$examQuery $subjectQuery model question past question practice paper PDF Nepal 2080 2081 2082 2083"

        return tavilySearch(
            query = query,
            maxResults = 8,
            includeRaw = true,
            boostOfficial = true
        )
    }

    private fun searchLessonSources(grade: Int, subject: String): List<StudyOnlineSource> {
        val subjectQuery = searchSubjectName(subject)
        val query = "Nepal CDC class $grade $subjectQuery textbook curriculum chapter lesson contents PDF"

        return tavilySearch(
            query = query,
            maxResults = 6,
            includeRaw = true,
            boostOfficial = true
        )
    }

    private fun tavilySearch(
        query: String,
        maxResults: Int,
        includeRaw: Boolean,
        boostOfficial: Boolean
    ): List<StudyOnlineSource> {
        val key = SathiSecrets.TAVILY_API_KEY
        if (key.isBlank() || key.contains("YETA_")) {
            throw IllegalStateException("Tavily key missing")
        }

        val connection = URL("https://api.tavily.com/search").openConnection() as HttpURLConnection
        connection.requestMethod = "POST"
        connection.setRequestProperty("Content-Type", "application/json")
        connection.setRequestProperty("Authorization", "Bearer $key")
        connection.doOutput = true
        connection.connectTimeout = 8000
        connection.readTimeout = 18000

        val body = JSONObject().apply {
            put("query", query)
            put("search_depth", "basic")
            put("chunks_per_source", 3)
            put("max_results", maxResults)
            put("topic", "general")
            put("country", "nepal")
            put("include_answer", false)
            put("include_raw_content", if (includeRaw) "text" else false)
            put("include_images", false)
            put("safe_search", true)

            if (boostOfficial) {
                put(
                    "include_domains",
                    JSONArray().apply {
                        put("moecdc.gov.np")
                        put("neb.gov.np")
                        put("cehrd.gov.np")
                    }
                )
                put("include_domains_mode", "boost")
            }
        }

        connection.outputStream.use {
            it.write(body.toString().toByteArray())
        }

        val responseCode = connection.responseCode
        val responseText = if (responseCode in 200..299) {
            connection.inputStream.bufferedReader().use { it.readText() }
        } else {
            connection.errorStream?.bufferedReader()?.use { it.readText() } ?: ""
        }

        connection.disconnect()
        if (responseCode !in 200..299) {
            throw IllegalStateException("Tavily error $responseCode")
        }

        val root = JSONObject(responseText)
        val results = root.optJSONArray("results") ?: return emptyList()
        val list = mutableListOf<StudyOnlineSource>()

        for (i in 0 until results.length()) {
            val item = results.optJSONObject(i) ?: continue
            val title = item.optString("title").trim()
            val url = item.optString("url").trim()
            val content = item.optString("content").trim()
            val raw = item.optString("raw_content").trim()

            if (url.isBlank()) continue

            val combined = buildString {
                if (content.isNotBlank()) appendLine(content)
                if (raw.isNotBlank()) {
                    append(if (raw.length > 7000) raw.take(7000) else raw)
                }
            }.trim()

            list.add(
                StudyOnlineSource(
                    title = if (title.isBlank()) "अनलाइन स्रोत" else title,
                    url = url,
                    snippet = combined
                )
            )
        }

        return list.distinctBy { it.url }
    }

    private fun buildQuestionBank(
        grade: Int,
        subject: String,
        englishAnswer: Boolean,
        sources: List<StudyOnlineSource>
    ): List<StudyQuestionItem> {
        val sourceText = buildString {
            sources.forEachIndexed { index, source ->
                appendLine("SOURCE ${index + 1}")
                appendLine("TITLE: ${source.title}")
                appendLine("URL: ${source.url}")
                appendLine("CONTENT:")
                appendLine(source.snippet)
                appendLine("---")
            }
        }

        val languageRule = if (englishAnswer) {
            "Return explanations/answers in clear English. Preserve the natural language of the question when needed."
        } else {
            "उत्तर र व्याख्या नेपालीमा देऊ। English subject का original question/sentence English मै राख्न मिल्छ।"
        }

        val prompt = """
You are building a Nepal school exam-preparation question bank.
Grade: $grade
Subject: $subject
$languageRule

Below are REAL ONLINE SEARCH SOURCES. Create a SOURCE-BACKED practice bank from actual exam/model/past-question patterns visible in those sources.

STRICT RULES:
1. NEVER create meta questions like "What is CDC curriculum?", "What is a specification grid?", or "What is the exam style?".
2. NEVER use a page title, curriculum description, source metadata, or search-result description as an exam question.
3. Use actual question wording when it is short and clearly visible in an official/public exam/model source. Otherwise create a close practice paraphrase based on the visible question pattern/topic.
4. Prefer recurring/high-value question patterns found across sources.
5. Cover different chapters/skills.
6. If the sources do not contain enough real question material, return FEWER questions. Do not invent filler.
7. Answers may be freshly solved by you, but must be correct for Grade $grade.
8. For maths/science/accounting calculations, show essential steps in the answer.
9. For English subject, include reading/grammar/writing/language-use questions rather than questions about the curriculum itself.
10. Each item must cite one source from the supplied list.
11. Priority must be one of: "अति महत्त्वपूर्ण", "महत्त्वपूर्ण", "अभ्यास".
12. Return ONLY valid JSON array.

JSON format:
[
  {
    "no": 1,
    "type": "छोटो / लामो / गणनात्मक / व्याकरण / लेखन / पठन",
    "question": "question text",
    "answer": "hidden model answer",
    "priority": "अति महत्त्वपूर्ण",
    "sourceIndex": 1
  }
]

Aim for 20-30 items only when the sources genuinely support them.

SOURCES:
$sourceText
""".trimIndent()

        val raw = geminiText(prompt, maxOutputTokens = 5000)
        val arr = JSONArray(extractJsonArray(raw))
        val result = mutableListOf<StudyQuestionItem>()

        for (i in 0 until arr.length()) {
            val obj = arr.optJSONObject(i) ?: continue
            val question = obj.optString("question").trim()
            val answer = obj.optString("answer").trim()
            val sourceIndex = obj.optInt("sourceIndex", 1) - 1
            val source = sources.getOrNull(sourceIndex)

            if (question.isBlank() || answer.isBlank()) continue
            if (looksLikeMetaQuestion(question)) continue

            result.add(
                StudyQuestionItem(
                    no = result.size + 1,
                    type = obj.optString("type", "अभ्यास").trim(),
                    question = question,
                    answer = answer,
                    priority = obj.optString("priority", "महत्त्वपूर्ण").trim(),
                    sourceTitle = source?.title.orEmpty(),
                    sourceUrl = source?.url.orEmpty()
                )
            )
        }

        return result
    }

    private fun buildLessonList(
        grade: Int,
        subject: String,
        englishAnswer: Boolean,
        sources: List<StudyOnlineSource>
    ): List<StudyLessonItem> {
        val sourceText = buildString {
            sources.forEachIndexed { index, source ->
                appendLine("SOURCE ${index + 1}: ${source.title}")
                appendLine("URL: ${source.url}")
                appendLine(source.snippet)
                appendLine("---")
            }
        }

        val languageRule = if (englishAnswer) {
            "Write summaries in English."
        } else {
            "summary नेपालीमा लेख। Subject/lesson title को official wording नबिगार।"
        }

        val prompt = """
You are extracting the current Nepal CDC textbook/curriculum lesson list.
Grade: $grade
Subject: $subject
$languageRule

Rules:
1. Use the supplied online sources only.
2. Prefer official CDC/NEB sources when there is disagreement.
3. Extract actual chapter/unit/lesson titles, not curriculum headings or website navigation.
4. Do not invent missing chapters.
5. Put them in teaching order when the source makes the order clear.
6. Return ONLY valid JSON array.

Format:
[
  {
    "no": 1,
    "title": "official lesson/unit title",
    "summary": "one short sentence",
    "sourceIndex": 1
  }
]

SOURCES:
$sourceText
""".trimIndent()

        val raw = geminiText(prompt, maxOutputTokens = 3000)
        val arr = JSONArray(extractJsonArray(raw))
        val result = mutableListOf<StudyLessonItem>()

        for (i in 0 until arr.length()) {
            val obj = arr.optJSONObject(i) ?: continue
            val title = obj.optString("title").trim()
            val sourceIndex = obj.optInt("sourceIndex", 1) - 1
            val source = sources.getOrNull(sourceIndex)
            if (title.isBlank()) continue

            result.add(
                StudyLessonItem(
                    no = result.size + 1,
                    title = title,
                    summary = obj.optString("summary").trim(),
                    sourceTitle = source?.title.orEmpty(),
                    sourceUrl = source?.url.orEmpty()
                )
            )
        }

        return result
    }

    private fun geminiText(prompt: String, maxOutputTokens: Int): String {
        val key = SathiSecrets.GEMINI_API_KEY
        if (key.isBlank() || key.contains("YETA_")) {
            throw IllegalStateException("Gemini key missing")
        }

        val connection = URL(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
        ).openConnection() as HttpURLConnection

        connection.requestMethod = "POST"
        connection.setRequestProperty("Content-Type", "application/json")
        connection.setRequestProperty("x-goog-api-key", key)
        connection.doOutput = true
        connection.connectTimeout = 8000
        connection.readTimeout = 30000

        val body = JSONObject().apply {
            put(
                "contents",
                JSONArray().apply {
                    put(
                        JSONObject().apply {
                            put("role", "user")
                            put(
                                "parts",
                                JSONArray().apply {
                                    put(JSONObject().apply { put("text", prompt) })
                                }
                            )
                        }
                    )
                }
            )
            put(
                "generationConfig",
                JSONObject().apply {
                    put("maxOutputTokens", maxOutputTokens)
                    put("temperature", 0.12)
                    put("responseMimeType", "application/json")
                }
            )
        }

        connection.outputStream.use {
            it.write(body.toString().toByteArray())
        }

        val code = connection.responseCode
        val text = if (code in 200..299) {
            connection.inputStream.bufferedReader().use { it.readText() }
        } else {
            connection.errorStream?.bufferedReader()?.use { it.readText() } ?: ""
        }

        connection.disconnect()
        if (code !in 200..299) {
            throw IllegalStateException("Gemini error $code")
        }

        val root = JSONObject(text)
        val parts = root.optJSONArray("candidates")
            ?.optJSONObject(0)
            ?.optJSONObject("content")
            ?.optJSONArray("parts")

        return parts?.optJSONObject(0)?.optString("text").orEmpty()
    }

    private fun looksLikeMetaQuestion(question: String): Boolean {
        val q = question.lowercase(Locale.getDefault())
        val banned = listOf(
            "cdc/neb पाठ्यक्रम",
            "cdc पाठ्यक्रम",
            "specification grid",
            "विशिष्टीकरण तालिका कस्तो",
            "परीक्षा शैली कस्तो",
            "curriculum कस्तो",
            "what is the curriculum",
            "what is cdc",
            "what is neb"
        )
        return banned.any { q.contains(it) }
    }

    private fun searchSubjectName(subject: String): String {
        return when (subject) {
            "नेपाली" -> "Nepali"
            "अङ्ग्रेजी" -> "English"
            "गणित" -> "Mathematics Math"
            "विज्ञान तथा प्रविधि" -> "Science and Technology"
            "सामाजिक अध्ययन" -> "Social Studies"
            "सामाजिक अध्ययन तथा मानव मूल्य शिक्षा" -> "Social Studies and Human Values Education"
            "स्वास्थ्य, शारीरिक शिक्षा तथा सिर्जनात्मक कला" -> "Health Physical Education Creative Arts"
            "ऐच्छिक गणित" -> "Optional Mathematics"
            "कम्प्युटर विज्ञान" -> "Computer Science"
            "लेखा", "लेखाशास्त्र" -> "Accountancy Accounting"
            "अर्थशास्त्र" -> "Economics"
            "भौतिक विज्ञान" -> "Physics"
            "रसायन विज्ञान" -> "Chemistry"
            "जीव विज्ञान" -> "Biology"
            "व्यवसाय अध्ययन" -> "Business Studies"
            "होटल व्यवस्थापन" -> "Hotel Management"
            else -> subject
        }
    }

    private fun extractJsonArray(raw: String): String {
        val clean = raw.replace("```json", "").replace("```", "").trim()
        val start = clean.indexOf('[')
        val end = clean.lastIndexOf(']')
        return if (start >= 0 && end > start) clean.substring(start, end + 1) else clean
    }

    private fun writeQuestionCache(key: String, result: StudyQuestionBankResult) {
        val obj = JSONObject().apply {
            put("savedAt", System.currentTimeMillis())
            put(
                "questions",
                JSONArray().apply {
                    result.questions.forEach { q ->
                        put(
                            JSONObject().apply {
                                put("no", q.no)
                                put("type", q.type)
                                put("question", q.question)
                                put("answer", q.answer)
                                put("priority", q.priority)
                                put("sourceTitle", q.sourceTitle)
                                put("sourceUrl", q.sourceUrl)
                            }
                        )
                    }
                }
            )
            put("sources", sourceArray(result.sources))
        }
        prefs.edit().putString(key, obj.toString()).apply()
    }

    private fun readQuestionCache(key: String, maxAge: Long): StudyQuestionBankResult? {
        val raw = prefs.getString(key, null) ?: return null
        return try {
            val obj = JSONObject(raw)
            val saved = obj.optLong("savedAt", 0L)
            if (System.currentTimeMillis() - saved > maxAge) return null

            val qArr = obj.optJSONArray("questions") ?: JSONArray()
            val questions = mutableListOf<StudyQuestionItem>()
            for (i in 0 until qArr.length()) {
                val q = qArr.optJSONObject(i) ?: continue
                questions.add(
                    StudyQuestionItem(
                        no = q.optInt("no", i + 1),
                        type = q.optString("type"),
                        question = q.optString("question"),
                        answer = q.optString("answer"),
                        priority = q.optString("priority"),
                        sourceTitle = q.optString("sourceTitle"),
                        sourceUrl = q.optString("sourceUrl")
                    )
                )
            }

            StudyQuestionBankResult(
                questions = questions,
                sources = parseSources(obj.optJSONArray("sources")),
                fromCache = true
            )
        } catch (_: Exception) {
            null
        }
    }

    private fun writeLessonCache(key: String, result: StudyLessonResult) {
        val obj = JSONObject().apply {
            put("savedAt", System.currentTimeMillis())
            put(
                "lessons",
                JSONArray().apply {
                    result.lessons.forEach { lesson ->
                        put(
                            JSONObject().apply {
                                put("no", lesson.no)
                                put("title", lesson.title)
                                put("summary", lesson.summary)
                                put("sourceTitle", lesson.sourceTitle)
                                put("sourceUrl", lesson.sourceUrl)
                            }
                        )
                    }
                }
            )
            put("sources", sourceArray(result.sources))
        }
        prefs.edit().putString(key, obj.toString()).apply()
    }

    private fun readLessonCache(key: String, maxAge: Long): StudyLessonResult? {
        val raw = prefs.getString(key, null) ?: return null
        return try {
            val obj = JSONObject(raw)
            val saved = obj.optLong("savedAt", 0L)
            if (System.currentTimeMillis() - saved > maxAge) return null

            val arr = obj.optJSONArray("lessons") ?: JSONArray()
            val lessons = mutableListOf<StudyLessonItem>()
            for (i in 0 until arr.length()) {
                val item = arr.optJSONObject(i) ?: continue
                lessons.add(
                    StudyLessonItem(
                        no = item.optInt("no", i + 1),
                        title = item.optString("title"),
                        summary = item.optString("summary"),
                        sourceTitle = item.optString("sourceTitle"),
                        sourceUrl = item.optString("sourceUrl")
                    )
                )
            }

            StudyLessonResult(
                lessons = lessons,
                sources = parseSources(obj.optJSONArray("sources")),
                fromCache = true
            )
        } catch (_: Exception) {
            null
        }
    }

    private fun sourceArray(sources: List<StudyOnlineSource>): JSONArray {
        return JSONArray().apply {
            sources.forEach { source ->
                put(
                    JSONObject().apply {
                        put("title", source.title)
                        put("url", source.url)
                        put("snippet", source.snippet)
                    }
                )
            }
        }
    }

    private fun parseSources(arr: JSONArray?): List<StudyOnlineSource> {
        if (arr == null) return emptyList()
        val result = mutableListOf<StudyOnlineSource>()
        for (i in 0 until arr.length()) {
            val item = arr.optJSONObject(i) ?: continue
            result.add(
                StudyOnlineSource(
                    title = item.optString("title"),
                    url = item.optString("url"),
                    snippet = item.optString("snippet")
                )
            )
        }
        return result
    }
}
