/**
 * Safe DOM construction. Text is always inserted as text nodes; model or
 * document content is never parsed as HTML.
 */

export type Child = Node | string | null | undefined | false;
export type Attrs = Record<string, string | boolean | undefined>;

export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Attrs = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  for (const [name, value] of Object.entries(attrs)) {
    if (value === undefined || value === false) continue;
    element.setAttribute(name, value === true ? "" : value);
  }
  element.append(...children.filter((child): child is Node | string => Boolean(child)));
  return element;
}

/** Plain text with line breaks preserved; no markup is interpreted. */
export function renderSafeText(text: string): DocumentFragment {
  const fragment = document.createDocumentFragment();
  text.split(/\r?\n/).forEach((line, index) => {
    if (index > 0) fragment.append(document.createElement("br"));
    fragment.append(document.createTextNode(line));
  });
  return fragment;
}
