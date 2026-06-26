import { Suspense } from "react";

import { LadderPage } from "@/features/ladder/LadderPage";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <LadderPage />
    </Suspense>
  );
}
