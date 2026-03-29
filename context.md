# Project: ReceiptRecon
Created: 2026-03-29

## What this is
ReceiptRecon is an AI-powered receipt scanning and return fraud detection platform. It consists of a React Native (Expo) frontend, a Node.js (Express) backend, and a Python (Flask) AI service for OCR and image analysis.

## Tech stack
- Frontend: React Native (Expo), Zustand (not Zusyand), Axios
- Backend: Node.js (Express)
- AI Service: Python (Flask), Gemini 2.0 Flash (via OpenRouter)
- Database: Supabase (PostgreSQL)
- Deployment: Vercel (frontend) / Render (backend)

## Repositories
- **Root (Backend + AI):** [kunalmttl/ReceiptRecon](https://github.com/kunalmttl/ReceiptRecon)
- **Frontend:** [kunalmttl/ReceiptRecon-frontend](https://github.com/kunalmttl/ReceiptRecon-frontend)

## Project structure
- `backend/`: Node.js Express API server (Root Repo)
- `ai_service/`: Python Flask service for AI processing (Root Repo)
- `frontend/`: Expo (React Native) mobile application (Frontend Repo - Git Subdirectory)
- `reference_data/`: Brand info and logs for the AI service

## Database Schema (Supabase)
- `profiles`: user_id (UUID), email, username, created_at
- `products`: id (UUID), name, brand, price, category, image_url
- `orders`: id (UUID), user_id, product_id, status (delivered/returned), return_reason, created_at

## Key decisions
- **Supabase Migration:** Replaced MongoDB with Supabase for relational data handling (PostgreSQL) and better authentication integration.
- **Repository Strategy:** Separated Frontend and Backend/AI into independent GitHub repositories for cleaner deployment workflows.
- **AI Choice:** Using OpenRouter to access Gemini 2.0 Flash for low-cost, high-performance image analysis.

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
