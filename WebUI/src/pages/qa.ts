import { mount, type WidgetHandle, type WidgetOptions } from "@qa/widget";
import { h, note, pageHeader, section } from "../components/ui.js";
import type { PageContext } from "../state.js";

export function renderQAPage(ctx: PageContext): HTMLElement {
  const slot = h("div", { class: "widget-slot" });
  const handle = mountQAWidget(slot, { client: ctx.client, title: "试问", openOnMount: true });
  ctx.onDispose(() => handle.destroy());
  return h(
    "div",
    { class: "page" },
    pageHeader("试问", "试问页直接复用网页插件；问答、引用和每轮实际范围展示将在 P3 实现。"),
    section(
      "说明",
      note("右下角的弹窗就是嵌入网站时的同一个插件，管理端不另写问答逻辑。"),
      note("知识库范围（单库、多库组合、自动选库）和推理配置控件都在插件弹窗内。"),
    ),
    slot,
  );
}

/** Mount the standalone widget; the admin UI never copies its logic. */
export function mountQAWidget(container: HTMLElement, options: WidgetOptions): WidgetHandle {
  return mount({ ...options, container });
}
