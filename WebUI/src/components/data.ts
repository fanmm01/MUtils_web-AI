/**
 * Data display shared by the admin pages: tables with explicit loading, empty
 * and failure rows, fact lists, times and ids, and a two-step confirmation for
 * destructive actions. Everything is built with DOM APIs; server text is never
 * parsed as HTML.
 */

import { h, type Child } from "./ui.js";

export interface DataTable {
  element: HTMLTableElement;
  /** Replace the body; an empty list shows `empty`. */
  setRows(rows: HTMLTableRowElement[], empty: string): void;
  appendRows(rows: HTMLTableRowElement[]): void;
  /** One full-width row instead of data: loading, failure, "select first". */
  setMessage(text: string, kind?: "info" | "error"): void;
}

export function dataTable(caption: string, headers: string[]): DataTable {
  const body = h("tbody", {});
  const element = h(
    "table",
    { class: "table" },
    h("caption", {}, caption),
    h("thead", {}, h("tr", {}, ...headers.map((label) => h("th", { scope: "col" }, label)))),
    body,
  );
  const setMessage = (text: string, kind: "info" | "error" = "info"): void => {
    body.replaceChildren(
      h("tr", {}, h("td", { colspan: String(headers.length), class: kind === "error" ? "empty error" : "empty" }, text)),
    );
  };
  return {
    element,
    setRows(rows, empty) {
      if (rows.length === 0) setMessage(empty);
      else body.replaceChildren(...rows);
    },
    appendRows(rows) {
      body.append(...rows);
    },
    setMessage,
  };
}

export function row(cells: Child[], attrs: Record<string, string> = {}): HTMLTableRowElement {
  return h("tr", attrs, ...cells.map((cell) => h("td", {}, cell)));
}

const TIME_FORMAT = new Intl.DateTimeFormat("zh-CN", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
});

export function formatTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : TIME_FORMAT.format(date);
}

export function idText(value: string | null | undefined): HTMLElement | string {
  return value ? h("code", { class: "id" }, value) : "—";
}

export function facts(entries: Array<[string, Child]>): HTMLElement {
  const list = h("dl", { class: "facts" });
  for (const [label, value] of entries) list.append(h("dt", {}, label), h("dd", {}, value ?? "—"));
  return list;
}

/**
 * Show "确认…？ [确认] [取消]" next to a destructive action. Resolves true only
 * when the user confirms; nothing is sent before that.
 */
export function confirmStrip(slot: HTMLElement, message: string, confirmLabel: string): Promise<boolean> {
  return new Promise((resolve) => {
    const confirm = h("button", { type: "button", class: "danger" }, confirmLabel);
    const cancel = h("button", { type: "button", class: "secondary" }, "取消");
    const strip = h("div", { class: "confirm", role: "group", "aria-label": "确认操作" }, h("p", {}, message), confirm, cancel);
    const finish = (value: boolean): void => {
      strip.remove();
      resolve(value);
    };
    confirm.addEventListener("click", () => finish(true));
    cancel.addEventListener("click", () => finish(false));
    slot.replaceChildren(strip);
    cancel.focus();
  });
}

export function listOf(items: string[], empty: string): HTMLElement {
  if (items.length === 0) return h("p", { class: "note" }, empty);
  return h("ul", { class: "path-list" }, ...items.map((item) => h("li", {}, h("code", {}, item))));
}
