import type { AnalysisResult } from "../types";

interface ResultViewProps {
  result: AnalysisResult;
  username: string;
  techStack?: string[];
  onBack: () => void;
  onExport: () => void;
}

// Same component handles both result types — it reads result.type to decide
// the title and whether to show a score, but the export button underneath
// doesn't change at all. This is the payoff of storing both results in one shape.
export function ResultView({ result, username, techStack, onBack, onExport }: ResultViewProps) {
  const title = result.type === "summary" ? "AI summary" : "Job match";

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
      <div className="subtitle" style={{ marginBottom: 14 }}>
        {username}'s GitHub profile
      </div>

      <div className="card accent-border">
        {result.type === "match" && result.score !== undefined && (
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 8,
            }}
          >
            <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Match score</span>
            <span style={{ fontSize: 20, fontWeight: 700, color: "var(--accent)" }}>
              {result.score}%
            </span>
          </div>
        )}
        <div style={{ fontSize: 12, lineHeight: 1.7, color: "var(--text)" }}>
          {result.content}
        </div>
      </div>

      {result.type === "summary" && techStack && techStack.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 14 }}>
          {techStack.slice(0, 6).map((tech) => (
            <span
              key={tech}
              style={{
                fontSize: 11,
                padding: "4px 10px",
                borderRadius: 999,
                background: "var(--surface)",
                border: "1px solid var(--border)",
                color: "var(--text-muted)",
              }}
            >
              {tech}
            </span>
          ))}
        </div>
      )}

      <button className="action primary" onClick={onExport}>
        Export PDF
      </button>
    </div>
  );
}
