# SATHI AI — नेपाली Personal AI Android Foundation

मुख्य app Personal AI हो; Study केवल एउटा feature हो।

अहिले: Nepali-only TTS/STT request, foreground background listener, ‘साथी’ wake phrase, camera/settings/maps/web-search commands, notification listener skeleton, Class 8–12 study feature shell.

Android limitation: microphone background listening का लागि persistent foreground-service notification चाहिन्छ। App Force stop गरेपछि wake listening चल्दैन। पछि Default Assistant/VoiceInteractionService र dedicated local wake-word engine थपिन्छ।

Spoken output मा English/Hindi fallback छैन। Phone मा ne-NP voice नभए dedicated Nepali voice engine अर्को चरणमा bundle गरिन्छ।
