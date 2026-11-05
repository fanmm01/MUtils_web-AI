/**
 * Widget state: UI lifecycle, knowledge catalog, next-turn selection and the
 * submit request. P1 has no answer stream, so no answer events are reduced here;
 * the server rejects session creation with 501 before any event could exist.
 */

import { QAError, type RetrievalSelection } from "@qa/client";

export interface ErrorView {
  title: string;
  message: string;
  code?: string;
  requestId?: string;
  notImplemented: boolean;
}

/** Only the catalog fields this widget displays. */
export interface CatalogItem {
  kb_id: string;
  name: string;
}

export type CatalogState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "loaded"; items: CatalogItem[] }
  | { status: "failed"; error: ErrorView };

export interface WidgetState {
  open: boolean;
  destroyed: boolean;
  catalog: CatalogState;
  /** Selection used by the next question; never null. */
  selection: RetrievalSelection;
  sessionId: string | null;
  scopeRevision: number | null;
  submitting: boolean;
  info: string | null;
  error: ErrorView | null;
}

export type WidgetEvent =
  | { type: "open" }
  | { type: "close" }
  | { type: "destroy" }
  | { type: "catalog/loading" }
  | { type: "catalog/loaded"; items: CatalogItem[] }
  | { type: "catalog/failed"; error: ErrorView }
  | { type: "selection/set"; selection: RetrievalSelection; scopeRevision?: number }
  | { type: "selection/incomplete" }
  | { type: "request/failed"; error: ErrorView }
  | { type: "submit/start" }
  | { type: "session/created"; sessionId: string; scopeRevision: number }
  | { type: "submit/accepted"; answerId: string }
  | { type: "submit/failed"; error: ErrorView };

export function createState(options: { initialSelection?: RetrievalSelection | null }): WidgetState {
  return {
    open: false,
    destroyed: false,
    catalog: { status: "idle" },
    selection: options.initialSelection ?? { mode: "auto" },
    sessionId: null,
    scopeRevision: null,
    submitting: false,
    info: null,
    error: null,
  };
}

export function reduce(state: WidgetState, event: WidgetEvent): WidgetState {
  if (state.destroyed) return state;
  switch (event.type) {
    case "open":
      return { ...state, open: true };
    case "close":
      return { ...state, open: false };
    case "destroy":
      return { ...state, open: false, destroyed: true };
    case "catalog/loading":
      return { ...state, catalog: { status: "loading" } };
    case "catalog/loaded":
      return { ...state, catalog: { status: "loaded", items: event.items } };
    case "catalog/failed":
      return { ...state, catalog: { status: "failed", error: event.error } };
    case "selection/set":
      return {
        ...state,
        selection: event.selection,
        scopeRevision: event.scopeRevision ?? state.scopeRevision,
        error: null,
        info: state.sessionId ? "已更新会话默认范围，下一轮生效。" : null,
      };
    case "selection/incomplete":
      return { ...state, info: "请先选择知识库；在选定前，下一次提问仍使用上方显示的范围。" };
    case "request/failed":
      return { ...state, info: null, error: event.error };
    case "submit/start":
      return { ...state, submitting: true, info: "正在提交…", error: null };
    case "session/created":
      return { ...state, sessionId: event.sessionId, scopeRevision: event.scopeRevision };
    case "submit/accepted":
      return {
        ...state,
        submitting: false,
        info: `服务已受理问题（answer_id: ${event.answerId}），本版本尚未实现回答展示。`,
      };
    case "submit/failed":
      return { ...state, submitting: false, info: null, error: event.error };
  }
}

export function canSubmit(state: WidgetState, text: string): boolean {
  return !state.destroyed && !state.submitting && text.trim().length > 0;
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
