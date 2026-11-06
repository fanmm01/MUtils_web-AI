/**
 * "Publish this version" panel shown after an import job or a content edit
 * produced a version. It reads the current active version first, says whether
 * the result is new, and publishes only after confirmation with
 * `expected_active_version_id`, so a concurrent change is a 409.
 */

import { confirmStrip, facts, idText } from "./data.js";
import { pageLink, type KBContext } from "./kb-context.js";
import { attempt, button, createStatusArea, h, isConflict, note, toolbar } from "./ui.js";
import type { PageContext } from "../state.js";

export function publishPanel(ctx: PageContext, kbc: KBContext, versionId: string | null): HTMLElement {
  const element = h("div", { class: "publish" });
  if (!versionId) {
    element.append(note("服务端没有返回结果版本。"));
    return element;
  }
  const status = createStatusArea();
  const slot = h("div", {});
  const publish = button("发布此版本", () => void run());
  const run = async (): Promise<void> => {
    if (!(await confirmStrip(slot, `确认把版本 ${versionId} 设为活动版本？之后的检索和问答将使用它。`, "确认发布"))) return;
    publish.disabled = true;
    const expected = kbc.current()?.active_version_id ?? null;
    const outcome = await attempt(status, "发布版本", () =>
      ctx.client.publishVersion(versionId, { expected_active_version_id: expected }, { signal: ctx.signal }),
    );
    if (outcome.ok) {
      await kbc.refresh();
      status.ok(`已发布：版本 ${versionId} 现在是活动版本。`);
      publish.remove();
      return;
    }
    publish.disabled = false;
    if (isConflict(outcome.error)) {
      status.element.append(h("p", {}, "活动版本已被其他操作改变，请到“版本”页核对后再发布。"), pageLink(ctx, "versions", "打开版本页"));
    }
  };
  void kbc.refresh().then((kb) => {
    if (ctx.signal.aborted) return;
    if (kb?.active_version_id === versionId) {
      element.replaceChildren(note(`版本 ${versionId} 已经是活动版本：内容没有变化，未产生新版本。`));
      return;
    }
    element.replaceChildren(
      h("p", {}, "新版本已构建，状态为“就绪，未发布”。发布前检索和问答仍使用原活动版本。"),
      facts([["结果版本", idText(versionId)]]),
      toolbar(publish, pageLink(ctx, "versions", "在版本页查看")),
      slot,
      status.element,
    );
  });
  return element;
}
