import { TopicDetailPage } from "@/features/topics/TopicDetailPage";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TopicDetailPage id={id} />;
}
