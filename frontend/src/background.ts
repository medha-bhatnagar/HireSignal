/**
 * Why this file exists, and why the OAuth call can't just live in the popup:
 *
 * Manifest V3's toolbar popup (index.html/App.tsx) is torn down -- its JS
 * context destroyed, not just hidden -- the moment it loses focus. Calling
 * chrome.identity.launchWebAuthFlow() opens GitHub's real login page in a
 * separate window; the instant the user clicks into that window to type
 * their password, the extension popup loses focus and Chrome kills it,
 * silently aborting whatever promise was in flight. The user would see the
 * GitHub login window, log in, and then... nothing -- the popup that was
 * supposed to receive the result is already gone.
 *
 * A service worker doesn't have this problem: it keeps running independent
 * of whether any popup is open. So the OAuth flow lives here, and the popup
 * (see lib/auth.ts's signInWithGithub) just sends a message and waits. Even
 * if the popup itself gets closed mid-flow, this code keeps running,
 * finishes storing the tokens, and the next time the user opens the popup
 * it just reads the signed-in state from chrome.storage.local as normal.
 */
import { BACKEND_URL, GITHUB_CLIENT_ID } from "./lib/config";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "SIGN_IN_WITH_GITHUB") {
    signInWithGithub()
      .then(sendResponse)
      .catch((err: unknown) =>
        sendResponse({ error: err instanceof Error ? err.message : "Sign-in failed." })
      );
    return true; // keep the message channel open for the async response above
  }
});

async function signInWithGithub(): Promise<{ username: string }> {
  const redirectUri = chrome.identity.getRedirectURL();
  const authUrl =
    `https://github.com/login/oauth/authorize` +
    `?client_id=${GITHUB_CLIENT_ID}` +
    `&scope=read:user` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}`;

  const redirectUrl = await chrome.identity.launchWebAuthFlow({
    url: authUrl,
    interactive: true,
  });
  if (!redirectUrl) throw new Error("GitHub sign-in was cancelled.");

  const code = new URL(redirectUrl).searchParams.get("code");
  if (!code) throw new Error("GitHub did not return an authorization code.");

  const res = await fetch(`${BACKEND_URL}/auth/github/callback/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) throw new Error(`GitHub sign-in failed (${res.status}).`);

  const data = await res.json();
  await chrome.storage.local.set({
    access_token: data.access,
    refresh_token: data.refresh,
    github_username: data.username,
  });

  return { username: data.username };
}
