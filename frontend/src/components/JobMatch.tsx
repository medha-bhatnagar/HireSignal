interface JobMatchProps {
  username: string;
  jobDescription: string;
  onChangeJobDescription: (value: string) => void;
  onBack: () => void;
  onAnalyze: () => void;
}

export function JobMatch({
  username,
  jobDescription,
  onChangeJobDescription,
  onBack,
  onAnalyze,
}: JobMatchProps) {
  const isEmpty = jobDescription.trim().length === 0;

  return (
    <div>
      <div className="header">
        <button className="back-button" onClick={onBack} aria-label="Back">
          ←
        </button>
        <div className="title" style={{ fontSize: 16 }}>
          Job match
        </div>
      </div>
      <div className="subtitle" style={{ marginBottom: 8 }}>
        {username}'s GitHub profile
      </div>

      <textarea
        className="job-input"
        placeholder="Paste the job description here — required skills, seniority level, tech stack..."
        value={jobDescription}
        onChange={(e) => onChangeJobDescription(e.target.value)}
      />
      {isEmpty && (
        <div style={{ fontSize: 12, color: "var(--accent)", marginTop: -8, marginBottom: 12 }}>
          Paste a job description before analyzing.
        </div>
      )}

      <button className="action primary" onClick={onAnalyze} disabled={isEmpty}>
        Analyze match
      </button>
    </div>
  );
}
