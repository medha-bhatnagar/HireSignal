interface HomeProps {
  isGitHubProfilePage: boolean;
  hasExportableResult: boolean;
  onSummary: () => void;
  onMatch: () => void;
  onExport: () => void;
  isSignedIn: boolean;
  signedInUsername?: string;
  onSignIn: () => void;
  onSignOut: () => void;
}

// This component only renders buttons and reports clicks upward via props —
// it doesn't know how to fetch data or talk to the content script itself.
// App.tsx owns that logic. Keeping this "dumb" makes it easy to test and
// easy to restyle later without touching any request logic.
export function Home({
  isGitHubProfilePage,
  hasExportableResult,
  onSummary,
  onMatch,
  onExport,
  isSignedIn,
  signedInUsername,
  onSignIn,
  onSignOut,
}: HomeProps) {
  return (
    <div>
      <div className="header centered">
        <div className="logo-mark">H</div>
        <div className="title">HireSignal</div>
        <div className="subtitle">Profile insight, on demand</div>
      </div>

      {/* Auth is optional, not a gate — anonymous users can use everything
          below at the shared/anonymous rate limit. Signing in just raises
          that limit and starts tracking a personal search history
          (see common.models.SearchHistory on the backend). */}
      <div
        className="card"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: 12,
        }}
      >
        {isSignedIn ? (
          <>
            <span style={{ color: "var(--text-muted)" }}>
              Signed in as <strong style={{ color: "var(--text)" }}>{signedInUsername}</strong>
            </span>
            <button
              onClick={onSignOut}
              style={{
                background: "none",
                border: "none",
                color: "var(--accent)",
                cursor: "pointer",
                fontSize: 12,
                padding: 0,
              }}
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <span style={{ color: "var(--text-muted)" }}>Using the anonymous tier</span>
            <button
              onClick={onSignIn}
              style={{
                background: "none",
                border: "none",
                color: "var(--accent)",
                cursor: "pointer",
                fontSize: 12,
                padding: 0,
              }}
            >
              Sign in with GitHub
            </button>
          </>
        )}
      </div>

      {!isGitHubProfilePage && (
        <div className="card" style={{ fontSize: 12, color: "var(--text-muted)" }}>
          Open a GitHub profile page to use HireSignal.
        </div>
      )}

      <button className="action" onClick={onSummary} disabled={!isGitHubProfilePage}>
        AI summary
      </button>
      <button className="action" onClick={onMatch} disabled={!isGitHubProfilePage}>
        Job match
      </button>
      {/* Disabled until a summary or match result exists in state — this
          button re-exports the most recent result without regenerating it. */}
      <button className="action primary" onClick={onExport} disabled={!hasExportableResult}>
        Export PDF
      </button>
    </div>
  );
}
