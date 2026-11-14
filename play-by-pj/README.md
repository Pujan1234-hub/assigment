# PLAY by PJ — VLC Decoder Edition 0.1.1

Android native player using actual VideoLAN LibVLC 3.7.7 (LGPL-2.1 library).
The app uses Android's Storage Access Framework and a seekable file descriptor for
local MP4/MKV/HEVC/MOV/AVI, with a software decoder retry if hardware decoding fails.
Supports HTTP(S) streams, playback controls, rate, scrubbing and on-device color looks.

This is a **new standalone preview project**, because the earlier chat ZIP was not
available in the connected GitHub account. Verify it on your device. Do not overwrite
production or imply every malformed/proprietary video codec will necessarily work.

Build: `gradle -p play-by-pj :app:assembleDebug` (JDK 17 / Android SDK 35)
APK package: `com.pjbuilts.playbypj`; no storage or notification permissions required.
`LibVLC` is VideoLAN software; retain its notices and LGPL compliance if distributed.
