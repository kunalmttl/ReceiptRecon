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
- `backend/`: Node.js Express API server (Root Repo) - Port 5000
- `ai_service/`: Python Flask service for AI processing (Root Repo) - Port 5002
- `frontend/`: Expo (React Native) mobile application (Frontend Repo - Git Subdirectory)
- `reference_data/`: Brand info and logs for the AI service
- `backend/seed.js`: Database initialization script

## Current Status
Backend and AI services are operational. Database has been migrated to Supabase. Frontend refactoring for UUID compatibility and multi-step return flow is complete. AI Service is ready for production deployment.

## Database Schema (Supabase)
- `profiles`: id (UUID), email, name, created_at
- `products`: id (UUID), name, brand, price, category, image_url, description (text), accessories (jsonb)
- `orders`: id (UUID), user_id, purchase_date, created_at
- `order_items`: id (UUID), order_id, product_id, quantity, price_at_purchase, return_status, return_reason, return_notes, return_initiated_at

## Key decisions
- **Supabase Migration:** Replaced MongoDB with Supabase for relational data handling (PostgreSQL) and better authentication integration.
- **Repository Strategy:** Separated Frontend and Backend/AI into independent GitHub repositories for cleaner deployment workflows.
- **AI Choice:** Using OpenRouter to access Gemini 2.0 Flash for low-cost, high-performance image analysis.

## Environment variables needed
- Backend: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `PORT`, `AI_SERVICE_URL`
- AI Service: `OPENROUTER_API_KEY`, `YOUR_SITE_URL`, `YOUR_SITE_NAME`
- Frontend: `EXPO_PUBLIC_BACKEND_URL`, `EXPO_PUBLIC_USER_ID`


## Deployment
- Frontend URL: [fill when deployed]
- Supabase Project URL: https://eggznjggkywqlqjlzchn.supabase.co


## Error log
| Date | Error | Fix Applied |
|------|-------|-------------|
| 2026-04-12 | `ECONNREFUSED ::1:5002` | Updated backend `.env` to use `127.0.0.1` instead of `localhost` to bypass IPv6 resolution mismatch. |
| 2026-04-12 | Missing `return_notes` column | Applied Supabase migration to add `return_notes` column to `order_items` table. |
| 2026-04-12 | Order Item Not Found (404) | Refined `initiateReturn` controller with better logging and explicit order ID verification. |
| 2026-04-12 | Orders not loading (Supabase) | Switched to SERVICE_ROLE_KEY to bypass RLS for custom header-based auth. |
| 2026-04-12 | Security Vulnerabilities | Patched Critical (Axios) and High (Lodash) vulnerabilities across Root, Backend, and Frontend using overrides and direct bumps. |
| 2026-04-12 | UnicodeDecodeError in AI Service | Specified encoding='utf-8' in open() call for brand_info.json in main.py. |
| 2026-04-12 | Port Conflict (5000) | Reassigned AI Service to port 5002 in main.py to allow Backend to run on 5000. |
| 2026-04-12 | wait-on hanging | Added /api/health endpoint to backend/server.js to satisfy development startup dependencies. |
| 2026-03-29 | replace_file_content mismatch | Used multi_replace or smaller chunks for products.tsx. |
| 2026-03-29 | _id property in key screens | Refactored to `id` (UUID) across all frontend components. |
| 2026-03-29 | Incorrect Port in root pkg.json | Verified `.env` PORT=5000 for backend health checks. |
| 2026-03-29 | ORDER_ID vs order_id | Normalized to `order_id` in navigation params. |
| 2026-03-29 | Retake Flow | Implemented `retriedSteps` logic in `failed.tsx` for smarter retries. |
| 2026-03-29 | Orders not loading | Updated frontend `.env` with localhost URL and added `EXPO_PUBLIC_USER_ID`. |
| 2026-03-29 | npx expo export error | Simplified `babel.config.js` and added `react-native-worklets-core` for Reanimated 4. |
