/**
 * Shared admin-page building blocks: safe DOM helpers, the not-implemented
 * banner and a status area that renders SDK errors as the server sent them.
 */

import { QAError } from "@qa/client";

export type Child = Node | string | null | undefined | false;
export type Attrs = Record<string, string | boolean | undefined>;

/** Build an element; text is always inserted as text nodes, never parsed as HTML. */
export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Attrs = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  for (const [name, value] of Object.entries(attrs)) {
    if (value === undefined || value === false) continue;
    element.setAttribute(name, value === true ? "" : value);
  }
  element.append(...present(children));
  return element;
}

function present(children: Child[]): Array<Node | string> {
  return children.filter((child): child is Node | string => Boolean(child));
}

export function pageHeader(title: string, notice: string): HTMLElement {
  return h(
    "header",
    { class: "page-header" },
    h("h1", { tabindex: "-1" }, title),
    h("p", { class: "banner", role: "note" }, h("strong", {}, "尚未实现："), notice),
  );
}

/** Header of a page whose operations are implemented: no not-implemented banner. */
export function pageIntro(title: string, intro: string): HTMLElement {
  return h(
    "header",
    { class: "page-header" },
    h("h1", { tabindex: "-1" }, title),
    h("p", { class: "intro" }, intro),
  );
}

export function section(title: string, ...children: Child[]): HTMLElement {
  return h("section", { class: "section" }, h("h2", {}, title), ...children);
}

export function note(text: string): HTMLElement {
  return h("p", { class: "note" }, text);
}

export function field(label: string, control: HTMLElement): HTMLElement {
  return h("label", { class: "field" }, h("span", {}, label), control);
}

export function button(label: string, onClick: () => void): HTMLButtonElement {
  const element = h("button", { type: "button" }, label);
  element.addEventListener("click", onClick);
  return element;
}

export function toolbar(...children: Child[]): HTMLElement {
  return h("div", { class: "toolbar" }, ...children);
}

/** Split free text into trimmed, non-empty items. */
export function splitList(text: string, separator: string | RegExp): string[] {
  return text
    .split(separator)
    .map((item) => item.trim())
    .filter(Boolean);
}

export interface ErrorView {
  title: string;
  message: string;
  code?: string;
  requestId?: string;
  status?: number;
  /** Field-level reasons from the error envelope, e.g. "kb_id：must match the URL". */
  details: string[];
  notImplemented: boolean;
}

const TITLE_BY_STATUS: Record<number, string> = {
  400: "请求无效",
  401: "未认证",
  403: "无权限",
  404: "资源不存在",
  409: "状态冲突",
  410: "资源已清理",
  422: "参数错误",
  429: "请求过于频繁",
  500: "服务内部错误",
  503: "依赖服务不可用",
};

/** Map an SDK error to display text without hiding the server's code or request id. */
export function describeError(error: unknown): ErrorView {
  if (error instanceof QAError) {
    const notImplemented = error.code === "FEATURE_NOT_IMPLEMENTED";
    const view: ErrorView = {
      title: notImplemented ? "尚未实现" : (TITLE_BY_STATUS[error.status] ?? "请求失败"),
      message: notImplemented ? `服务端尚未实现该功能（${error.message}）。` : error.message,
      code: error.code,
      status: error.status,
      details: error.details.map((item) => (item.field ? `${item.field}：${item.reason}` : item.reason)),
      notImplemented,
    };
    if (error.requestId) view.requestId = error.requestId;
    return view;
  }
  if (isAbort(error)) {
    return { title: "请求已中止", message: "请求超时或已被取消。", details: [], notImplemented: false };
  }
  if (error instanceof TypeError) {
    return { title: "无法连接问答服务", message: error.message, details: [], notImplemented: false };
  }
  const message = error instanceof Error ? error.message : String(error);
  return { title: "请求失败", message, details: [], notImplemented: false };
}

/** An aborted request (page left or timeout); also matches cross-realm DOMExceptions. */
export function isAbort(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    (error as { name?: unknown }).name === "AbortError"
  );
}

export function isConflict(error: unknown): boolean {
  return error instanceof QAError && error.status === 409;
}

export function isNotFound(error: unknown): boolean {
  return error instanceof QAError && error.status === 404;
}

export interface StatusArea {
  element: HTMLElement;
  pending(text: string): void;
  /** Neutral information (what happened, what is still pending). */
  done(text: string, ...extra: Child[]): void;
  /** A server-confirmed change such as 已创建/已发布. */
  ok(text: string, ...extra: Child[]): void;
  fail(label: string, error: ErrorView, ...extra: Child[]): void;
  clear(): void;
}

export function createStatusArea(): StatusArea {
  const element = h("div", { class: "status", role: "status", "aria-live": "polite" });
  const set = (kind: string, ...children: Child[]): void => {
    element.dataset.kind = kind;
    element.replaceChildren(...present(children));
  };
  const withExtra = (text: string, extra: Child[]): Child[] =>
    extra.length === 0 ? [text] : [h("p", {}, text), ...extra];
  return {
    element,
    pending: (text) => set("pending", text),
    done: (text, ...extra) => set("info", ...withExtra(text, extra)),
    ok: (text, ...extra) => set("ok", ...withExtra(text, extra)),
    fail: (label, error, ...extra) => {
      const meta = [error.code, error.requestId && `request_id: ${error.requestId}`]
        .filter(Boolean)
        .join(" · ");
      set(
        "error",
        h("p", { class: "status-title" }, `${label}：${error.title}`),
        h("p", {}, error.message),
        error.details.length > 0 &&
          h("ul", { class: "status-details" }, ...error.details.map((item) => h("li", {}, item))),
        meta && h("p", { class: "status-meta" }, meta),
        ...extra,
      );
    },
    clear: () => {
      delete element.dataset.kind;
      element.replaceChildren();
    },
  };
}

export type Outcome<T> = { ok: true; value: T } | { ok: false; error: unknown };

/**
 * Run one SDK call for a page: show progress, report a failure with the
 * server's code and request id, and hand the typed result back. A timeout is
 * an abort too, so aborts are reported like any other failure.
 */
export async function attempt<T>(
  status: StatusArea,
  label: string,
  action: () => Promise<T>,
): Promise<Outcome<T>> {
  status.pending(`${label}：请求中…`);
  try {
    const value = await action();
    status.clear();
    return { ok: true, value };
  } catch (error) {
    status.fail(label, describeError(error));
    return { ok: false, error };
  }
}

/**
 * Run one SDK call and report the real outcome. P1 pages do not render result
 * data, so a 2xx response is reported as such rather than shown as content.
 */
export async function runAction(
  status: StatusArea,
  label: string,
  action: () => Promise<unknown>,
): Promise<void> {
  status.pending(`${label}：请求中…`);
  try {
    await action();
    status.done(`${label}：服务端返回了成功响应，但本页面尚未实现结果展示。`);
  } catch (error) {
    status.fail(label, describeError(error));
  }
}
