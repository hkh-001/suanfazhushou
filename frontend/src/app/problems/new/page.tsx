import { ProblemFormPage } from "@/features/problems/ProblemFormPage";

export default async function Page({
  searchParams
}: {
  searchParams: Promise<{ visibility?: string }>;
}) {
  const { visibility } = await searchParams;
  return <ProblemFormPage initialVisibility={visibility === "public" ? "public" : "private"} />;
}
