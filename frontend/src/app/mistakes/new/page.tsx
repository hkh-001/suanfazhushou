import { Suspense } from "react";

import { MistakeCreatePage } from "@/features/mistakes/MistakeFormPage";

export default function Page() {
  return (
    <Suspense fallback={<div className="p-6 text-sm text-[#64748b]">正在加载复盘表单...</div>}>
      <MistakeCreatePage />
    </Suspense>
  );
}
