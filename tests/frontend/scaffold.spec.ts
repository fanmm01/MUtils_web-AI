/**
 * P1-B scaffold acceptance: navigation, models page, widget lifecycle and
 * not-implemented states. The fake fetch answers like the P1 scaffold API
 * (200 for static capabilities, 501 FEATURE_NOT_IMPLEMENTED otherwise), so the
 * real SDK, pages and widget run end to end without a server.
 */

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { createClient, type Client } from "@qa/client";
import { mount as mountWidget, type WidgetHandle } from "@qa/widget";
import { afterEach, expect, test, vi } from "vitest";
import { dispose, mount, navigate } from "../../WebUI/src/main.js";
import { ROUTES } from "../../WebUI/src/state.js";

const API = "http://qa.test";
const REPO = process.env.QA_REPO_ROOT ?? "";
if (!REPO) throw new Error("QA_REPO_ROOT is set by tests/frontend/vitest.config.ts");

const CAPABILITIES = {
  mode: "scaffold",
  schema_version: 1,
  implemented: ["health", "readiness", "capabilities"],
  unimplemented: ["knowledge", "content", "imports", "sources", "versions", "search", "ask",
    "sessions", "feedback", "selection", "models", "jobs", "widget"],
  selection_limits: { max_candidate_kbs: 20, max_selected_kbs: 3 },
};
const MODEL_CAPABILITIES = { mode: "scaffold", runtimes: [], install_requires_confirmation: true };
const FEATURE_BY_PREFIX: ReadonlyArray<readonly [string, string]> = [
  ["/v1/kbs", "knowledge"],
  ["/v1/knowledge-catalog", "selection"],
  ["/v1/sessions", "sessions"],
  ["/v1/issues", "feedback"],
  ["/v1/models", "models"],
  ["/v1/inference-profiles", "models"],
];

interface Call {
  method: string;
  path: string;
  origin: string;
  body: unknown;
}

let requestSeq = 0;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": `req-${++requestSeq}` },
  });
}
/** A fake transport shaped like the P1 scaffold API; it records every call. */
function scaffoldServer(): { client: Client; calls: Call[] } {
  const calls: Call[] = [];
  const fetchImpl = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = new URL(String(input));
    const method = init?.method ?? "GET";
    const body = typeof init?.body === "string" ? JSON.parse(init.body) : undefined;
    calls.push({ method, path: url.pathname, origin: url.origin, body });
    if (method === "GET" && url.pathname === "/v1/capabilities") return json(200, CAPABILITIES);
    if (method === "GET" && url.pathname === "/v1/models/capabilities") {
      return json(200, MODEL_CAPABILITIES);
    }
    const feature =
      FEATURE_BY_PREFIX.find(([prefix]) => url.pathname.startsWith(prefix))?.[1] ?? "unknown";
    return json(501, {
      error: {
        code: "FEATURE_NOT_IMPLEMENTED",
        message: `'${feature}' is not implemented in the scaffold build`,
        details: [],
      },
      request_id: `req-${requestSeq}`,
    });
  };
  return { client: createClient({ baseUrl: API, fetch: fetchImpl }), calls };
}

const widgets: WidgetHandle[] = [];

function mountAdmin(): { root: HTMLElement; calls: Call[] } {
  const server = scaffoldServer();
  const root = document.createElement("div");
  document.body.append(root);
  mount(root, { client: server.client });
  return { root, calls: server.calls };
}

function mountTestWidget(): { handle: WidgetHandle; shadow: ShadowRoot; calls: Call[] } {
  const server = scaffoldServer();
  const handle = mountWidget({ client: server.client });
  widgets.push(handle);
  const host = document.querySelector("qa-widget");
  if (!host?.shadowRoot) throw new Error("widget host with an open shadow root was not created");
  return { handle, shadow: host.shadowRoot, calls: server.calls };
}

function byText<T extends Element>(scope: ParentNode, selector: string, text: string): T {
  const match = [...scope.querySelectorAll<T>(selector)].find(
    (element) => element.textContent?.trim() === text,
  );
  if (!match) throw new Error(`no ${selector} with text "${text}"`);
  return match;
}

function isDisabled(element: HTMLButtonElement): boolean {
  return element.disabled || element.closest("fieldset:disabled") !== null;
}

function textOf(scope: ParentNode, selector: string): string {
  return scope.querySelector(selector)?.textContent ?? "";
}

afterEach(() => {
  dispose();
  for (const handle of widgets.splice(0)) handle.destroy();
  document.body.replaceChildren();
  history.replaceState(null, "", "/");
});
test("testAdminNavigationIncludesModels", async () => {
  const { root } = mountAdmin();
  const labels = [...root.querySelectorAll("nav a")].map((link) => link.textContent);
  expect(labels).toEqual(ROUTES.map((route) => route.label));
  expect(labels).toContain("模型");
  expect(textOf(root, "main h1")).toBe("知识库");

  byText<HTMLAnchorElement>(root, "nav a", "模型").click();
  expect(textOf(root, "main h1")).toBe("模型");
  expect(byText(root, "nav a", "模型").getAttribute("aria-current")).toBe("page");
  expect(byText(root, "nav a", "知识库").hasAttribute("aria-current")).toBe(false);
  expect(location.hash).toBe("#/models");
  await vi.waitFor(() => expect(textOf(root, ".service-badge")).toContain("框架模式"));
});

test("testModelsPageNeverScansOrShowsFakeRuntime", async () => {
  const { root, calls } = mountAdmin();
  navigate("models");
  await vi.waitFor(() => expect(root.querySelector(".facts")?.textContent).toContain("scaffold"));

  // Rendering reads only the static capability endpoints from the configured API.
  expect(new Set(calls.map((call) => `${call.method} ${call.path}`))).toEqual(
    new Set(["GET /v1/capabilities", "GET /v1/models/capabilities"]),
  );
  expect(calls.every((call) => call.origin === API)).toBe(true);
  const facts = root.querySelector(".facts")?.textContent ?? "";
  expect(facts).toContain("0（服务端未配置任何运行时）");
  expect(facts).toContain("尚未检测");

  // Detection, profile editing and install cannot start from this page.
  for (const label of ["检测运行时", "生成安装预览", "确认安装", "保存为新修订"]) {
    expect(isDisabled(byText<HTMLButtonElement>(root, "button", label))).toBe(true);
  }
  // No editable endpoint, path, URL or key field.
  const inputs = [...root.querySelectorAll("main input")].map((input) => input.outerHTML).join(" ");
  expect(inputs).not.toMatch(/url|endpoint|path|key|token/i);

  byText<HTMLButtonElement>(root, "button", "刷新运行时列表").click();
  await vi.waitFor(() =>
    expect(root.querySelector("main")?.textContent).toContain("刷新运行时列表：尚未实现"),
  );
  expect(calls.at(-1)).toMatchObject({ method: "GET", path: "/v1/models/runtimes" });
  expect(calls.some((call) => call.path === "/v1/models/discovery")).toBe(false);
  expect(calls.some((call) => call.path.startsWith("/v1/model-installs"))).toBe(false);
  // The page lists no runtime or model rows it was not given.
  expect(root.querySelector("main")?.textContent).not.toMatch(/ollama|lm studio|llama\.cpp|qwen3|bge-m3/i);
});
test("testWidgetOpenCloseDestroy", () => {
  const { handle, shadow } = mountTestWidget();
  const launcher = shadow.querySelector<HTMLButtonElement>(".qa-launcher");
  const panel = shadow.querySelector<HTMLElement>(".qa-panel");
  if (!launcher || !panel) throw new Error("launcher or panel missing");
  expect(panel.hidden).toBe(true);
  expect(launcher.getAttribute("aria-expanded")).toBe("false");
  expect(panel.getAttribute("role")).toBe("dialog");

  launcher.click();
  expect(panel.hidden).toBe(false);
  expect(launcher.getAttribute("aria-expanded")).toBe("true");
  expect(shadow.activeElement).toBe(shadow.querySelector("textarea"));

  shadow.querySelector("textarea")?.dispatchEvent(
    new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
  );
  expect(panel.hidden).toBe(true);
  expect(shadow.activeElement).toBe(launcher);

  handle.open();
  expect(panel.hidden).toBe(false);
  shadow.querySelector<HTMLButtonElement>(".qa-close")?.click();
  expect(panel.hidden).toBe(true);

  // Styles live in the shadow root only; nothing is injected into the host page.
  expect(document.head.querySelector("style")).toBeNull();

  handle.destroy();
  expect(document.querySelector("qa-widget")).toBeNull();
  expect(() => {
    handle.open();
    handle.close();
    handle.destroy();
  }).not.toThrow();
});

test("testSelectionAndInferenceControlsRemainScaffold", async () => {
  const { handle, shadow, calls } = mountTestWidget();
  handle.open();
  const selector = shadow.querySelector(".qa-selector");
  if (!selector) throw new Error("knowledge selector missing");
  await vi.waitFor(() => expect(selector.textContent).toContain("知识库目录尚未实现"));

  for (const label of ["单库", "多库组合", "自动选库"]) {
    expect(byText(selector, "label", label).querySelector("input[type=radio]")).not.toBeNull();
  }
  expect(selector.querySelectorAll(".qa-kb-list li")).toHaveLength(0);
  expect(textOf(selector, ".qa-effective")).toBe("下一轮使用：自动选库");

  // Choosing an explicit mode without a catalog cannot invent a knowledge base.
  byText(selector, "label", "单库").querySelector<HTMLInputElement>("input")?.click();
  expect(handle.getSelection()).toEqual({ mode: "auto" });
  expect(textOf(selector, ".qa-effective")).toBe("下一轮使用：自动选库");
  expect(textOf(shadow, ".qa-status")).toContain("请先选择知识库");

  const inference = shadow.querySelector<HTMLFieldSetElement>(".qa-inference");
  expect(inference?.disabled).toBe(true);
  expect(inference?.textContent).toContain("推理配置选择尚未实现");

  expect(calls.map((call) => `${call.method} ${call.path}`)).toEqual(["GET /v1/knowledge-catalog"]);
});
test("testVisibleNotImplementedState", () => {
  const { root } = mountAdmin();
  for (const route of ROUTES) {
    navigate(route.id);
    expect(textOf(root, "main h1")).toBe(route.label);
    expect(textOf(root, "main .banner")).toContain("尚未实现");
  }
  // The 试问 page mounts the real widget and removes it when the page is left.
  navigate("qa");
  expect(document.querySelectorAll("qa-widget")).toHaveLength(1);
  navigate("knowledge");
  expect(document.querySelectorAll("qa-widget")).toHaveLength(0);
});

test("testNoFakeSuccessOrAnswer", async () => {
  const { root, calls } = mountAdmin();
  const form = root.querySelector<HTMLFormElement>("form[aria-label=新建知识库]");
  const name = form?.querySelector<HTMLInputElement>("input[name=name]");
  if (!form || !name) throw new Error("create form missing");
  name.value = "产品手册";
  form.requestSubmit();
  await vi.waitFor(() => expect(form.textContent).toContain("创建知识库：尚未实现"));
  expect(form.textContent).toContain("FEATURE_NOT_IMPLEMENTED");
  expect(calls.at(-1)).toMatchObject({
    method: "POST",
    path: "/v1/kbs",
    body: { name: "产品手册", description: "", domain_tags: [] },
  });
  expect(root.querySelector("main")?.textContent).not.toContain("成功");
  const rows = root.querySelectorAll("main tbody tr");
  expect(rows).toHaveLength(1);
  expect(rows[0]?.textContent).toContain("尚未实现");
  dispose();

  const widget = mountTestWidget();
  widget.handle.open();
  const input = widget.shadow.querySelector<HTMLTextAreaElement>("textarea");
  if (!input) throw new Error("widget input missing");
  input.value = "如何升级？";
  input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  await vi.waitFor(() => expect(textOf(widget.shadow, ".qa-status")).toContain("尚未实现"));
  expect(textOf(widget.shadow, ".qa-status")).toContain("FEATURE_NOT_IMPLEMENTED");
  // The question was not accepted, so it is not shown as a sent message.
  expect(widget.shadow.querySelectorAll(".qa-message")).toHaveLength(1);
  expect(widget.shadow.querySelector(".qa-message-notice")).not.toBeNull();
  expect(input.value).toBe("如何升级？");
  expect(widget.calls.map((call) => `${call.method} ${call.path}`)).toEqual([
    "GET /v1/knowledge-catalog",
    "POST /v1/sessions",
  ]);
  expect(widget.calls[1]?.body).toEqual({ selection: { mode: "auto" } });
});

function collectFiles(dir: string, extensions: string[]): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return collectFiles(path, extensions);
    return extensions.some((ext) => name.endsWith(ext)) ? [path] : [];
  });
}

const FORBIDDEN_IN_SOURCE: ReadonlyArray<readonly [RegExp, string]> = [
  [/\b(localStorage|sessionStorage|indexedDB)\b|document\.cookie/, "browser storage: no credential or secret is persisted"],
  [/\.innerHTML\b|\.outerHTML\s*=|insertAdjacentHTML|document\.write/, "HTML injection"],
  [/\beval\s*\(|new\s+Function\s*\(/, "dynamic code execution"],
  [/localhost|127\.0\.0\.1|:11434\b|:1234\b/, "hard-coded local endpoint: runtimes are reached only through the server"],
  [/navigator\.(mediaDevices|usb|hid|serial|bluetooth|getBattery)/, "probing the browser's machine"],
  [/fixtures?\//, "test fixtures in the default build"],
];

test("static: front-end source has no storage, injection, local probing or fixtures", () => {
  const files = [
    ...collectFiles(join(REPO, "WebUI/src"), [".ts", ".css"]),
    ...collectFiles(join(REPO, "WebWidget/src"), [".ts", ".css"]),
    join(REPO, "WebUI/index.html"),
  ];
  const violations = files.flatMap((file) => {
    const text = readFileSync(file, "utf8");
    return FORBIDDEN_IN_SOURCE.filter(([pattern]) => pattern.test(text)).map(
      ([, reason]) => `${file.slice(REPO.length)}: ${reason}`,
    );
  });
  expect(violations).toEqual([]);
});

test("static: the widget never imports admin UI code", () => {
  const offenders = collectFiles(join(REPO, "WebWidget/src"), [".ts"]).filter((file) =>
    /from\s+["'][^"']*(WebUI|@qa\/webui)/.test(readFileSync(file, "utf8")),
  );
  expect(offenders).toEqual([]);
});

const bundleDirs = ["WebUI/dist", "WebWidget/dist"].map((dir) => join(REPO, dir));

test.skipIf(!bundleDirs.every((dir) => existsSync(dir)))(
  "static: built bundles contain no answer-event fixture data",
  () => {
    const leaks = bundleDirs
      .flatMap((dir) => collectFiles(dir, [".js"]))
      .filter((file) => /answer_fixture|session_fixture|binding_fixture|answer-events\.schema/.test(readFileSync(file, "utf8")));
    expect(leaks).toEqual([]);
  },
);
