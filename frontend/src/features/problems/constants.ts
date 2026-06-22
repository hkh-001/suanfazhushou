import type { ProblemDifficulty } from "./types";

export const difficultyLabels: Record<ProblemDifficulty, string> = {
  beginner: "入门",
  basic: "基础",
  intermediate: "提高",
  advanced: "进阶"
};

export const difficultyStyles: Record<ProblemDifficulty, string> = {
  beginner: "border-emerald-200 bg-emerald-50 text-emerald-700",
  basic: "border-blue-200 bg-blue-50 text-blue-700",
  intermediate: "border-amber-200 bg-amber-50 text-amber-700",
  advanced: "border-rose-200 bg-rose-50 text-rose-700"
};
