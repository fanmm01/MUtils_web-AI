/**
 * Shared job card: state, progress, per-file diagnostics, the persisted event
 * log and cancel/retry. It polls `GET /v1/jobs/{id}` plus the JSON event
 * replay (`GET /v1/jobs/{id}/events`, SSE in P3) until a terminal state. Only
 * the server's job record decides the state; nothing here assumes progress.
 */

import type { Client, Job, JobState } from "@qa/client";
import { dataTable, facts, formatTime, idText, row } from "./data.js";
import { button, createStatusArea, describeError, h, isConflict, toolbar } from "./ui.js";

const STATE_LABEL: Record<JobState, string> = {
  queued: "排队中",
  running: "处理中",
  cancel_requested: "正在取消",
  succeeded: "已完成",
  failed: "失败",
  cancelled: "已取消",
  outcome_unknown: "结果未知",
};
const TERMINAL: ReadonlySet<JobState> = new Set(["succeeded", "failed", "cancelled", "outcome_unknown"]);
const EVENT_LABEL: Record<string, string> = {
  "job.accepted": "已受理",
  "job.progress": "进度",
  "job.completed": "完成",
  "job.failed": "失败",
  "job.cancelled": "已取消",
};
const DIAGNOSTIC_LABEL: Record<string, string> = { ok: "已处理", skipped: "已跳过", failed: "失败" };

export function jobState(job: Job): JobState {
  return job.state ?? "queued";
}

export function isTerminal(job: Job): boolean {
  return TERMINAL.has(jobState(job));
}

export interface JobCardOptions {
  title: string;
  signal: AbortSignal;
  pollMs: number;
  /** Shown for a failed or cancelled job; e.g. regenerate the import preview. */
  retry?: { label: string; run: () => void };
  /** Called once with the terminal job. */
  onTerminal?: (job: Job) => void;
}

export interface JobCard {
  element: HTMLElement;
  /** Resolves with the terminal job, or null if the page was left first. */
  finished: Promise<Job | null>;
}

interface LogEntry {
  seq: number;
  label: string;
  time: string;
  text: string;
}

/** Render one job and keep it current until it reaches a terminal state. */
export function watchJob(client: Client, jobId: string, options: JobCardOptions): JobCard {
  const summary = h("div", { class: "job-summary" });
  const hint = h("p", { class: "note" });
  const diagnostics = dataTable("逐文件结果", ["文件", "结果", "说明"]);
  const diagnosticsBox = h("details", { class: "job-diagnostics" }, h("summary", {}, "逐文件结果"), diagnostics.element);
  const log = h("ol", { class: "job-log" });
  const logBox = h("details", { class: "job-events" }, h("summary", {}, "任务事件"), log);
  const actions = toolbar();
  const status = createStatusArea();
  const element = h(
    "article",
    { class: "job", "aria-label": `${options.title} ${jobId}` },
    h("h3", {}, options.title),
    summary,
    hint,
    diagnosticsBox,
    logBox,
    actions,
    status.element,
  );
  element.dataset.jobId = jobId;
  diagnostics.setMessage("暂无逐文件结果。");

  const entries: LogEntry[] = [];
  let after = 0;

  const render = (job: Job): void => {
    const state = jobState(job);
    element.dataset.state = state;
    const progress =
      state === "running" || state === "succeeded" ? `${Math.round((job.progress ?? 0) * 100)}%` : "—";
    summary.replaceChildren(
      facts([
        ["任务 ID", idText(job.job_id)],
        ["状态", h("span", { class: `job-state job-state-${state}` }, STATE_LABEL[state])],
        ["进度", progress],
        ["创建时间", formatTime(job.created_at)],
        ["错误码", job.error_code ? h("code", {}, job.error_code) : "—"],
        ["结果版本", job.result_version_id ? idText(job.result_version_id) : "—"],
      ]),
    );
    hint.textContent =
      state === "queued"
        ? "任务已排队。导入由服务端后台进程 qa-worker 执行；它未运行时任务会一直停留在排队中。"
        : state === "outcome_unknown"
          ? "服务端无法确认任务结果，需要服务端对账后才能确定。"
          : "";
    const files = job.diagnostics ?? [];
    diagnostics.setRows(
      files.map((item) =>
        row([h("code", {}, item.relative_path), DIAGNOSTIC_LABEL[item.status] ?? item.status, item.message ?? ""], {
          "data-status": item.status,
        }),
      ),
      // The server lists failed and skipped files only.
      isTerminal(job) ? "服务端没有报告失败或跳过的文件。" : "暂无逐文件结果。",
    );
    if (files.some((item) => item.status === "failed")) diagnosticsBox.open = true;
    renderActions(job);
  };

  const renderLog = (): void => {
    log.replaceChildren(
      ...entries.map((entry) =>
        h("li", {}, `#${entry.seq} ${entry.label}`, entry.time && ` · ${entry.time}`, entry.text && ` · ${entry.text}`),
      ),
    );
    if (entries.some((entry) => entry.label === EVENT_LABEL["job.failed"])) logBox.open = true;
  };

  const renderActions = (job: Job): void => {
    actions.replaceChildren();
    const state = jobState(job);
    if (!isTerminal(job) && state !== "cancel_requested") {
      actions.append(button("取消任务", () => void cancel()));
    }
    if ((state === "failed" || state === "cancelled") && options.retry) {
      const { label, run } = options.retry;
      actions.append(button(label, run));
    }
  };

  const cancel = async (): Promise<void> => {
    status.pending("取消任务：请求中…");
    try {
      render(await client.cancelJob(jobId, { signal: options.signal }));
      status.done("已请求取消；以服务端返回的任务状态为准。");
    } catch (error) {
      if (!isConflict(error)) {
        status.fail("取消任务", describeError(error));
        return;
      }
      try {
        render(await client.getJob(jobId, { signal: options.signal }));
      } catch {
        // The next poll shows the final state.
      }
      status.done("任务已经结束，无法取消。");
    }
  };

  const fetchOnce = async (): Promise<Job> => {
    const job = await client.getJob(jobId, { signal: options.signal });
    const raw = await client.jobEvents(jobId, after, { signal: options.signal });
    for (const entry of raw.map(parseEvent)) {
      if (!entry || entry.seq <= after) continue;
      entries.push(entry);
      after = entry.seq;
    }
    renderLog();
    render(job);
    return job;
  };

  const finished = (async (): Promise<Job | null> => {
    for (;;) {
      if (options.signal.aborted) return null;
      try {
        const job = await fetchOnce();
        status.clear();
        if (isTerminal(job)) {
          options.onTerminal?.(job);
          return job;
        }
        await sleep(options.pollMs, options.signal);
      } catch (error) {
        if (options.signal.aborted) return null;
        status.fail("获取任务状态", describeError(error));
        if (!(await waitForRetry(status, options.signal))) return null;
      }
    }
  })();

  return { element, finished };
}

/** Show a retry button under a polling failure; resolves false if the page is left. */
function waitForRetry(status: ReturnType<typeof createStatusArea>, signal: AbortSignal): Promise<boolean> {
  return new Promise((resolve) => {
    const retry = button("重新获取状态", () => resolve(true));
    status.element.append(toolbar(retry));
    signal.addEventListener("abort", () => resolve(false), { once: true });
  });
}

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, ms);
    signal.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        resolve();
      },
      { once: true },
    );
  });
}

/** The replay envelope is typed loosely by the contract (`object[]`); keep valid entries. */
function parseEvent(raw: Record<string, unknown>): LogEntry | null {
  const seq = raw.id;
  if (typeof seq !== "number") return null;
  const name = typeof raw.event === "string" ? raw.event : "";
  const data = raw.data && typeof raw.data === "object" ? (raw.data as Record<string, unknown>) : {};
  const parts: string[] = [];
  if (typeof data.progress === "number") parts.push(`${Math.round(data.progress * 100)}%`);
  if (typeof data.phase === "string" && data.phase) parts.push(data.phase);
  if (typeof data.diagnostic === "string" && data.diagnostic) parts.push(data.diagnostic);
  return {
    seq,
    label: EVENT_LABEL[name] ?? name,
    time: typeof data.timestamp === "string" ? formatTime(data.timestamp) : "",
    text: parts.join(" · "),
  };
}
