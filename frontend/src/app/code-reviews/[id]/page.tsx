import { CodeReviewDetailPage } from "@/features/code-reviews/CodeReviewDetailPage";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <CodeReviewDetailPage id={id} />;
}
