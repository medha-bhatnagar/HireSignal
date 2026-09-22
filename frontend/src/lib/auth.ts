import { BACKEND_URL } from "./config";

const STORAGE_KEYS = {
  ACCESS: "access_token",
  REFRESH: "refresh_token",
  USERNAME: "github_username",
  DEVICE_ID: "device_id",
} as const;

export interface AuthState {
  signedIn: boolean;
  username?: string;
}

// A random id generated once per install, used to key the ANONYMOUS rate
// limit tier on the backend (see common/ratelimit.py's X-Device-Id check).
// Without this, anonymous requests fall back to IP-based tracking, which
// works but is a much blunter signal (e.g. everyone on the same shared
// wifi/NAT would count as one caller).
export async function getDeviceId(): Promise<string> {
  const stored = await chrome.storage.local.get(STORAGE_KEYS.DEVICE_ID);
  const existing = stored[STORAGE_KEYS.DEVICE_ID] as string | undefined;
  if (existing) return existing;
  const id = crypto.randomUUID();
  await chrome.storage.local.set({ [STORAGE_KEYS.DEVICE_ID]: id });
  return id;
}

export async function getAuthState(): Promise<AuthState> {
  const stored = await chrome.storage.local.get([STORAGE_KEYS.ACCESS, STORAGE_KEYS.USERNAME]);
  return {
    signedIn: Boolean(stored[STORAGE_KEYS.ACCESS]),
    username: stored[STORAGE_KEYS.USERNAME] as string | undefined,
  };
}

export async function signOut(): Promise<void> {
  await chrome.storage.local.remove([
    STORAGE_KEYS.ACCESS,
    STORAGE_KEYS.REFRESH,
    STORAGE_KEYS.USERNAME,
  ]);
}

// Kicks off the GitHub OAuth popup. The actual chrome.identity.launchWebAuthFlow
// call lives in background.ts (a service worker), NOT here -- see the note
// at the top of background.ts for why calling it directly from this popup
// script would silently break. This just sends a message and waits for the
// service worker's response, storing nothing itself.
export function signInWithGithub(): Promise<AuthState> {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ type: "SIGN_IN_WITH_GITHUB" }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      if (response?.error) {
        reject(new Error(response.error));
        return;
      }
      resolve({ signedIn: true, username: response.username });
    });
  });
}

async function refreshAccessToken(): Promise<string | null> {
  const stored = await chrome.storage.local.get(STORAGE_KEYS.REFRESH);
  const refresh = stored[STORAGE_KEYS.REFRESH];
  if (!refresh) return null;

  const res = await fetch(`${BACKEND_URL}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) {
    // The refresh token itself is invalid or expired -- sign out fully so
    // the UI falls back to the anonymous tier instead of retrying forever
    // on every subsequent request.
    await signOut();
    return null;
  }

  const data = await res.json();
  await chrome.storage.local.set({ [STORAGE_KEYS.ACCESS]: data.access });
  return data.access as string;
}

/**
 * Attaches whichever credential is available: a JWT if signed in,
 * otherwise the anonymous device id. On a 401 (expired access token),
 * refreshes once and retries -- the user should never notice their token
 * expired mid-session. If the refresh itself fails, retries one more time
 * as anonymous rather than surfacing a confusing auth error for what the
 * user experiences as "just looking up a profile".
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const stored = await chrome.storage.local.get(STORAGE_KEYS.ACCESS);
  const headers = new Headers(options.headers);

  if (stored[STORAGE_KEYS.ACCESS]) {
    headers.set("Authorization", `Bearer ${stored[STORAGE_KEYS.ACCESS]}`);
  } else {
    headers.set("X-Device-Id", await getDeviceId());
  }

  let res = await fetch(url, { ...options, headers });

  if (res.status === 401 && stored[STORAGE_KEYS.ACCESS]) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      headers.set("Authorization", `Bearer ${newAccess}`);
    } else {
      headers.delete("Authorization");
      headers.set("X-Device-Id", await getDeviceId());
    }
    res = await fetch(url, { ...options, headers });
  }

  return res;
}

export { STORAGE_KEYS };
