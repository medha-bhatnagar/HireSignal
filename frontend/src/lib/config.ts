// Point this at wherever your Django server runs. During development
// that's the manage.py runserver default; change it once you deploy.
// Shared by lib/backend.ts, lib/auth.ts, and background.ts so it only
// needs to change in one place.
export const BACKEND_URL = "http://127.0.0.1:8000";
export const API_URL = `${BACKEND_URL}/api`;

// The GitHub OAuth App's client id -- public, safe to ship inside the
// extension bundle (unlike the client secret, which lives only in the
// Django backend's environment variables and is never sent to, or stored
// in, the extension). Get this from your OAuth App's settings page after
// registering it at github.com/settings/developers.
export const GITHUB_CLIENT_ID = "Ov23liHUrQwXOYZJoZ6r";
