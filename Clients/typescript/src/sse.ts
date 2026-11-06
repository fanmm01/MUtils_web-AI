/**
 * SSE transport for answer and job streams.
 *
 * Uses ``fetch`` + ``ReadableStream`` so the Authorization header can be sent
 * (EventSource cannot set headers). TCP chunks are not event boundaries; UTF-8
 * sequences and ``data:`` lines may split, so decode incrementally.
 */

import type { Client } from "./client.js";
import type { AnswerEvent, AnswerEventV2, JobEvent, JobEventV2 } from "./generated/events.js";

export type SSEEvent = AnswerEvent | AnswerEventV2 | JobEvent | JobEventV2;

export interface SSECallbacks {
  onEvent: (event: SSEEvent) => void;
  signal?: AbortSignal;
  /** Resume cursor; maps to ``Last-Event-ID``. */
  after?: number;
  onError?: (error: Error) => void;
  /** Reconnect with exponential backoff; the caller can disable this. */
  reconnect?: boolean;
}

const DEFAULT_RETRY_MS = 1_000;
const MAX_RETRY_MS = 30_000;

export async function subscribeAnswer(
  client: Client,
  answerId: string,
  callbacks: SSECallbacks,
): Promise<void> {
  return subscribe(client, `/v1/answers/${encodeURIComponent(answerId)}/events`, callbacks);
}

export async function subscribeJob(
  client: Client,
  jobId: string,
  callbacks: SSECallbacks,
): Promise<void> {
  return subscribe(client, `/v1/jobs/${encodeURIComponent(jobId)}/events`, callbacks);
}

async function subscribe(client: Client, path: string, callbacks: SSECallbacks): Promise<void> {
  let after = callbacks.after;
  let attempt = 0;
  const reconnect = callbacks.reconnect ?? true;
  for (;;) {
    if (callbacks.signal?.aborted) return;
    try {
      const headers = after !== undefined ? { "Last-Event-ID": String(after) } : undefined;
      const response = await client.stream(path, { signal: callbacks.signal, headers });
      let terminal = false;
      for await (const event of parseSSE(response.body)) {
        if (typeof event.id === "number") {
          if (after !== undefined && event.id <= after) continue;
          after = event.id;
        }
        callbacks.onEvent(event);
        if (isTerminal(event)) {
          terminal = true;
          break;
        }
      }
      if (terminal) return;
      attempt = 0;
    } catch (error) {
      if (callbacks.signal?.aborted) return;
      callbacks.onError?.(error instanceof Error ? error : new Error(String(error)));
      if (!reconnect) return;
    }
    if (!reconnect || callbacks.signal?.aborted) return;
    attempt += 1;
    await delay(Math.min(DEFAULT_RETRY_MS * 2 ** attempt, MAX_RETRY_MS), callbacks.signal);
  }
}

export async function* parseSSE(
  body: ReadableStream<Uint8Array> | null,
): AsyncGenerator<SSEEvent & { id?: number }> {
  if (!body) return;
  const reader = body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let dataLines: string[] = [];
  let eventId: number | undefined;

  const flush = (): (SSEEvent & { id?: number }) | undefined => {
    if (dataLines.length === 0) return undefined;
    const raw = dataLines.join("\n");
    dataLines = [];
    if (raw === "") return undefined;
    let payload: unknown;
    try {
      payload = JSON.parse(raw);
    } catch {
      return undefined;
    }
    return { ...(payload as SSEEvent), id: eventId } as SSEEvent & { id?: number };
  };

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let newline = buffer.indexOf("\n");
      while (newline >= 0) {
        let rawLine = buffer.slice(0, newline);
        buffer = buffer.slice(newline + 1);
        if (rawLine.endsWith("\r")) rawLine = rawLine.slice(0, -1);
        if (rawLine === "") {
          const event = flush();
          if (event) yield event;
        } else if (!rawLine.startsWith(":")) {
          const colon = rawLine.indexOf(":");
          const field = colon === -1 ? rawLine : rawLine.slice(0, colon);
          let valueText = colon === -1 ? "" : rawLine.slice(colon + 1);
          if (valueText.startsWith(" ")) valueText = valueText.slice(1);
          if (field === "data") dataLines.push(valueText);
          else if (field === "id") {
            const parsed = Number(valueText);
            eventId = Number.isFinite(parsed) ? parsed : undefined;
          }
        }
        newline = buffer.indexOf("\n");
      }
    }
    buffer += decoder.decode();
    if (buffer.trim() !== "") {
      const colon = buffer.indexOf(":");
      if (colon !== -1 && buffer.slice(0, colon) === "data") {
        const valueText = buffer.slice(colon + 1).replace(/^ /, "");
        dataLines.push(valueText);
      }
    }
    const event = flush();
    if (event) yield event;
  } finally {
    reader.releaseLock();
  }
}

function isTerminal(event: SSEEvent): boolean {
  if ("answer_id" in event) {
    return (
      event.event === "answer.completed" ||
      event.event === "answer.refused" ||
      event.event === "answer.failed" ||
      event.event === "answer.cancelled"
    );
  }
  return (
    event.event === "job.completed" ||
    event.event === "job.failed" ||
    event.event === "job.cancelled"
  );
}

function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        resolve();
      },
      { once: true },
    );
  });
}
