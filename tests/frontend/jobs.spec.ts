import { expect, test, vi } from "vitest";
import type { Client, Job } from "@qa/client";
import { watchJob } from "../../WebUI/src/components/jobs.js";

const finishedJob: Job = {
  job_id: "job_done",
  kind: "import",
  state: "succeeded",
  progress: 1,
  revision: 2,
  created_at: "2026-11-06T00:00:00Z",
  result_version_id: "ver_ready",
};

test("terminal job remains visible when event replay is unavailable", async () => {
  const getJob = vi.fn(async () => finishedJob);
  const jobEvents = vi.fn(async () => {
    throw new Error("event replay temporarily unavailable");
  });
  const onTerminal = vi.fn();
  const card = watchJob({ getJob, jobEvents } as unknown as Client, "job_done", {
    title: "导入任务",
    signal: new AbortController().signal,
    pollMs: 1,
    onTerminal,
  });
  document.body.append(card.element);
  expect(await card.finished).toEqual(finishedJob);
  expect(card.element.dataset.state).toBe("succeeded");
  expect(card.element.textContent).toContain("ver_ready");
  expect(card.element.textContent).toContain("event replay temporarily unavailable");
  expect(onTerminal).toHaveBeenCalledOnce();
  expect(getJob).toHaveBeenCalledTimes(1);
  expect(jobEvents).toHaveBeenCalledTimes(1);
  card.element.remove();
});
