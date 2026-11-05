import { field, h, note, pageHeader, section, toolbar } from "../components/ui.js";

/** Files the user picked in this browser; nothing is uploaded in P1. */
export interface UploadSelection {
  files: Array<{ relativePath: string; size: number; selected: boolean }>;
}

const MAX_LISTED = 200;

export function renderImportPage(): HTMLElement {
  let selection: UploadSelection = { files: [] };
  const summary = h("p", { class: "note", role: "status" }, "尚未选择目录。");
  const fileList = h("ul", { class: "file-list" });

  const picker = h("input", { type: "file", multiple: true, webkitdirectory: true });
  picker.addEventListener("change", () => {
    selection = selectDirectory(picker.files ?? []);
    renderFiles();
  });

  function renderFiles(): void {
    fileList.replaceChildren();
    for (const file of selection.files.slice(0, MAX_LISTED)) {
      const box = h("input", { type: "checkbox" });
      box.checked = file.selected;
      box.addEventListener("change", () => {
        toggleFile(selection, file.relativePath, box.checked);
        renderSummary();
      });
      fileList.append(h("li", {}, h("label", {}, box, ` ${file.relativePath}（${file.size} 字节）`)));
    }
    renderSummary();
  }

  function renderSummary(): void {
    const total = selection.files.length;
    const chosen = selection.files.filter((file) => file.selected).length;
    const hidden = total > MAX_LISTED ? `，列表只显示前 ${MAX_LISTED} 个` : "";
    summary.textContent =
      total === 0
        ? "尚未选择目录。"
        : `已在浏览器中选择 ${total} 个文件，勾选 ${chosen} 个${hidden}。文件尚未上传。`;
  }

  return h(
    "div",
    { class: "page" },
    pageHeader("导入", "上传、导入预览、增量同步和任务进度将在 P2 实现。"),
    section(
      "上传本机目录",
      field("选择目录", picker),
      summary,
      fileList,
      toolbar(
        h("button", { type: "button", disabled: true }, "生成导入预览"),
        h("button", { type: "button", disabled: true }, "提交导入"),
      ),
      note("上传与导入预览尚未实现，因此按钮不可用；不会上传任何文件。"),
    ),
    section(
      "服务端授权目录",
      toolbar(h("button", { type: "button", disabled: true }, "列出授权目录")),
      note("服务端授权目录与同步尚未实现。浏览器只能选择本机文件，不能直接读取服务端路径。"),
    ),
    section("导入任务", note("导入任务尚未实现，没有任务进度可显示。")),
  );
}

export function selectDirectory(files: ArrayLike<File>): UploadSelection {
  return {
    files: Array.from(files, (file) => ({
      relativePath: file.webkitRelativePath || file.name,
      size: file.size,
      selected: true,
    })),
  };
}

export function toggleFile(selection: UploadSelection, path: string, selected: boolean): void {
  const file = selection.files.find((item) => item.relativePath === path);
  if (file) file.selected = selected;
}
