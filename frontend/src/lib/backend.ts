import type { ProfileData } from "../types";
import { API_URL } from "./config";
import { authenticatedFetch } from "./auth";

// Reads the username straight off the current tab's URL — no content
// script needed, since your backend fetches from the real GitHub API
// by username rather than scraping the rendered page.
async function getActiveTab(): Promise<chrome.tabs.Tab> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) throw new Error("No active tab found");
  return tab;
}

export async function isOnGitHubProfile(): Promise<boolean> {
  const tab = await getActiveTab();
  return /^https:\/\/github\.com\/[^/]+\/?$/.test(tab.url ?? "");
}

export async function getUsernameFromTab(): Promise<string> {
  const tab = await getActiveTab();
  const match = (tab.url ?? "").match(/^https:\/\/github\.com\/([^/]+)\/?$/);
  if (!match) throw new Error("Not on a GitHub profile page");
  return match[1];
}

// Reads the Retry-After header a 429 response sends (see
// common/ratelimit.py) and turns it into a friendly, specific message
// instead of a generic "request failed" — this is the moment to nudge an
// anonymous user toward signing in for a higher limit.
async function throwForBadResponse(res: Response, action: string): Promise<never> {
  if (res.status === 429) {
    const retryAfterSeconds = Number(res.headers.get("Retry-After") ?? "3600");
    const minutes = Math.max(1, Math.round(retryAfterSeconds / 60));
    throw new Error(
      `You've hit the hourly limit. Try again in about ${minutes} minute${
        minutes === 1 ? "" : "s"
      }, or sign in with GitHub for a higher limit.`
    );
  }
  throw new Error(`${action} failed (${res.status})`);
}

// GET /api/analyze/<username>/ — returns profile data AND the AI summary
// in one response, since your Django view generates both server-side.
export async function analyzeProfile(
  username: string
): Promise<{ profile: ProfileData; summary: string }> {
  const res = await authenticatedFetch(`${API_URL}/analyze/${encodeURIComponent(username)}/`);
  if (!res.ok) await throwForBadResponse(res, "Analyze request");
  const data = await res.json();

  const profile: ProfileData = {
    username: data.username,
    full_name: data.full_name,
    bio: data.bio,
    tech_stack: data.tech_stack ?? [],
    profile_image: data.profile_image,
    account_age: data.account_age,
  };

  return { profile, summary: data.ai_summary as string };
}

// POST /api/match/<username>/ — the view expects { "requirements": "..." }
// and returns { username, job_match }.
export async function matchJob(username: string, jobDescription: string): Promise<string> {
  const res = await authenticatedFetch(`${API_URL}/match/${encodeURIComponent(username)}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ requirements: jobDescription }),
  });
  if (!res.ok) await throwForBadResponse(res, "Match request");
  const data = await res.json();
  return data.job_match as string;
}

// The AI prompt for job matching returns a free-form paragraph, not
// structured JSON, so there's no guaranteed numeric field to read a score
// from. This is a best-effort regex looking for the first "NN%" it finds —
// it'll work as long as the model states a percentage, but it's fragile
// against phrasing changes. The generate_job_match prompt in ai/generate.py
// already has a commented-out structured-JSON version — switching to that
// and having match_job return a real "score" field would make this
// unnecessary and far more reliable.
export function parseScoreFromText(text: string): number | undefined {
  const match = text.match(/(\d{1,3})\s?%/);
  if (!match) return undefined;
  const value = Number(match[1]);
  return value >= 0 && value <= 100 ? value : undefined;
}
