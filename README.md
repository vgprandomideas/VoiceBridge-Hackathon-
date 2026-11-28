# VoiceBridge

**Assistive multilingual communication for people who need assistance and their caregivers.**

Scaler × Wispr Flow Hackathon — working prototype submission (Streamlit edition).

[Live prototype](https://voicebridgesolutions.streamlit.app/)

## Problem and solution
People with speech difficulties, age-related limitations or language barriers may struggle to communicate everyday needs. VoiceBridge provides private two-way conversations, quick pictogram requests, text, original voice recordings and caregiver groups.

## Run with Docker
Prerequisites: Docker with Compose and internet access for the initial build.

```sh
docker compose up --build
```

Open http://localhost:3000. No API key or .env file is required for core startup. Stop with Ctrl+C, or `docker compose down` from another terminal.

## Evaluator walkthrough
1. Open the app in two independent browser sessions (one may be incognito).
2. Choose caregiver in one session and create a connection code.
3. Choose assistance in the other session and enter the code within three minutes.
4. Select a quick phrase or type a message, then send it.
5. Read, listen, acknowledge and reply from the caregiver session.
6. Try original voice recording and playback, or select a preferred language for incoming text translation.
7. Try creating a care group with multiple people. Each receiver has a separate conversation.

Either role can initiate a connection. For local Docker testing, enter the code manually; shared links default to the hosted demo unless VOICEBRIDGE_PUBLIC_URL is configured.

## Wispr Flow
Select Dictate with Wispr Flow, focus the message field and activate Flow on a supported device. Review the inserted text before sending. Integration is device-level dictation, not a direct Wispr API. Typing and quick phrases remain available without Flow.

## Dependencies and fallback
- Python, Streamlit and SQLite: core application and local storage.
- Browser speech synthesis and microphone: device-dependent playback and recording.
- Experimental external text translation: internet required; original text remains available if translation fails.
- Optional OpenAI transcription: OPENAI_API_KEY enables transcription of recorded audio; otherwise use original audio, typing or Wispr dictation. No key required for startup.

## Safety and prototype limitations
Use synthetic demonstration data only. Not a clinical or emergency service. Translation can be inaccurate. Connection codes are bearer credentials; share privately. Hosted SQLite data may reset. Production authentication, retention controls and clinical validation are outside this prototype.

## Repository layout
- `streamlit_app.py`: primary application.
- `Dockerfile`, `docker-compose.yml`: container launch configuration.
- `requirements.txt`: Python dependencies.
- `.github/workflows/`: verification and runner diagnostics.
- Legacy JavaScript files are retained but are not the primary Docker entrypoint.

## Verification status
Docker startup configuration is present. GitHub-hosted diagnostic jobs failed before recording execution steps on Ubuntu and Windows; Docker runtime verification is still pending. Do not interpret the diagnostic failure as a successful application test.

## Provenance
Existing VoiceBridge hackathon prototype and subsequent Streamlit adaptation. Pre-hackathon code must not be counted toward originality requirements. Organizer starter-template compliance and eligibility require confirmation.
