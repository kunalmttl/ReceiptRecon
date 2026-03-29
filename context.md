# Project: ReceiptRecon
Created: 2026-03-29

## What this is
ReceiptRecon is an AI-powered receipt scanning and return fraud detection platform. It consists of a React Native (Expo) frontend, a Node.js (Express) backend, and a Python (Flask) AI service for OCR and image analysis.

## Tech stack
- Frontend: React Native (Expo), Zusyand, Axios
- Backend: Node.js (Express), Supabase (PostgreSQL)
- AI Service: Python (Flask), Gemini 2.0 Flash (via OpenRouter)
- Database: Supabase (PostgreSQL)
- Deployment: Vercel (frontend) / Render (backend) [Planned]


## Project structure
- `frontend/`: Expo (React Native) mobile application
- `backend/`: Node.js Express API server
- `ai_service/`: Python Flask service for AI processing
- `reference_data/`: Brand info and logs for the AI service

## Key decisions
- Using OpenRouter to access Gemini 2.0 Flash for low-cost, high-performance image analysis.
- Multi-repo structure in a single workspace (mono-repo style).

## Environment variables needed
- Backend: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `PORT`, `AI_SERVICE_URL`
- AI Service: `OPENROUTER_API_KEY`, `YOUR_SITE_URL`, `YOUR_SITE_NAME`
- Frontend: `BACKEND_URL`


## Deployment
- Frontend URL: [fill when deployed]
- Supabase Project URL: https://eggznjggkywqlqjlzchn.supabase.co


## Error log
| Date | Error | Fix Applied |
|------|-------|-------------|
| 2026-03-29 | None | N/A |
