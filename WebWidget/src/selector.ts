/**
 * Knowledge-scope selector: single base, multi-base combination or auto.
 * It only builds a RetrievalSelection; validation and routing stay on the server.
 */

import type { KBTarget, RetrievalSelection } from "@qa/client";
import { h } from "./render.js";
import type { CatalogState } from "./state.js";

export type SelectorMode = "single" | "multi" | "auto";

export interface KnowledgeSelector {
  element: HTMLElement;
  setMode(mode: SelectorMode): void;
  toggleKnowledge(kbId: string, selected: boolean): void;
  /** Explicit modes with no knowledge base chosen return null. */
  readSelection(): RetrievalSelection | null;
  /** Replace the selector state from the host API; does not fire onChange. */
  reset(selection: RetrievalSelection): void;
  renderCatalog(catalog: CatalogState): void;
  /** Show the selection the next question will actually use. */
  renderEffective(selection: RetrievalSelection): void;
}

const MODE_LABELS: ReadonlyArray<readonly [SelectorMode, string]> = [
  ["single", "单库"],
  ["multi", "多库组合"],
  ["auto", "自动选库"],
];

let uid = 0;

export function createKnowledgeSelector(
  catalog: CatalogState,
  selection: RetrievalSelection,
  onChange: (selection: RetrievalSelection | null) => void,
): KnowledgeSelector {
  const group = `qa-scope-${++uid}`;
  let mode: SelectorMode = "auto";
  let targets: KBTarget[] = [];
  let auto: RetrievalSelection = { mode: "auto" };
  let lastCatalog = catalog;
  let names = new Map<string, string>();
  const kbInputs = new Map<string, HTMLInputElement>();

  const modeInputs = new Map<SelectorMode, HTMLInputElement>();
  const modeList = h("ul", { class: "qa-modes" });
  for (const [value, label] of MODE_LABELS) {
    const input = h("input", { type: "radio", name: `${group}-mode`, value });
    input.addEventListener("change", () => {
      if (input.checked) changeMode(value, true);
    });
    modeInputs.set(value, input);
    modeList.append(h("li", {}, h("label", {}, input, ` ${label}`)));
  }
  const status = h("p", { class: "qa-note", role: "note" });
  const list = h("ul", { class: "qa-kb-list" });
  const effective = h("p", { class: "qa-effective" });
  const element = h(
    "fieldset",
    { class: "qa-selector" },
    h("legend", {}, "知识库范围"),
    modeList,
    status,
    list,
    effective,
  );

  function load(next: RetrievalSelection): void {
    if (next.mode === "auto") {
      mode = "auto";
      auto = { ...next };
      targets = [];
    } else {
      targets = next.targets.map((target) => ({ ...target }));
      mode = targets.length > 1 ? "multi" : "single";
    }
    for (const [value, input] of modeInputs) input.checked = value === mode;
  }

  function label(kbId: string): string {
    return names.get(kbId) ?? kbId;
  }

  function renderStatus(): void {
    switch (lastCatalog.status) {
      case "idle":
        status.textContent = "打开插件后加载知识库目录。";
        break;
      case "loading":
        status.textContent = "正在加载知识库目录…";
        break;
      case "failed": {
        const { error } = lastCatalog;
        status.textContent = error.notImplemented
          ? `知识库目录尚未实现（${error.code ?? ""}），无法列出可选知识库。`
          : `知识库目录加载失败：${error.title}。`;
        break;
      }
      case "loaded":
        status.textContent =
          lastCatalog.items.length === 0 ? "没有可检索的知识库。" : "";
        break;
    }
    if (mode === "auto") status.append(" 自动选库由服务端按问题选择知识库。");
  }

  function renderList(): void {
    renderStatus();
    list.replaceChildren();
    kbInputs.clear();
    if (mode === "auto") return;
    const ids = lastCatalog.status === "loaded" ? lastCatalog.items.map((item) => item.kb_id) : [];
    for (const target of targets) if (!ids.includes(target.kb_id)) ids.push(target.kb_id);
    for (const kbId of ids) {
      const input = h("input", {
        type: mode === "single" ? "radio" : "checkbox",
        name: `${group}-kb`,
        value: kbId,
      });
      input.checked = targets.some((target) => target.kb_id === kbId);
      input.addEventListener("change", () => toggle(kbId, input.checked));
      kbInputs.set(kbId, input);
      list.append(h("li", {}, h("label", {}, input, ` ${label(kbId)}`)));
    }
  }

  function readSelection(): RetrievalSelection | null {
    if (mode === "auto") return { ...auto };
    const chosen = mode === "single" ? targets.slice(0, 1) : targets;
    if (chosen.length === 0) return null;
    return { mode: "explicit", targets: chosen.map((target) => ({ ...target })) };
  }

  function changeMode(next: SelectorMode, notify: boolean): void {
    mode = next;
    if (mode === "single") targets = targets.slice(0, 1);
    for (const [value, input] of modeInputs) input.checked = value === mode;
    renderList();
    if (notify) onChange(readSelection());
  }

  function toggle(kbId: string, selected: boolean): void {
    if (mode === "auto") return;
    if (mode === "single") {
      targets = selected ? [{ kb_id: kbId }] : targets.filter((t) => t.kb_id !== kbId);
    } else if (selected) {
      if (!targets.some((t) => t.kb_id === kbId)) targets = [...targets, { kb_id: kbId }];
    } else {
      targets = targets.filter((t) => t.kb_id !== kbId);
    }
    // Sync checked states in place so the focused input is not re-created.
    for (const [id, input] of kbInputs) input.checked = targets.some((t) => t.kb_id === id);
    onChange(readSelection());
  }

  load(selection);
  renderList();

  return {
    element,
    setMode: (next) => changeMode(next, true),
    toggleKnowledge: toggle,
    readSelection,
    reset(next) {
      load(next);
      renderList();
    },
    renderCatalog(next) {
      if (next === lastCatalog) return;
      lastCatalog = next;
      names =
        next.status === "loaded"
          ? new Map(next.items.map((item) => [item.kb_id, item.name]))
          : names;
      renderList();
    },
    renderEffective(current) {
      effective.textContent = `下一轮使用：${describeSelection(current, label)}`;
    },
  };
}

function describeSelection(selection: RetrievalSelection, label: (id: string) => string): string {
  if (selection.mode === "auto") {
    const ids = selection.candidate_kb_ids ?? [];
    const candidates = ids.length > 0 ? `，候选 ${ids.map(label).join("、")}` : "";
    const max = selection.max_kbs ? `，最多 ${selection.max_kbs} 个` : "";
    return `自动选库${candidates}${max}`;
  }
  const names = selection.targets.map(
    (target) => label(target.kb_id) + (target.version_id ? `@${target.version_id}` : ""),
  );
  return `${names.length === 1 ? "单库" : "多库组合"} ${names.join("、")}`;
}
