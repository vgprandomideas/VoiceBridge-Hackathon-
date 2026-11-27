# VoiceBridge — local competition prototype

Run `docker compose up` from the repository root. Open http://localhost:3000 and /care.html. Docker and internet access for the initial image and dependency download are required. No .env file or API keys are required. Local Durable Objects persist in the Docker volume.

## Core demonstration
Create a care group, add a resident, open their private invitation in another browser tab, send a request, play it aloud, and reply. Use a supported browser with installed speech voices. Browser dictation may require internet and microphone permission. Wispr Flow is an optional separately installed dictation application. The local configuration deliberately omits Workers AI: arbitrary translation and server transcription are unavailable; use original text, browser dictation or typing instead. Do not claim clinical or emergency reliability. Use synthetic data only.

## Verification
Run `node --test tests/care-group.test.mjs` with Node 22. Docker startup and physical audio must be verified before submission. The cloud deployment uses the separate wrangler.jsonc configuration.
