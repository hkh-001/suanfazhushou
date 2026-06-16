import { MistakeDetailPage } from "@/features/mistakes/MistakeDetailPage";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MistakeDetailPage id={id} />;
}
