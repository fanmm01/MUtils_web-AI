/**
 * Classic-script entry (dist/qa-widget.iife.js). The IIFE build exposes this
 * module as window.QAWidget and auto-mounts from the loading script's
 * non-sensitive data attributes. Hosts needing a credential getter call
 * QAWidget.mount() themselves and set data-auto-mount="false".
 */

import type { RetrievalSelection } from "@qa/client";
import { mount, type WidgetHandle, type WidgetOptions } from "./index.js";

export { mount };
export type { WidgetHandle, WidgetOptions };

const mounted = new WeakMap<HTMLScriptElement, WidgetHandle>();

export function autoMount(script: HTMLScriptElement): WidgetHandle | null {
  const existing = mounted.get(script);
  if (existing) return existing;
  const data = script.dataset;
  if (!data.apiBase || data.autoMount === "false") return null;

  const options: WidgetOptions = { apiBase: data.apiBase, openOnMount: data.open === "true" };
  if (data.title) options.title = data.title;
  if (data.position === "bottom-left" || data.position === "bottom-right") {
    options.position = data.position;
  }
  const selection = readSelection(data);
  if (selection) options.initialSelection = selection;

  const handle = mount(options);
  const destroy = handle.destroy;
  handle.destroy = () => {
    mounted.delete(script);
    destroy();
  };
  mounted.set(script, handle);
  return handle;
}

function readSelection(data: DOMStringMap): RetrievalSelection | null {
  const ids = [...new Set((data.kbIds ?? "").split(",").map((id) => id.trim()).filter(Boolean))];
  if (data.selectionMode === "explicit") {
    return ids.length > 0 ? { mode: "explicit", targets: ids.map((kb_id) => ({ kb_id })) } : null;
  }
  const selection: RetrievalSelection = { mode: "auto" };
  if (ids.length > 0) selection.candidate_kb_ids = ids;
  const max = Number(data.maxKbs);
  if (Number.isInteger(max) && max >= 1) selection.max_kbs = max;
  return selection;
}

const current = typeof document === "undefined" ? null : document.currentScript;
if (current instanceof HTMLScriptElement) {
  if (document.body) autoMount(current);
  else document.addEventListener("DOMContentLoaded", () => autoMount(current), { once: true });
}
