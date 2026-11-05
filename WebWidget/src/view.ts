/**
 * Widget DOM: floating launcher, dialog panel and messages, all inside an open
 * shadow root so host-page CSS cannot restyle the widget and the widget's CSS
 * cannot leak into the host page.
 */

import { h, renderSafeText } from "./render.js";
import type { ErrorView } from "./state.js";
import css from "./styles.css?inline";

export type MessageRole = "notice" | "user";
export type WidgetPosition = "bottom-right" | "bottom-left";

export const NOT_IMPLEMENTED_NOTICE =
  "问答功能尚未实现：当前为 P1 框架版本。提交的问题会发送到问答服务，插件如实显示服务端返回的结果。";

export interface PanelParts {
  panel: HTMLElement;
  scope: HTMLElement;
  messages: HTMLElement;
  status: HTMLElement;
  form: HTMLFormElement;
  input: HTMLTextAreaElement;
  send: HTMLButtonElement;
  closeButton: HTMLButtonElement;
}

export interface StatusView {
  info: string | null;
  error: ErrorView | null;
  submitting: boolean;
}

export interface WidgetView extends PanelParts {
  host: HTMLElement;
  root: ShadowRoot;
  launcher: HTMLButtonElement;
  setOpen(open: boolean): void;
  appendMessage(role: MessageRole, text: string): void;
  resetMessages(): void;
  renderStatus(status: StatusView): void;
  remove(): void;
}

let uid = 0;

export function createLauncher(title: string): HTMLButtonElement {
  return h(
    "button",
    {
      type: "button",
      class: "qa-launcher",
      "aria-label": title,
      "aria-haspopup": "dialog",
      "aria-expanded": "false",
    },
    "问",
  );
}

export function createPanel(id: string, title: string): PanelParts {
  const titleId = `${id}-title`;
  const inputId = `${id}-input`;
  const closeButton = h("button", { type: "button", class: "qa-close", "aria-label": "关闭" }, "×");
  const scope = h("section", { class: "qa-scope", "aria-label": "检索与推理范围" });
  const messages = h("div", {
    class: "qa-messages",
    role: "log",
    "aria-live": "polite",
    "aria-label": "对话消息",
  });
  const status = h("div", { class: "qa-status", role: "status", "aria-live": "polite" });
  const input = h("textarea", {
    id: inputId,
    class: "qa-input",
    rows: "2",
    placeholder: "输入问题，Enter 发送，Shift+Enter 换行",
  });
  const send = h("button", { type: "submit", class: "qa-send" }, "发送");
  const form = h(
    "form",
    { class: "qa-composer" },
    h("label", { class: "qa-sr-only", for: inputId }, "问题"),
    input,
    send,
  );
  const panel = h(
    "section",
    { id, class: "qa-panel", role: "dialog", "aria-labelledby": titleId, hidden: true },
    h(
      "header",
      { class: "qa-header" },
      h("h2", { id: titleId, class: "qa-title" }, title),
      h("span", { class: "qa-badge" }, "框架版 · 尚未实现"),
      closeButton,
    ),
    h("div", { class: "qa-body" }, scope, messages, status),
    form,
  );
  return { panel, scope, messages, status, form, input, send, closeButton };
}

/** Disabled placeholder: the widget sends no inference field in P1. */
export function createInferencePlaceholder(): HTMLElement {
  return h(
    "fieldset",
    { class: "qa-inference", disabled: true },
    h("legend", {}, "推理配置"),
    h(
      "label",
      {},
      "模型配置 ",
      h("select", { "aria-label": "模型配置" }, h("option", {}, "服务端默认")),
    ),
    h(
      "p",
      { class: "qa-note", role: "note" },
      "推理配置选择尚未实现：插件不发送 inference 字段，由服务端默认配置决定。",
    ),
  );
}

export function renderMessage(role: MessageRole, text: string): HTMLElement {
  return h("div", { class: `qa-message qa-message-${role}` }, renderSafeText(text));
}

export function createWidgetView(
  options: { title: string; position: WidgetPosition },
  container: HTMLElement,
): WidgetView {
  const id = `qa-widget-${++uid}`;
  const host = document.createElement("qa-widget");
  host.setAttribute("data-qa-widget", "");
  const root = host.attachShadow({ mode: "open" });
  adoptStyles(root);

  const launcher = createLauncher(options.title);
  const parts = createPanel(id, options.title);
  launcher.setAttribute("aria-controls", id);
  root.append(h("div", { class: "qa-root", "data-position": options.position }, launcher, parts.panel));
  container.append(host);

  const resetMessages = (): void => {
    parts.messages.replaceChildren(renderMessage("notice", NOT_IMPLEMENTED_NOTICE));
  };
  resetMessages();

  return {
    ...parts,
    host,
    root,
    launcher,
    setOpen(open) {
      parts.panel.hidden = !open;
      launcher.setAttribute("aria-expanded", String(open));
    },
    appendMessage(role, text) {
      parts.messages.append(renderMessage(role, text));
    },
    resetMessages,
    renderStatus({ info, error, submitting }) {
      const box = parts.status;
      box.replaceChildren();
      if (error) {
        box.dataset.kind = "error";
        box.append(h("p", { class: "qa-status-title" }, error.title), h("p", {}, error.message));
        const meta = [error.code, error.requestId && `request_id: ${error.requestId}`]
          .filter(Boolean)
          .join(" · ");
        if (meta) box.append(h("p", { class: "qa-status-meta" }, meta));
      } else {
        box.dataset.kind = "info";
        if (info) box.append(info);
      }
      parts.send.disabled = submitting;
      parts.send.textContent = submitting ? "提交中…" : "发送";
    },
    remove() {
      host.remove();
    },
  };
}

function adoptStyles(root: ShadowRoot): void {
  try {
    const sheet = new CSSStyleSheet();
    sheet.replaceSync(css);
    root.adoptedStyleSheets = [sheet];
    return;
  } catch {
    // Engines without constructable stylesheets get a <style> inside the shadow root.
  }
  root.append(h("style", {}, css));
}
