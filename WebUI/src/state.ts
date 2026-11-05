/**
 * Admin app state: current route and service status. Holds no credentials or
 * model secrets; page data stays inside each page.
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
  service: ServiceState;
}

export type AppAction =
  | { type: "route"; route: RouteId }
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
  onDispose(cleanup: () => void): void;
}

function reduce(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "route":
      return state.route === action.route ? state : { ...state, route: action.route };
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
