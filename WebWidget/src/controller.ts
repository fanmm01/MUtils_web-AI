/**
 * WidgetController wires the view, selector and state to the shared SDK.
 * Every server call goes through @qa/client; nothing here fabricates a response.
 */

import type { Client, RetrievalSelection } from "@qa/client";
import { createKnowledgeSelector, type KnowledgeSelector } from "./selector.js";
import {
  canSubmit,
  createState,
  describeError,
  reduce,
  type CatalogItem,
  type WidgetEvent,
  type WidgetState,
} from "./state.js";
import {
  createInferencePlaceholder,
  createWidgetView,
  type WidgetPosition,
  type WidgetView,
} from "./view.js";

export interface ControllerOptions {
  client: Client;
  title: string;
  position: WidgetPosition;
  container: HTMLElement;
  initialSelection: RetrievalSelection | null;
  showKnowledgeSelector: boolean;
  showInferenceSelector: boolean;
}

export class WidgetController {
  private state: WidgetState;
  private readonly client: Client;
  private readonly view: WidgetView;
  private readonly selector: KnowledgeSelector | null;
  private readonly cleanups: Array<() => void> = [];
  private catalogRequested = false;

  constructor(options: ControllerOptions) {
    this.client = options.client;
    this.state = createState({ initialSelection: options.initialSelection });
    this.view = createWidgetView(
      { title: options.title, position: options.position },
      options.container,
    );
    this.selector = options.showKnowledgeSelector
      ? createKnowledgeSelector(this.state.catalog, this.state.selection, (selection) => {
          void this.applySelection(selection, false);
        })
      : null;
    if (this.selector) this.view.scope.append(this.selector.element);
    if (options.showInferenceSelector) this.view.scope.append(createInferencePlaceholder());
    this.bind();
    this.render();
  }

  open(options: { focus?: boolean } = {}): void {
    if (this.state.destroyed || this.state.open) return;
    this.dispatch({ type: "open" });
    if (options.focus ?? true) this.view.input.focus();
    if (this.selector && !this.catalogRequested) {
      this.catalogRequested = true;
      void this.loadKnowledgeCatalog();
    }
  }

  close(): void {
    if (this.state.destroyed || !this.state.open) return;
    const focusInside = this.view.root.activeElement !== null;
    this.dispatch({ type: "close" });
    if (focusInside) this.view.launcher.focus();
  }

  async loadKnowledgeCatalog(): Promise<void> {
    if (this.state.destroyed) return;
    this.dispatch({ type: "catalog/loading" });
    try {
      const page = await this.client.getKnowledgeCatalog();
      this.dispatch({ type: "catalog/loaded", items: toCatalogItems(page.items) });
    } catch (error) {
      this.dispatch({ type: "catalog/failed", error: describeError(error) });
    }
  }

  /** Host API: also moves the selector UI to the given selection. */
  async setSelection(selection: RetrievalSelection): Promise<void> {
    await this.applySelection(selection, true);
  }

  getSelection(): RetrievalSelection {
    return copySelection(this.state.selection);
  }

  async send(text: string): Promise<void> {
    const question = text.trim();
    if (!canSubmit(this.state, question)) return;
    this.dispatch({ type: "submit/start" });
    try {
      let { sessionId } = this.state;
      if (!sessionId) {
        const session = await this.client.createSession({ selection: this.state.selection });
        if (this.state.destroyed) return;
        sessionId = session.session_id;
        this.dispatch({ type: "session/created", sessionId, scopeRevision: session.scope_revision });
      }
      const response = await this.client.submitAnswer(
        sessionId,
        { question },
        { idempotencyKey: newIdempotencyKey() },
      );
      if (this.state.destroyed) return;
      const answerId = response.handle?.answer_id ?? response.answer?.answer_id;
      if (!answerId) throw new Error("服务响应缺少 answer_id");
      this.view.appendMessage("user", question);
      this.view.input.value = "";
      this.dispatch({ type: "submit/accepted", answerId });
    } catch (error) {
      this.dispatch({ type: "submit/failed", error: describeError(error) });
    }
  }

  destroy(): void {
    if (this.state.destroyed) return;
    this.dispatch({ type: "destroy" });
    for (const cleanup of this.cleanups.splice(0)) cleanup();
    this.view.remove();
  }

  private async applySelection(
    selection: RetrievalSelection | null,
    syncSelector: boolean,
  ): Promise<void> {
    if (this.state.destroyed) return;
    if (!selection || (selection.mode === "explicit" && selection.targets.length === 0)) {
      this.dispatch({ type: "selection/incomplete" });
      return;
    }
    if (syncSelector) this.selector?.reset(selection);
    const { sessionId, scopeRevision } = this.state;
    if (!sessionId || scopeRevision === null) {
      // No session yet: the selection becomes the new session's default.
      this.dispatch({ type: "selection/set", selection });
      return;
    }
    try {
      const session = await this.client.setSessionSelection(sessionId, {
        selection,
        expected_scope_revision: scopeRevision,
      });
      this.dispatch({
        type: "selection/set",
        selection: session.selection,
        scopeRevision: session.scope_revision,
      });
    } catch (error) {
      this.dispatch({ type: "request/failed", error: describeError(error) });
    }
  }

  private bind(): void {
    const { launcher, closeButton, form, input, root } = this.view;
    this.listen(launcher, "click", () => (this.state.open ? this.close() : this.open()));
    this.listen(closeButton, "click", () => this.close());
    this.listen(form, "submit", (event) => {
      event.preventDefault();
      void this.send(input.value);
    });
    this.listen(input, "keydown", (event) => {
      const key = event as KeyboardEvent;
      if (key.key === "Enter" && !key.shiftKey && !key.isComposing) {
        key.preventDefault();
        void this.send(input.value);
      }
    });
    this.listen(root, "keydown", (event) => {
      if ((event as KeyboardEvent).key === "Escape") this.close();
    });
  }

  private listen(target: EventTarget, type: string, handler: (event: Event) => void): void {
    target.addEventListener(type, handler);
    this.cleanups.push(() => target.removeEventListener(type, handler));
  }

  private dispatch(event: WidgetEvent): void {
    const next = reduce(this.state, event);
    if (next === this.state) return;
    this.state = next;
    this.render();
  }

  private render(): void {
    const { state, view, selector } = this;
    view.setOpen(state.open);
    view.renderStatus(state);
    selector?.renderCatalog(state.catalog);
    selector?.renderEffective(state.selection);
  }
}

/** The SDK types the catalog loosely; keep only well-formed entries. */
function toCatalogItems(items: unknown): CatalogItem[] {
  if (!Array.isArray(items)) return [];
  const result: CatalogItem[] = [];
  for (const item of items) {
    if (item && typeof item === "object") {
      const { kb_id, name } = item as Record<string, unknown>;
      if (typeof kb_id === "string" && typeof name === "string") result.push({ kb_id, name });
    }
  }
  return result;
}

/** Plain copy; avoids structuredClone, which older host pages may lack. */
function copySelection(selection: RetrievalSelection): RetrievalSelection {
  if (selection.mode === "explicit") {
    return { mode: "explicit", targets: selection.targets.map((target) => ({ ...target })) };
  }
  const copy: RetrievalSelection = { ...selection };
  if (selection.candidate_kb_ids) copy.candidate_kb_ids = [...selection.candidate_kb_ids];
  return copy;
}

function newIdempotencyKey(): string {
  // randomUUID exists only in secure contexts; hosts may embed over plain HTTP.
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}
