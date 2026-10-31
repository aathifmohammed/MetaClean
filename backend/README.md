# MetaClean Backend

MetaClean is a FastAPI backend for checking and cleaning image metadata. This repository scaffold includes Google ID-token authentication, MongoDB Atlas, recent activity retention, user-owned API endpoints, and Cloudflare R2-compatible object storage for cleaned images.

## Setup

1. Use Python 3.11 or a Python version supported by all dependencies.
2. Create and activate a virtual environment.
3. Install dependencies: `python -m pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and set the private MongoDB URI.
5. To enable sign-in, configure a Google OAuth web client ID and set `GOOGLE_CLIENT_ID`. The frontend must send a Google ID token in `Authorization: Bearer <credential>`; do not send a client secret to the frontend.
6. To enable saving endpoint images, configure the R2 variables and create the bucket in Cloudflare.
7. Start the server: `python -m uvicorn app.main:app --reload`.
8. Open `/docs`.

## API overview

- `POST /api/metadata/check` — check readable EXIF and known AI marker terms. Guests can use it. Signed-in requests create an activity record.
- `POST /api/metadata/clean` — multipart fields `file` and `mode` (`ai_only` or `all`). Guests can use it.
- `GET /api/account/me` — current signed-in user.
- `GET /api/account/activities` — up to 10 most recent activities.
- `POST /api/endpoints` — create a named endpoint.
- `GET /api/endpoints` — list your endpoints.
- `PATCH /api/endpoints/{endpoint_id}` — rename your endpoint.
- `DELETE /api/endpoints/{endpoint_id}` — delete your endpoint and its stored images.
- `POST /api/endpoints/{endpoint_id}/images` — clean and save an image to the endpoint; the oldest is removed after the endpoint exceeds 10 images.
- `DELETE /api/endpoints/{endpoint_id}/images/{image_id}` — delete one stored image.
- `GET /api/public/{endpoint_id}` — public read-only endpoint data.
- `GET /api/public/{endpoint_id}/images/{image_id}` — public image retrieval.

## Google authentication

The frontend should use Google Identity Services to obtain an ID token and send it as a Bearer token. The backend verifies the token with Google's library and checks the configured audience. A Google OAuth client ID must be configured before protected routes work. Never trust a user ID, email, or role sent directly by the browser.

## Storage

MongoDB stores user profiles, activity records, endpoint configuration, and image metadata/object keys. Image bytes are stored in R2, not in MongoDB. R2 variables are required for endpoint image upload/download. The backend still allows guest check/clean operations when R2 is not configured.

## AI-only cleaning limitations (v1)

AI-only cleaning inspects readable top-level EXIF field values for a limited list of known terms. If a match is found, the entire matching field is removed. Other top-level EXIF fields are preserved where supported by Pillow and the image format. This is heuristic matching, not definitive AI-image detection. Selective XMP, IPTC, C2PA, nested EXIF, and proprietary metadata cleaning are not implemented. Absence of a marker does not prove an image is non-AI.

The all-metadata mode re-encodes images without deliberately copying metadata, but should not be described as a forensic guarantee that every possible metadata block has been removed. Re-encoding may change file size or image encoding.

## Security notes before production

- Use HTTPS and restrict CORS to your deployed frontend origin.
- Add rate limiting and request-size limits at the reverse proxy as well as in the application.
- Configure R2 credentials with least privilege and never commit `.env`.
- Use a scheduled cleanup policy for orphaned R2 objects if storage/database operations fail partway through.
- Review concurrency for FIFO limits if many simultaneous uploads to one endpoint are expected.
- Run tests and perform manual integration tests with real JPEG, PNG, and WebP files before deployment.
