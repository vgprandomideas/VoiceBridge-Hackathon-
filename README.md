# VoiceBridge — Scaler × Wispr Flow prototype

Accessible private communication for residents and caregivers in India.

## Run
Install Docker with Compose, clone this repository, then run `docker compose up` and open http://localhost:3000. No secret keys or .env file are needed. Initial image and npm downloads require internet.

## Demo
Open /care.html, create a care group, add a resident, open the invitation in a second browser, send a request, play it aloud and reply. Use synthetic data. Wispr Flow can dictate into editable fields using its separately installed device controls. Browser speech recognition and playback depend on browser support, permissions and available voices. Cloudflare AI translation and server transcription are disabled locally; use original text or typing. This is not an emergency or clinical system.

## Dependencies
Node 22, Wrangler 4, local Durable Objects, browser speech APIs. No required environment variables. Optional cloud AI is not configured in this edition. Data persists in a local Docker volume.

## Tests
`node --test tests/care-group.test.mjs`. CI also attempts Docker startup and health checks. Check actual CI results before claiming a pass.

## Provenance
This edition imports the existing VoiceBridge prototype developed for the hackathon activities and adds local Docker packaging. Earlier development history remains in the original private repository. Eligibility and originality are subject to organizer rules.
