// The shape returned by GET /api/analyze/<username>/ — matches
// build_profile_data() plus the generated ai_summary in developers/views.py.
export interface ProfileData {
  username: string;
  full_name: string;
  bio: string;
  tech_stack: string[];
  profile_image: string;
  account_age: string;
}

// The two things this extension can produce, stored in one place so the
// PDF button can export either without caring which one it is.
export interface AnalysisResult {
  type: "summary" | "match";
  content: string;
  score?: number; // best-effort, parsed from the AI's prose — see backend.ts
}

// The single source of truth for what the popup is currently doing.
// Using one status instead of separate booleans (isLoading, hasError, hasResult)
// makes invalid combinations (loading AND error at once) impossible to represent.
export type Status = "idle" | "loading" | "error" | "success";

export type View = "home" | "match" | "summary";
