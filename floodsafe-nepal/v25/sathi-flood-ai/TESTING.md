# Safe test checklist

This prototype is intentionally additive. Do not merge into `main` until the tests below pass.

1. Open `sathi-flood-ai/index.html` from the same origin as FloodSafe V25.
2. Confirm the existing V25 screen inside the frame is visually and functionally unchanged.
3. Open the robot button and type: `अहिले कुन नदीमा बाढीको जोखिम छ?`
4. Ask a named river question, for example: `कोशीको अवस्था कस्तो छ?`
5. Ask: `आज पानी कति बजे पर्छ र कहिले रोकिन्छ?`
6. Open the mobile keyboard and confirm the composer remains visible above the keyboard.
7. Tap the microphone and confirm one-shot voice input works where browser SpeechRecognition is supported.
8. Enable `Ye Sathi` and confirm it only listens while the test page is open. Native background wake support is a separate Android task.
9. Confirm no existing V25 file appears in the PR diff.
