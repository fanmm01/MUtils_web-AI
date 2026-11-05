import { field, h, note, pageHeader, section, toolbar } from "../components/ui.js";

export function renderContentPage(): HTMLElement {
  return h(
    "div",
    { class: "page" },
    pageHeader("内容", "文档与问答对的增删改查将在 P2 实现。"),
    section(
      "文档",
      h(
        "fieldset",
        { class: "form", disabled: true },
        h("legend", {}, "编辑文档"),
        field("标题", h("input", {})),
        field("规范化正文", h("textarea", { rows: "6" })),
        field("替换原件", h("input", { type: "file" })),
        toolbar(h("button", { type: "button" }, "保存为新修订"), h("button", { type: "button" }, "删除")),
      ),
      note("需要先选择知识库和文档；内容管理尚未实现。编辑正文会产生新修订，不会回写原 Word 文件。"),
    ),
    section(
      "问答对",
      h(
        "fieldset",
        { class: "form", disabled: true },
        h("legend", {}, "编辑问答对"),
        field("问题", h("input", {})),
        field("答案", h("textarea", { rows: "4" })),
        toolbar(h("button", { type: "button" }, "保存"), h("button", { type: "button" }, "删除")),
      ),
      note("问答对录入尚未实现。"),
    ),
  );
}
