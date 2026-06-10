import { ProblemDetailPage } from "@/features/problems/ProblemDetailPage";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ProblemDetailPage id={id} />;
}
