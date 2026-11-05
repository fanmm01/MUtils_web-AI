/**
 * Admin app entry: shell, hash navigation and page lifecycle. Navigation shows
 * every page including 模型; the server, not this UI, enforces permissions.
 */

import { createClient, type Client } from "@qa/client";
import { describeError, h } from "./components/ui.js";
import { renderContentPage } from "./pages/content.js";
import { renderImportPage } from "./pages/imports.js";
import { renderIssuesPage } from "./pages/issues.js";
import { renderKnowledgePage } from "./pages/knowledge.js";
import { renderModelsPage } from "./pages/models.js";
import { renderQAPage } from "./pages/qa.js";
import { renderVersionPage } from "./pages/versions.js";
import {
  ROUTES,
  createStore,
  isRouteId,
  type PageContext,
  type RouteId,
  type ServiceState,
  type Store,
} from "./state.js";
import "./styles.css";

const PAGES: Record<RouteId, (ctx: PageContext) => HTMLElement> = {
  knowledge: renderKnowledgePage,
  imports: renderImportPage,
  content: renderContentPage,
  versions: renderVersionPage,
  issues: renderIssuesPage,
  qa: renderQAPage,
  models: renderModelsPage,
};

interface App {
  root: HTMLElement;
  client: Client;
  store: Store;
  main: HTMLElement;
  badge: HTMLElement;
  links: Map<RouteId, HTMLAnchorElement>;
  cleanups: Array<() => void>;
  pageCleanups: Array<() => void>;
}

let app: App | null = null;

export interface MountOptions {
  /** Inject a client (tests); defaults to the same-origin API. */
  client?: Client;
}

export function mount(root: HTMLElement, options: MountOptions = {}): void {
  dispose();
  const client = options.client ?? createClient({ baseUrl: defaultApiBase() });
  const store = createStore({ route: routeFromHash(), service: { status: "checking" } });
  const badge = h("span", { class: "service-badge", role: "status" });
  const links = new Map<RouteId, HTMLAnchorElement>();
  const nav = h("nav", { class: "app-nav", "aria-label": "主导航" });
  const list = h("ul", {});
  for (const route of ROUTES) {
    const link = h("a", { href: `#/${route.id}` }, route.label);
    link.addEventListener("click", (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      navigate(route.id);
    });
    links.set(route.id, link);
    list.append(h("li", {}, link));
  }
  nav.append(list);
  const main = h("main", { class: "app-main", id: "main" });
  root.classList.add("qa-admin");
  root.replaceChildren(
    h("header", { class: "app-header" }, h("span", { class: "app-title" }, "问答小助手 · 知识库管理"), badge),
    nav,
    main,
  );

  const current: App = { root, client, store, main, badge, links, cleanups: [], pageCleanups: [] };
  app = current;
  current.cleanups.push(
    store.subscribe((state, previous) => {
      if (state.route !== previous.route) showPage(current, true);
      if (state.service !== previous.service) renderBadge(current, state.service);
    }),
  );
  const onHashChange = (): void => navigate(routeFromHash());
  window.addEventListener("hashchange", onHashChange);
  current.cleanups.push(() => window.removeEventListener("hashchange", onHashChange));

  renderBadge(current, store.getState().service);
  showPage(current, false);
  void checkService(current);
}

export function navigate(route: RouteId): void {
  if (!app) return;
  if (location.hash !== `#/${route}`) location.hash = `#/${route}`;
  app.store.dispatch({ type: "route", route });
}

export function dispose(): void {
  if (!app) return;
  const current = app;
  app = null;
  for (const cleanup of current.pageCleanups.splice(0)) cleanup();
  for (const cleanup of current.cleanups.splice(0)) cleanup();
  current.root.replaceChildren();
  current.root.classList.remove("qa-admin");
}

function showPage(current: App, moveFocus: boolean): void {
  for (const cleanup of current.pageCleanups.splice(0)) cleanup();
  const { route } = current.store.getState();
  const ctx: PageContext = {
    client: current.client,
    onDispose: (cleanup) => current.pageCleanups.push(cleanup),
  };
  current.main.replaceChildren(PAGES[route](ctx));
  for (const [id, link] of current.links) {
    if (id === route) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  const label = ROUTES.find((item) => item.id === route)?.label ?? "";
  document.title = `${label} · 问答小助手`;
  if (moveFocus) current.main.querySelector<HTMLElement>("h1")?.focus();
}

async function checkService(current: App): Promise<void> {
  try {
    const caps = await current.client.capabilities();
    if (app !== current) return;
    const unimplemented = Array.isArray(caps.unimplemented)
      ? caps.unimplemented.filter((item): item is string => typeof item === "string")
      : [];
    const mode = typeof caps.mode === "string" ? caps.mode : "unknown";
    current.store.dispatch({ type: "service", service: { status: "online", mode, unimplemented } });
  } catch (error) {
    if (app !== current) return;
    current.store.dispatch({ type: "service", service: { status: "offline", error: describeError(error) } });
  }
}

function renderBadge(current: App, service: ServiceState): void {
  const { badge } = current;
  badge.dataset.kind = service.status;
  switch (service.status) {
    case "checking":
      badge.textContent = "正在连接服务…";
      break;
    case "online":
      badge.textContent =
        service.mode === "scaffold"
          ? `服务：框架模式（${service.unimplemented.length} 项功能尚未实现）`
          : `服务：${service.mode}`;
      break;
    case "offline":
      badge.textContent = `服务不可用：${service.error.title}`;
      break;
  }
}

function routeFromHash(): RouteId {
  const value = location.hash.replace(/^#\/?/, "");
  return isRouteId(value) ? value : "knowledge";
}

function defaultApiBase(): string {
  const configured: unknown = import.meta.env.VITE_QA_API_BASE;
  return typeof configured === "string" && configured ? configured : location.origin;
}

const autoRoot = document.getElementById("app");
if (autoRoot) mount(autoRoot);
