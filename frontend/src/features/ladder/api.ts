import { apiFetch } from "@/lib/api/client";

import type { LadderNodeDetail, LadderSummary } from "./types";

type DataResponse<T> = {
  data: T;
};

export async function fetchLadder(): Promise<LadderSummary> {
  const response = await apiFetch<DataResponse<LadderSummary>>("/ladder");
  return response.data;
}

export async function fetchLadderNode(nodeId: string): Promise<LadderNodeDetail> {
  const response = await apiFetch<DataResponse<LadderNodeDetail>>(`/ladder/nodes/${nodeId}`);
  return response.data;
}

export async function completeLadderNodeMaterial(nodeId: string): Promise<LadderSummary> {
  const response = await apiFetch<DataResponse<LadderSummary>>(`/ladder/nodes/${nodeId}/material-complete`, {
    method: "POST"
  });
  return response.data;
}
