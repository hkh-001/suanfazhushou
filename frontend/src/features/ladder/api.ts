import { apiFetch } from "@/lib/api/client";

import type { LadderNodeDetail, LadderPracticeSubmitPayload, LadderPracticeSubmitResult, LadderSummary } from "./types";

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

export async function submitLadderNodePractice(
  nodeId: string,
  payload: LadderPracticeSubmitPayload
): Promise<LadderPracticeSubmitResult> {
  const response = await apiFetch<DataResponse<LadderPracticeSubmitResult>>(`/ladder/nodes/${nodeId}/practice-submit`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
  return response.data;
}
