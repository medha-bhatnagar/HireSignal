interface LoadingProps {
  title: string;
  message: string;
}

// Reused for both the summary and match requests — only the title and
// message text differ, passed in from App.tsx based on which action is running.
export function Loading({ title, message }: LoadingProps) {
  return (
    <div>
      <div className="header">
        <button className="back-button" disabled aria-label="Back">
          ←
        </button>
        <div className="title" style={{ fontSize: 16, color: "var(--text-dim)" }}>
          {title}
        </div>
      </div>

      <div className="card loading-box">
        <svg className="spinner" width="32" height="32" viewBox="0 0 32 32">
          <circle cx="16" cy="16" r="13" fill="none" stroke="var(--border)" strokeWidth="3" />
          <path
            d="M16 3a13 13 0 0 1 13 13"
            fill="none"
            stroke="var(--accent)"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
        <div style={{ fontSize: 13 }}>{message}</div>
      </div>
    </div>
  );
}
