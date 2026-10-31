# FloodSafe Nepal v0.9.21 — Android Beta Test 🇳🇵

**FloodSafe Nepal** is an independently developed flood-awareness and public-safety information app for Nepal, created under **PJBUILTS** by **Pujan Chapagain**. The goal is to make available river-gauge observations, weather conditions, and safety information easier to find and understand on a mobile phone.

> **Status: BETA / TEST BUILD.** This is not a Government of Nepal app or a replacement for official emergency warnings. Some features still require field testing in Nepal. Always follow official DHM, NDRRMA, and local-authority instructions in an emergency.

## 📱 Download the current Android beta

- **[Download FloodSafe Nepal Android Beta APK](https://github.com/Pujan1234-hub/assigment/releases/download/floodsafe-v0921-last-reading-test-20261030/FloodSafe-Nepal-Android-Beta.apk)**
- **[Project website and download page](https://pjbuilts.com/floodsafe-nepal/)**

The two APK filenames attached to this release contain the **same tested binary** (about 99.36 MB). This build installs as **FloodSafe Nepal TEST** under a separate preview package, so it does not overwrite the regular FloodSafe Nepal app. Google Play Store closed testing has **not yet been published** from this preview APK. iPhone/iOS support is planned, but no iOS app is available yet.

## 🌊 What is included

- **Nepal river monitoring:** Map of available river-monitoring stations, with station details and district-based exploration.
- **Official-data integration:** Uses available DHM observations, with BIPAD data as a fallback when appropriate. Source availability may change.
- **Reading freshness:** Shows the observation time and differentiates recent readings from older or unavailable data. A historical reading is **not** presented as a live measurement.
- **Weather and rainfall:** Local weather context, rainfall information and related advisory content.
- **Location-aware experience:** Nearby stations and monitoring context, subject to location permission and available information.
- **Nepali and English:** Bilingual app information and educational content.
- **Notifications:** Firebase-powered service notices and an official-data river-alert system with local safety filters.
- **Safe content updates:** Some in-app announcements, curated knowledge and help content can refresh without reinstalling the APK.
- **SATHI:** In-app information and safety-guidance assistant.

## ✅ What was actually tested

- Android beta opened and was exercised on **Samsung Galaxy Z Fold 6** and **Redmi Note 14 Pro 5G**.
- A **non-emergency Firebase notification** was received on **both phones**.
- In-app OTA notice **ON/OFF** and updated text were checked.
- The Android test build passed its CI build/unit-test checks.

**Not yet verified:** Real-world Nepal GPS/nearby-river alert delivery across hazard scenarios, all device/OS combinations, and final Play Store release requirements. A successful general test notification **does not** certify real flood-alert delivery.

## 🛠️ v0.9.21 change: last verified station reading

For grey/inactive or stale stations, the detail view may show the **last source-verified water-level measurement and its observation time**, explicitly labelled as historical **NOT LIVE**. If no verifiable measurement and timestamp exist, the reading remains unavailable. This change does **not** turn old data into a fresh warning.

The existing map appearance, river glow, weather visuals, notifications, SATHI, languages and content OTA behavior were preserved.

## ⚠️ Important safety and privacy notes

- Official stations or forecasts may temporarily be unavailable. **Missing data is not proof of safety.**
- Real river-warning notifications require suitably recent verified observations and location checks; Nepal field validation remains pending.
- The app may request permissions such as notifications and location for relevant functions.
- This project **does not claim government affiliation, emergency-service authority, or guaranteed alert delivery**.

## 🗣️ नेपालीमा छोटो जानकारी

**FloodSafe Nepal** नेपालका नदी, मौसम र बाढी जोखिमसम्बन्धी उपलब्ध जानकारी मोबाइलमा सहज रूपमा हेर्न बनाइएको स्वतन्त्र परियोजना हो। अहिलेको **v0.9.21 Android Beta परीक्षण संस्करण** मा नदी स्टेशनको नक्सा, जिल्लाअनुसार खोजी, DHM/BIPAD बाट उपलब्ध मापन, मापनको समय, मौसम, वर्षा, नेपाली/अङ्ग्रेजी जानकारी र सूचना प्रणाली छन्।

पुरानो नदी मापन देखिए पनि त्यसलाई **हालको live अवस्था** भनेर जनाइँदैन। Samsung र Redmi दुवैमा **साधारण Firebase परीक्षण सूचना** सफल भएको छ; **नेपालमा वास्तविक नदी खतरा चेतावनीको field test बाँकी** छ। यो सरकारी एप होइन, आधिकारिक चेतावनीको विकल्प होइन।

**Developer:** Pujan Chapagain · **PJBUILTS** · https://pjbuilts.com

Feedback is welcome through the project website.