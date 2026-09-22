import { jsPDF } from "jspdf";
import type { AnalysisResult } from "../types";

// This function doesn't know or care whether "result" came from the summary
// button or the job-match button — that's the whole point of storing both
// in the same shape (see types.ts). It just formats whatever text is there.
export function exportResultToPdf(result: AnalysisResult, username: string) {
  const doc = new jsPDF();
  const title = result.type === "summary" ? "GitHub profile summary" : "Job match report";

  doc.setFontSize(18);
  doc.text(title, 20, 20);

  doc.setFontSize(11);
  doc.text(`Profile: ${username}`, 20, 30);

  if (result.type === "match" && result.score !== undefined) {
    doc.setFontSize(14);
    doc.text(`Match score: ${result.score}%`, 20, 42);
  }

  doc.setFontSize(11);
  const startY = result.type === "match" ? 52 : 42;
  const wrapped = doc.splitTextToSize(result.content, 170);
  doc.text(wrapped, 20, startY);

  doc.save(`hiresignal-${result.type}-${username}.pdf`);
}
