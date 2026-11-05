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
      notImplemented,
    };
    if (error.requestId) view.requestId = error.requestId;
    return view;
  }
  if (error instanceof DOMException && error.name === "AbortError") {
    return { title: "请求已中止", message: "请求超时或已被取消。", notImplemented: false };
  }
  if (error instanceof TypeError) {
    return { title: "无法连接问答服务", message: error.message, notImplemented: false };
  }
  return { title: "请求失败", message: String(error), notImplemented: false };
}

export interface StatusArea {
  element: HTMLElement;
  pending(text: string): void;
  done(text: string): void;
  fail(label: string, error: ErrorView): void;
}

export function createStatusArea(): StatusArea {
  const element = h("div", { class: "status", role: "status", "aria-live": "polite" });
  const set = (kind: string, ...children: Child[]): void => {
    element.dataset.kind = kind;
    element.replaceChildren(...present(children));
  };
  return {
    element,
    pending: (text) => set("pending", text),
    done: (text) => set("info", text),
    fail: (label, error) => {
      const meta = [error.code, error.requestId && `request_id: ${error.requestId}`]
        .filter(Boolean)
        .join(" · ");
      set(
        "error",
        h("p", { class: "status-title" }, `${label}：${error.title}`),
        h("p", {}, error.message),
        meta && h("p", { class: "status-meta" }, meta),
      );
    },
  };
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
