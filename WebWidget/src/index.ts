/**
 * Public widget entry. Each mount() call creates an independent instance with
 * its own shadow root, state and session. Permissions come from the credential
 * the host supplies, never from these options.
 */

import { createClient, type Client, type RetrievalSelection } from "@qa/client";
import { WidgetController } from "./controller.js";
import type { WidgetPosition } from "./view.js";

export interface WidgetOptions {
  /** Absolute base URL of the Q&A service, e.g. "https://qa.example.com". */
  apiBase?: string;
  /** Host-provided short-lived ticket getter; the widget never stores it. */
  getCredential?: () => string | null | Promise<string | null>;
  /** Default scope for the first session; omitted means auto selection. */
  initialSelection?: RetrievalSelection | null;
  title?: string;
  position?: WidgetPosition;
  /** Where the widget host element is appended; defaults to document.body. */
  container?: HTMLElement;
  openOnMount?: boolean;
  showKnowledgeSelector?: boolean;
  showInferenceSelector?: boolean;
  /** Pre-built SDK client (tests, or hosts sharing one client). */
  client?: Client;
}

export interface WidgetHandle {
  open(): void;
  close(): void;
  setSelection(selection: RetrievalSelection): Promise<void>;
  getSelection(): RetrievalSelection;
  destroy(): void;
}

export type { WidgetPosition };

export function mount(options: WidgetOptions): WidgetHandle {
  const client = options.client ?? defaultClient(options);
  const controller = new WidgetController({
    client,
    title: options.title ?? "问答助手",
    position: options.position ?? "bottom-right",
    container: options.container ?? document.body,
    initialSelection: options.initialSelection ?? null,
    showKnowledgeSelector: options.showKnowledgeSelector ?? true,
    showInferenceSelector: options.showInferenceSelector ?? true,
  });
  if (options.openOnMount) controller.open({ focus: false });
  return {
    open: () => controller.open(),
    close: () => controller.close(),
    setSelection: (selection) => controller.setSelection(selection),
    getSelection: () => controller.getSelection(),
    destroy: () => controller.destroy(),
  };
}

function defaultClient(options: WidgetOptions): Client {
  if (!options.apiBase) throw new Error("QAWidget.mount: apiBase or client is required");
  return createClient({
    baseUrl: options.apiBase,
    ...(options.getCredential ? { getCredential: options.getCredential } : {}),
  });
}
