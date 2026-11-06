/**
 * Admin app state: current route, selected knowledge base and service status.
 * Holds no credentials or model secrets; page data stays inside each page. The
 * selected knowledge base lives in the URL hash (`#/content?kb=…`), so a reload
 * keeps it without browser storage.
 */

import type { Client } from "@qa/client";
import type { ErrorView } from "./components/ui.js";

export type RouteId = "knowledge" | "imports" | "content" | "versions" | "issues" | "qa" | "models";

export const ROUTES: ReadonlyArray<{ id: RouteId; label: string }> = [
  { id: "knowledge", label: "知识库" },
  { id: "imports", label: "导入" },
  { id: "content", label: "内容" },
  { id: "versions", label: "版本" },
  { id: "issues", label: "问题反馈" },
  { id: "qa", label: "试问" },
  { id: "models", label: "模型" },
];

export function isRouteId(value: string): value is RouteId {
  return ROUTES.some((route) => route.id === value);
}

export type ServiceState =
  | { status: "checking" }
  | { status: "online"; mode: string; unimplemented: string[] }
  | { status: "offline"; error: ErrorView };

export interface AppState {
  route: RouteId;
  /** Knowledge base the KB-scoped pages work on; null until one is chosen. */
  kbId: string | null;
  service: ServiceState;
}

export type AppAction =
  | { type: "route"; route: RouteId; kbId: string | null }
  | { type: "service"; service: ServiceState };

export type Listener = (state: AppState, previous: AppState) => void;

export interface Store {
  getState(): AppState;
  dispatch(action: AppAction): void;
  subscribe(listener: Listener): () => void;
}

/** What a page receives; pages register cleanup for anything they mount. */
export interface PageContext {
  client: Client;
  route: RouteId;
  kbId: string | null;
  /** Aborted when the page is left: pass it to every request the page starts. */
  signal: AbortSignal;
  onDispose(cleanup: () => void): void;
  /** Go to a page; `kbId` defaults to the current selection. */
  navigate(route: RouteId, kbId?: string | null, notice?: string): void;
  /** A one-time message carried over from the previous page's action. */
  notice?: string;
  /** Interval for polling job state; tests shorten it. */
  jobPollMs: number;
}

function reduce(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "route":
      return state.route === action.route && state.kbId === action.kbId
        ? state
        : { ...state, route: action.route, kbId: action.kbId };
    case "service":
      return { ...state, service: action.service };
  }
}

export function createStore(initial: AppState): Store {
  let state = initial;
  const listeners = new Set<Listener>();
  return {
    getState: () => state,
    dispatch(action) {
      const previous = state;
      state = reduce(state, action);
      if (state === previous) return;
      for (const listener of [...listeners]) listener(state, previous);
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

/** Parse `#/route?kb=id`; unknown routes fall back to the knowledge page. */
export function parseHash(hash: string): { route: RouteId; kbId: string | null } {
  const raw = hash.replace(/^#\/?/, "");
  const [path = "", query = ""] = raw.split("?", 2);
  const kb = new URLSearchParams(query).get("kb");
  return { route: isRouteId(path) ? path : "knowledge", kbId: kb ? kb : null };
}

export function formatHash(route: RouteId, kbId: string | null): string {
  return kbId ? `#/${route}?kb=${encodeURIComponent(kbId)}` : `#/${route}`;
}
