# Instant feedback push (staging only)
1. In Firebase project floodsafe-nepal register a separate Android app, package com.pjbuilts.floodsafefeedback. Download its google-services.json and put it at floodsafe-feedback-android/app/google-services.json (not the main app config).
2. In the new FloodSafe Feedback Supabase project only, add Edge Function secret FEEDBACK_FCM_SERVICE_ACCOUNT with Firebase service-account JSON for floodsafe-nepal and appropriate messaging permissions. Never commit or share the private key.
3. Run setup.sql in the new feedback project, then deploy index.ts as feedback-api with verify_jwt=false (existing public POST and separate admin authentication preserved). Verify old submission/read/update and new authenticated registration; no main app topics or data modified.
4. Compile v1.0.5, enable notification permissions and background alerts after first login. Test open, background, screen off. FCM is near-real-time, not guaranteed after force-stop/offline/DND.
Only one admin device registration is supported in this staged implementation. Generic push contains no feedback message/contact. Existing polling remains fallback.
