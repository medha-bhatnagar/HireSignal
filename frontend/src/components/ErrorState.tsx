interface ErrorStateProps {
  title: string;
  message: string;
  onBack: () => void;
  onRetry: () => void;
}

export function ErrorState({ title, message, onBack, onRetry }: ErrorStateProps) {
  return (
    <div>
      <div className="header">
        <button className="back-button" onClick={onBack} aria-label="Back">
          ←
        </button>
        <div className="title" style={{ fontSize: 16 }}>
          {title}
        </div>
      </div>

      <div className="card accent-border" style={{ textAlign: "center", padding: "28px 16px" }}>
        <div style={{ fontSize: 13, marginBottom: 6 }}>Couldn't complete the request</div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.5 }}>{message}</div>
      </div>

      <button className="action" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}
