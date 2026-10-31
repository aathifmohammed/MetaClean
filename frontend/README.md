# MetaClean Frontend

React + Vite frontend for the MetaClean FastAPI backend.

## Requirements
- Node.js 20 or newer recommended
- The MetaClean FastAPI backend running at `http://127.0.0.1:8000`
- Google OAuth Web Client ID for sign-in-only features

## Setup

1. Extract this folder beside your backend folder (or wherever you keep frontend projects).
2. Open a terminal in `MetaClean-frontend`.
3. Install dependencies:

   ```bash
   npm install
   ```

4. Copy `.env.example` to `.env` and configure:

   ```dotenv
   VITE_API_BASE_URL=http://127.0.0.1:8000
   VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   ```

   Use the same Google Web Client ID as `GOOGLE_CLIENT_ID` in the backend `.env`. If you omit the Google ID, guest image checking and cleaning still work, but sign-in features remain unavailable.

5. Start the FastAPI backend in its own terminal:

   ```powershell
   python -m uvicorn app.main:app --reload
   ```

6. Start the frontend:

   ```bash
   npm run dev
   ```

7. Open `http://localhost:5173`.

## Backend connection

The frontend sends HTTP requests to `VITE_API_BASE_URL`. It expects the routes implemented by the current MetaClean backend:
- `POST /api/metadata/check` (multipart field `file`)
- `POST /api/metadata/clean` (multipart fields `file`, `mode` = `ai_only` or `all`)
- `GET /api/account/me`
- `GET /api/account/activities`
- `POST/GET/PATCH/DELETE /api/endpoints...`
- `GET /api/public/{endpoint_id}` and public image URLs

The frontend does not connect directly to MongoDB or Cloudflare R2. Those remain server-side integrations.

## Deploying frontend to Vercel

1. Import the repository into Vercel and set the project's **Root Directory** to `frontend`.
2. Vercel uses `frontend/vercel.json` to install dependencies with `npm ci`, build with `npm run build`, and publish `dist`.
3. In Vercel Project Settings → Environment Variables, set:
   - `VITE_API_BASE_URL` to the public Render backend URL, with no trailing slash (for example, `https://your-api.onrender.com`).
   - `VITE_GOOGLE_CLIENT_ID` to the same Google OAuth Web Client ID configured on the backend.
4. In Render, set `CORS_ORIGINS` to the exact Vercel site origin (for example, `https://your-app.vercel.app`). For cross-origin cookie sessions, set `SESSION_COOKIE_SAMESITE=none` and `SESSION_COOKIE_SECURE=true`.
5. Redeploy both services after changing environment variables.

Render's `CORS_ORIGINS` and cookie settings must match the deployed frontend origin and HTTPS setup. The browser sends session cookies with credentialed requests; browsers that block third-party cookies may require serving the API through a same-site custom domain or proxy.

## Google setup

For local development, add `http://localhost:5173` to the Google OAuth Web Client's Authorized JavaScript origins. Use the same client ID in both frontend and backend environment files. The frontend receives a Google ID token and sends it to FastAPI in the `Authorization: Bearer ...` header.

## Notes

- The frontend only displays known marker terms returned by the backend; it does not claim definitive AI-image detection.
- Guest checking and cleaning do not require Google sign-in.
- Named endpoints require Google sign-in and working R2 configuration.
- For production deployment, configure HTTPS, production CORS origins, and appropriate token/session handling.
