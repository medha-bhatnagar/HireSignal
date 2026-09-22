import { useEffect, useState } from "react";
import type { AnalysisResult, ProfileData, Status, View } from "./types";
import { isOnGitHubProfile, getUsernameFromTab, analyzeProfile, matchJob, parseScoreFromText } from "./lib/backend";
import { getAuthState, signInWithGithub, signOut, type AuthState } from "./lib/auth";
import { exportResultToPdf } from "./lib/pdf";
import { Home } from "./components/Home";
import { JobMatch } from "./components/JobMatch";
import { ResultView } from "./components/ResultView";
import { Loading } from "./components/Loading";
import { ErrorState } from "./components/ErrorState";

export default function App() {
  // Navigation
  const [view, setView] = useState<View>("home");

  // Request lifecycle — one status instead of three separate booleans
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Data
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [jobDescription, setJobDescription] = useState("");

  // Environment — checked once when the popup opens
  const [isGitHubProfilePage, setIsGitHubProfilePage] = useState(false);
  const [username, setUsername] = useState<string | null>(null);

  // Auth — optional, not a gate (see Home.tsx). Loaded from chrome.storage
  // on every popup open since the background service worker may have
  // signed the user in (or a token may have been silently refreshed)
  // since the popup was last shown.
  const [auth, setAuth] = useState<AuthState>({ signedIn: false });
  const [signInError, setSignInError] = useState<string | null>(null);

  useEffect(() => {
    isOnGitHubProfile().then((onProfile) => {
      setIsGitHubProfilePage(onProfile);
      if (onProfile) getUsernameFromTab().then(setUsername).catch(() => {});
    });
    getAuthState().then(setAuth);
  }, []);

  async function handleSignIn() {
    setSignInError(null);
    try {
      const newAuth = await signInWithGithub();
      setAuth(newAuth);
    } catch (err) {
      setSignInError(err instanceof Error ? err.message : "Sign-in failed.");
    }
  }

  async function handleSignOut() {
    await signOut();
    setAuth({ signedIn: false });
  }

  async function handleSummary() {
    setView("summary");
    setStatus("loading");
    try {
      if (!username) throw new Error("Couldn't read the username from this tab.");
      const { profile: data, summary } = await analyzeProfile(username);
      setProfile(data);
      setResult({ type: "summary", content: summary });
      setStatus("success");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Something went wrong.");
      setStatus("error");
    }
  }

  async function handleAnalyzeMatch() {
    setStatus("loading");
    try {
      if (!username) throw new Error("Couldn't read the username from this tab.");
      const content = await matchJob(username, jobDescription);
      setResult({ type: "match", content, score: parseScoreFromText(content) });
      setStatus("success");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Something went wrong.");
      setStatus("error");
    }
  }

  function handleExport() {
    if (result && username) exportResultToPdf(result, username);
  }

  function goHome() {
    setView("home");
    setStatus("idle");
  }

  // --- Render logic: each branch below corresponds to a mockup screen ---

  if (status === "loading") {
    return (
      <div className="popup">
        <Loading
          title={view === "summary" ? "AI summary" : "Job match"}
          message={
            view === "summary"
              ? "Reading profile and generating summary"
              : "Comparing profile to job description"
          }
        />
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="popup">
        <ErrorState
          title={view === "summary" ? "AI summary" : "Job match"}
          message={errorMessage ?? "Please try again."}
          onBack={goHome}
          onRetry={view === "summary" ? handleSummary : handleAnalyzeMatch}
        />
      </div>
    );
  }

  if (status === "success" && result) {
    return (
      <div className="popup">
        <ResultView
          result={result}
          username={username ?? ""}
          techStack={profile?.tech_stack}
          onBack={goHome}
          onExport={handleExport}
        />
      </div>
    );
  }

  if (view === "match") {
    return (
      <div className="popup">
        <JobMatch
          username={username ?? "this"}
          jobDescription={jobDescription}
          onChangeJobDescription={setJobDescription}
          onBack={goHome}
          onAnalyze={handleAnalyzeMatch}
        />
      </div>
    );
  }

  return (
    <div className="popup">
      <Home
        isGitHubProfilePage={isGitHubProfilePage}
        hasExportableResult={result !== null}
        onSummary={handleSummary}
        onMatch={() => setView("match")}
        onExport={handleExport}
        isSignedIn={auth.signedIn}
        signedInUsername={auth.username}
        onSignIn={handleSignIn}
        onSignOut={handleSignOut}
      />
      {signInError && (
        <div style={{ fontSize: 11, color: "var(--accent)", marginTop: 8, textAlign: "center" }}>
          {signInError}
        </div>
      )}
    </div>
  );
}
