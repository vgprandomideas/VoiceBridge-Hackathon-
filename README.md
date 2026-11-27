# VoiceBridge — Hackathon prototype

Primary submission: Streamlit edition. Live demo: https://voicebridgesolutions.streamlit.app/

## Run locally
`docker compose up --build` then open http://localhost:3000. No secrets or .env required. Initial dependency downloads need internet.

## Demo
Choose caregiver, create a group, add a resident, copy their private code. In a separate browser session choose assistance and connect with that code. Select a quick request, review and send. Caregiver reads, listens, acknowledges and replies. Use Wispr Flow device dictation in the message field. Browser playback depends on device support. Use synthetic data only; not an emergency service.

## Dependencies and limitations
Python, Streamlit, SQLite, browser speech synthesis. No paid API required. Typing and quick phrases remain available if speech playback fails. No automatic transcription or translation in this edition. Cloud storage may reset. Access codes are bearer credentials; keep private. Legacy JavaScript source remains in this repository but is not the primary Docker entrypoint.

## Provenance
Existing VoiceBridge hackathon prototype and subsequent Streamlit adaptation. Do not count pre-hackathon code toward originality requirements. Organizer starter-template compliance and eligibility require confirmation.
