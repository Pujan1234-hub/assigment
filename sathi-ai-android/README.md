# SATHI AI — Android Study Upgrade

This folder is being developed on the separate branch `sathi-ai-online-study` so the existing `main` branch projects (FloodSafe, DateMate, FixCheck, etc.) are not modified.

## Current focus

The Study module is being rebuilt as a Nepal-first exam preparation hub rather than a generic AI chat page.

### Online source-backed features

- Class 8–12 subject selection
- Nepali / Roman Nepali / English input
- Nepali or English answer mode
- Online lesson/chapter discovery from CDC/NEB-oriented sources
- Online model/past-paper question discovery
- Removes curriculum/meta questions such as “What is CDC?” or “What is a specification grid?”
- Question cards with hidden answers
- Source label/link on each question
- Refresh-online button
- 24-hour question-bank cache and 7-day lesson-list cache to reduce API credit usage
- Model paper, MCQ, practical, revision, custom tutoring and answer checking remain available

## New source files

- `app/src/main/java/com/sathiai/app/StudyOnlineRepository.kt`
- `app/src/main/java/com/sathiai/app/StudyModule.kt`

The Android app should keep using the existing `SathiSecrets.GEMINI_API_KEY` and `SathiSecrets.TAVILY_API_KEY`; API keys must never be committed to GitHub.

## Important

Online question-bank mode searches for real model/past-paper/question-pattern sources, then builds a source-backed practice bank. It intentionally rejects filler/meta questions. For non-official sources, the app may present a close practice paraphrase instead of copying an entire paper verbatim.
