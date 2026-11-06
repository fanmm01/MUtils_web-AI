/**
 * 导入: import sources, browser directory upload, server-side authorized roots,
 * import preview → confirm → job, and publishing the resulting version. The
 * server scans, verifies hashes and decides what is added or deleted; this page
 * only shows its answers.
 */

import { QAError, type ImportPreview, type KnowledgeBase, type ManifestFile, type Selection as SourceSelection, type Source, type SourceManifest } from "@qa/client";
import { dataTable, facts, idText, listOf, row } from "../components/data.js";
import { watchJob } from "../components/jobs.js";
import { kbContext, type KBContext } from "../components/kb-context.js";
import { publishPanel } from "../components/publish.js";
import {
  attempt,
  button,
  createStatusArea,
  describeError,
  field,
  h,
  isConflict,
  isNotFound,
  note,
  pageIntro,
  section,
  toolbar,
  type StatusArea,
} from "../components/ui.js";
import type { PageContext } from "../state.js";

/** Files the user picked in this browser, relative to the chosen folder. */
export interface UploadSelection {
  files: Array<{ relativePath: string; size: number; selected: boolean; file: File }>;
}


export function renderImportPage(ctx: PageContext): HTMLElement {
  const kbc = kbContext(ctx);
  const body = h("div", {});
  void kbc.ready.then((kb) => {
    if (kb && !ctx.signal.aborted) body.replaceChildren(...importSections(ctx, kbc, kb));
  });
  return h(
    "div",
    { class: "page" },
    pageIntro("导入", "为所选知识库登记来源，上传本机目录或同步服务端授权目录，先预览变化，确认后由后台任务构建新版本。"),
    kbc.element,
    body,
  );
}
function importSections(ctx: PageContext, kbc: KBContext, kb: KnowledgeBase): HTMLElement[] {
  const jobs = jobsArea(ctx, kbc);
  const sourceSlot = h("div", {});
  const showSource = (source: Source | null): void => {
    sourceSlot.replaceChildren(...(source ? sourceSections(ctx, kb, source, jobs.add) : []));
  };
  return [sourcesPanel(ctx, kb, showSource), sourceSlot, jobs.element];
}

function sourcesPanel(ctx: PageContext, kb: KnowledgeBase, onSelect: (source: Source | null) => void): HTMLElement {
  const status = createStatusArea();
  const table = dataTable("导入来源", ["名称", "类型", "来源 ID", "操作"]);
  let active: string | null = null;

  const render = (sources: Source[]): void => {
    table.setRows(
      sources.map((source) => {
        const isActive = source.source_id === active;
        const action = isActive
          ? h("span", { class: "badge" }, "使用中")
          : button("使用此来源", () => select(source, sources));
        if (!isActive) action.setAttribute("aria-label", `使用来源 ${source.display_name}`);
        return row([source.display_name, kindLabel(source), idText(source.source_id), action], {
          "data-source-id": source.source_id,
        });
      }),
      "还没有导入来源。请先在下方新建一个上传来源或服务端目录来源。",
    );
  };
  const select = (source: Source, sources: Source[]): void => {
    active = source.source_id;
    render(sources);
    onSelect(source);
  };
  const load = async (prefer?: string): Promise<void> => {
    table.setMessage("正在加载…");
    const outcome = await attempt(status, "加载导入来源", () => ctx.client.listSources(kb.kb_id, { signal: ctx.signal }));
    if (!outcome.ok) {
      table.setMessage(`加载失败：${describeError(outcome.error).title}`, "error");
      return;
    }
    const sources = outcome.value;
    const next = sources.find((item) => item.source_id === (prefer ?? active)) ?? sources[0];
    if (next) select(next, sources);
    else {
      render(sources);
      onSelect(null);
    }
  };
  const createStatus = createStatusArea();
  const uploadName = h("input", { name: "display_name", required: true, maxlength: "200", placeholder: "如：产品手册目录" });
  const uploadForm = h(
    "form",
    { class: "form", "aria-label": "新建上传来源" },
    field("来源名称", uploadName),
    h("button", { type: "submit" }, "新建上传来源"),
  );
  uploadForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void createSource(ctx, kb, { kind: "upload", display_name: uploadName.value.trim() }, createStatus).then((source) => {
      if (source) void load(source.source_id);
    });
  });

  const rootSlot = h("div", {});
  void attempt(createStatus, "读取服务端授权目录", () => ctx.client.listSourceRoots({ signal: ctx.signal })).then((outcome) => {
    if (!outcome.ok || ctx.signal.aborted) return;
    if (outcome.value.length === 0) {
      rootSlot.replaceChildren(note("服务端没有配置授权目录（QA_SOURCE_ROOTS），只能上传本机目录。"));
      return;
    }
    const root = h("select", { name: "root_id" }, ...outcome.value.map((id) => h("option", { value: id }, id)));
    const name = h("input", { name: "root_display_name", required: true, maxlength: "200" });
    const form = h(
      "form",
      { class: "form", "aria-label": "新建服务端目录来源" },
      field("授权目录", root),
      field("来源名称", name),
      h("button", { type: "submit" }, "新建服务端目录来源"),
      note("浏览器只能看到服务端公布的目录 ID，不能读取服务端路径。"),
    );
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const body = { kind: "local_root" as const, display_name: name.value.trim(), root_id: root.value };
      void createSource(ctx, kb, body, createStatus).then((source) => {
        if (source) void load(source.source_id);
      });
    });
    rootSlot.replaceChildren(form);
  });

  void load();
  return section("导入来源", status.element, table.element, h("div", { class: "split" }, uploadForm, rootSlot), createStatus.element);
}
/**
 * The frozen contract takes a complete `Source` on create, including the id and
 * the revision token; the client picks a random id and the first revision.
 */
async function createSource(
  ctx: PageContext,
  kb: KnowledgeBase,
  spec: { kind: Source["kind"]; display_name: string; root_id?: string },
  status: StatusArea,
): Promise<Source | null> {
  const body: Source = { source_id: newId("src"), kb_id: kb.kb_id, revision: "r1", ...spec };
  const outcome = await attempt(status, "新建导入来源", () => ctx.client.createSource(kb.kb_id, body, { signal: ctx.signal }));
  if (!outcome.ok) return null;
  status.ok(`已新建来源“${outcome.value.display_name}”。`);
  return outcome.value;
}

function newId(prefix: string): string {
  const bytes = crypto.getRandomValues(new Uint8Array(12));
  return `${prefix}_${Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}

function kindLabel(source: Source): string {
  return source.kind === "upload" ? "上传目录" : `服务端目录（${source.root_id ?? "未指定"}）`;
}

function sourceSections(ctx: PageContext, kb: KnowledgeBase, source: Source, addJob: AddJob): HTMLElement[] {
  const preview = previewPanel(ctx, kb, source, addJob);
  const intake = source.kind === "upload" ? uploadPanel(ctx, source, preview.uploaded) : localRootPanel(ctx, source, addJob);
  return [intake, preview.element];
}

function uploadPanel(ctx: PageContext, source: Source, onUploaded: (manifest: SourceManifest) => void): HTMLElement {
  let selection: UploadSelection = { files: [] };
  const status = createStatusArea();
  const summary = h("p", { class: "note", role: "status" }, "尚未选择目录。");
  const fileList = h("ul", { class: "file-list" });
  const picker = h("input", { type: "file", name: "directory", multiple: true, webkitdirectory: true });
  const upload = button("上传所选文件", () => void run());
  upload.disabled = true;

  const renderSummary = (): void => {
    const total = selection.files.length;
    const chosen = selection.files.filter((file) => file.selected).length;
    summary.textContent = total === 0 ? "尚未选择目录。" : `已在浏览器中选择 ${total} 个文件，勾选 ${chosen} 个。尚未上传。`;
    upload.disabled = chosen === 0;
  };
  const renderFiles = (): void => {
    fileList.replaceChildren();
    // Every file is listed: a file that is selected must also be visible and uncheckable.
    for (const file of selection.files) {
      const box = h("input", { type: "checkbox" });
      box.checked = file.selected;
      box.addEventListener("change", () => {
        toggleFile(selection, file.relativePath, box.checked);
        renderSummary();
      });
      fileList.append(h("li", {}, h("label", {}, box, ` ${file.relativePath}（${formatSize(file.size)}）`)));
    }
    renderSummary();
  };
  picker.addEventListener("change", () => {
    selection = selectDirectory(picker.files ?? []);
    status.clear();
    renderFiles();
  });

  const run = async (): Promise<void> => {
    upload.disabled = true;
    picker.disabled = true;
    try {
      const manifest = await uploadSelection(ctx, source, selection, (text) => status.pending(text));
      reportManifest(manifest, status);
      onUploaded(manifest);
    } catch (error) {
      status.fail("上传", describeError(error));
    } finally {
      picker.disabled = false;
      renderSummary();
    }
  };

  return section(
    `上传本机目录 · ${source.display_name}`,
    field("选择目录", picker),
    summary,
    fileList,
    toolbar(upload),
    status.element,
    note("浏览器会计算每个文件的 SHA-256，只上传勾选的文件；服务端逐字节核对。关闭页面后不会继续监听本机目录，下次同步需重新选择并上传。"),
  );
}

/**
 * Hash, declare, send and complete one upload batch. Unchecked files make the
 * batch partial (explicit `relative_paths`), so the server never treats the
 * missing files as deleted.
 */
export async function uploadSelection(
  ctx: PageContext,
  source: Source,
  selection: UploadSelection,
  progress: (text: string) => void,
): Promise<SourceManifest> {
  const chosen = selection.files.filter((file) => file.selected);
  if (chosen.length === 0) throw new Error("没有勾选任何文件。");
  if (!globalThis.crypto?.subtle) {
    throw new Error("浏览器未提供 Web Crypto（只在 HTTPS 等安全上下文中可用），无法计算文件摘要。");
  }
  const files: ManifestFile[] = [];
  for (const [index, item] of chosen.entries()) {
    progress(`正在计算摘要：${index + 1}/${chosen.length} ${item.relativePath}`);
    const digest = await crypto.subtle.digest("SHA-256", await item.file.arrayBuffer());
    files.push({ relative_path: item.relativePath, digest: toHex(digest), size: item.size });
  }
  const partial = chosen.length < selection.files.length;
  progress("正在登记上传批次…");
  const batch = await ctx.client.beginUpload(
    { source_id: source.source_id, selection: partial ? { relative_paths: files.map((file) => file.relative_path) } : {}, files },
    { signal: ctx.signal },
  );
  for (const [index, item] of chosen.entries()) {
    progress(`正在上传：${index + 1}/${chosen.length} ${item.relativePath}`);
    await ctx.client.putUploadFile(batch.batch_id, item.relativePath, item.file, { signal: ctx.signal });
  }
  progress("正在等待服务端核验上传结果…");
  return ctx.client.completeUpload(batch.batch_id, { signal: ctx.signal });
}

/** Report the server's verdict on the batch; true when it can be previewed. */
function reportManifest(manifest: SourceManifest, status: StatusArea): boolean {
  const count = manifest.files?.length ?? 0;
  if (manifest.scan_status !== "succeeded") {
    status.fail("上传核验", {
      title: "未通过",
      message: "服务端核验发现有声明的文件没有收到或内容不符，本批次不能用于导入。请重新选择目录后上传。",
      details: [],
      notImplemented: false,
    });
    return false;
  }
  const scope =
    manifest.scan_scope === "partial"
      ? "这是部分上传：未勾选的文件不会因此被视为已删除。"
      : "这是完整上传：镜像同步可以据此删除来源中已不存在的文件。";
  status.ok(`服务端已核验 ${count} 个文件。${scope}下一步：生成导入预览。`);
  return true;
}

/** Paths relative to the chosen folder, like the CLI's `collect_upload`. */
export function selectDirectory(files: ArrayLike<File>): UploadSelection {
  const list = Array.from(files, (file) => ({ file, path: (file.webkitRelativePath || file.name).replaceAll("\\", "/") }));
  const roots = new Set(list.map((item) => (item.path.includes("/") ? item.path.split("/", 1)[0] : "")));
  const [root] = [...roots];
  const strip = roots.size === 1 && root ? `${root}/` : "";
  return {
    files: list
      .map(({ file, path }) => ({
        relativePath: strip && path.startsWith(strip) ? path.slice(strip.length) : path,
        size: file.size,
        selected: true,
        file,
      }))
      .sort((a, b) => (a.relativePath < b.relativePath ? -1 : a.relativePath > b.relativePath ? 1 : 0)),
  };
}

export function toggleFile(selection: UploadSelection, path: string, selected: boolean): void {
  const file = selection.files.find((item) => item.relativePath === path);
  if (file) file.selected = selected;
}
function localRootPanel(ctx: PageContext, source: Source, addJob: AddJob): HTMLElement {
  const status = createStatusArea();
  const sync = button("立即同步（合并）", () => void run());
  const run = async (): Promise<void> => {
    sync.disabled = true;
    const outcome = await attempt(status, "同步来源", () => syncSource(ctx, source.source_id));
    sync.disabled = false;
    if (!outcome.ok) return;
    if (!outcome.value.job_id) {
      status.done("服务端已受理同步，但没有返回任务 ID，无法跟踪进度。");
      return;
    }
    status.done("已提交同步任务，进度见下方“导入任务”。");
    addJob(outcome.value.job_id, "同步任务");
  };
  return section(
    `服务端目录 · ${source.display_name}`,
    facts([["授权目录 ID", idText(source.root_id ?? null)]]),
    note("服务端扫描它自己的授权目录。“立即同步”使用合并模式，不删除文档；需要按来源删除文档时，请在下方用镜像模式预览并确认。"),
    toolbar(sync),
    status.element,
  );
}

export function syncSource(ctx: PageContext, sourceId: string) {
  return ctx.client.syncSource(sourceId, {}, { signal: ctx.signal });
}

type ImportMode = "merge" | "mirror";

export function previewImport(ctx: PageContext, kb: KnowledgeBase, source: Source, mode: ImportMode, selection: SourceSelection) {
  return ctx.client.previewImport(
    kb.kb_id,
    { kb_id: kb.kb_id, source_id: source.source_id, mode, selection },
    { signal: ctx.signal },
  );
}

export function submitImport(
  ctx: PageContext,
  kb: KnowledgeBase,
  source: Source,
  preview: ImportPreview,
  mode: ImportMode,
  selection: SourceSelection,
) {
  return ctx.client.importDocuments(
    kb.kb_id,
    { kb_id: kb.kb_id, source_id: source.source_id, mode, selection, expected_preview_hash: preview.preview_hash },
    { signal: ctx.signal },
  );
}

function previewPanel(
  ctx: PageContext,
  kb: KnowledgeBase,
  source: Source,
  addJob: AddJob,
): { element: HTMLElement; uploaded: (manifest: SourceManifest) => void } {
  const status = createStatusArea();
  // The server compares the request's selection with the batch's: send the one it was uploaded
  // with. Before any upload on this page, a full scan (empty selection) is assumed.
  let selection: SourceSelection = {};
  let partial = false;
  const result = h("div", {});
  const modeSelect = h(
    "select",
    { name: "mode" },
    h("option", { value: "merge" }, "合并：新增和修改，不删除"),
    h("option", { value: "mirror" }, "镜像：与来源一致，删除来源中已不存在的文档"),
  );
  const generate = button("生成导入预览", () => void run());
  modeSelect.addEventListener("change", () => {
    result.replaceChildren();
    status.done("导入模式已更改，请重新生成预览。");
  });
  const run = async (): Promise<void> => {
    // A job card's retry can outlive this panel when another source is chosen.
    if (!status.element.isConnected) return;
    const mode = modeSelect.value as ImportMode;
    result.replaceChildren();
    const sent = selection;
    const outcome = await attempt(status, "生成导入预览", () => previewImport(ctx, kb, source, mode, sent));
    if (!outcome.ok) {
      if (isConflict(outcome.error) && source.kind === "upload") {
        status.element.append(h("p", {}, "这个上传来源还没有完成的上传批次，请先上传目录。"));
      } else if (isSelectionMismatch(outcome.error)) {
        status.element.append(h("p", {}, "服务端记录的最近一次上传批次是按另一组勾选上传的（例如在刷新页面之前）。请重新选择目录并上传，再生成预览。"));
      }
      return;
    }
    result.replaceChildren(previewView(ctx, kb, source, outcome.value, mode, sent, partial, run, addJob));
  };
  const element = section(
    "导入预览与确认",
    field("导入模式", modeSelect),
    toolbar(generate),
    status.element,
    result,
    note("预览只读取服务端已核验的文件清单，不改动知识库；确认时服务端会再次核对文件与预览摘要。"),
  );
  const uploaded = (manifest: SourceManifest): void => {
    // The server keeps the latest batch even when its check failed; follow it either way.
    selection = manifest.selection ?? {};
    partial = manifest.scan_scope === "partial";
    // A new upload makes any earlier preview stale.
    result.replaceChildren();
    if (manifest.scan_status === "succeeded") status.done("上传已核验，可以生成导入预览。");
    else status.clear();
  };
  return { element, uploaded };
}

function previewView(
  ctx: PageContext,
  kb: KnowledgeBase,
  source: Source,
  preview: ImportPreview,
  mode: ImportMode,
  selection: SourceSelection,
  partial: boolean,
  regenerate: () => Promise<void>,
  addJob: AddJob,
): HTMLElement {
  const added = preview.added ?? [];
  const modified = preview.modified ?? [];
  const removed = preview.removed ?? [];
  const conflicts = preview.conflicts ?? [];
  const status = createStatusArea();
  const confirm = h("button", { type: "button" }, "确认导入");
  const deletionBox = h("input", { type: "checkbox", name: "confirm_removal" });
  let submitted = false;
  const needsDeletionConsent = mode === "mirror" && removed.length > 0;
  const update = (): void => {
    confirm.disabled = submitted || conflicts.length > 0 || (needsDeletionConsent && !deletionBox.checked);
  };
  deletionBox.addEventListener("change", update);
  update();

  const unchanged = added.length + modified.length + removed.length === 0;
  const element = h(
    "div",
    { class: "preview", "aria-label": "导入预览结果" },
    facts([
      ["新增", String(added.length)],
      ["修改", String(modified.length)],
      [mode === "mirror" ? "将删除" : "来源中已不存在", String(removed.length)],
      ["冲突", String(conflicts.length)],
      ["预览 ID", idText(preview.preview_id)],
    ]),
    group("新增的文件", added, "info"),
    group("修改的文件", modified, "info"),
    group(mode === "mirror" ? "将从知识库删除的文件" : "来源中已不存在的文件（合并模式不删除）", removed, mode === "mirror" ? "danger" : "info"),
    group("冲突", conflicts, "danger"),
    unchanged && note("与该来源上次成功导入的清单相比没有变化。"),
    mode === "mirror" && partial && note("这是部分上传：镜像模式只比较本次上传的文件，未勾选的文件不会因此被删除。"),
    conflicts.length > 0 && note("存在冲突时不能提交；请处理冲突后重新生成预览。"),
    needsDeletionConsent &&
      h("label", { class: "consent" }, deletionBox, ` 我已核对上面 ${removed.length} 个将被删除的文件，确认按来源删除它们`),
    toolbar(confirm),
    status.element,
  );
  confirm.addEventListener("click", () => {
    submitted = true;
    update();
    void attempt(status, "确认导入", () => submitImport(ctx, kb, source, preview, mode, selection)).then((outcome) => {
      if (!outcome.ok) {
        if (isConflict(outcome.error)) {
          status.element.append(h("p", {}, "预览之后来源文件、勾选范围、导入模式或上次导入的基线发生了变化，这份预览已失效。请重新生成预览。"));
        } else if (isNotFound(outcome.error)) {
          status.element.append(h("p", {}, "服务端找不到这份预览，请重新生成预览。"));
        } else {
          submitted = false;
          update();
        }
        return;
      }
      if (!outcome.value.job_id) {
        status.done("服务端已受理导入，但没有返回任务 ID，无法跟踪进度。");
        return;
      }
      status.done("已提交导入任务，进度见下方“导入任务”。");
      addJob(outcome.value.job_id, "导入任务", { label: "重新生成预览", run: () => void regenerate() });
    });
  });
  return element;
}

function group(title: string, items: string[], tone: "info" | "danger"): HTMLElement | null {
  if (items.length === 0) return null;
  const box = h("details", { class: tone === "danger" ? "group danger" : "group" }, h("summary", {}, `${title}（${items.length}）`), listOf(items, ""));
  box.open = items.length <= 20 || tone === "danger";
  return box;
}

type AddJob = (jobId: string, title: string, retry?: { label: string; run: () => void }) => void;

function jobsArea(ctx: PageContext, kbc: KBContext): { element: HTMLElement; add: AddJob } {
  const list = h("div", { class: "job-list" });
  const empty = note("本页提交的导入或同步任务会显示在这里。");
  const element = section("导入任务", empty, list);
  const add: AddJob = (jobId, title, retry) => {
    empty.remove();
    const publishSlot = h("div", {});
    const card = watchJob(ctx.client, jobId, {
      title,
      signal: ctx.signal,
      pollMs: ctx.jobPollMs,
      retry,
      onTerminal: (job) => {
        if (job.state === "succeeded") publishSlot.replaceChildren(publishPanel(ctx, kbc, job.result_version_id ?? null));
      },
    });
    list.prepend(h("div", { class: "job-entry" }, card.element, publishSlot));
  };
  return { element, add };
}
/** 422 from preview: the request's selection is not the one the latest batch was uploaded with. */
function isSelectionMismatch(error: unknown): boolean {
  return error instanceof QAError && error.status === 422 && error.details.some((item) => item.field === "selection");
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} 字节`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function toHex(buffer: ArrayBuffer): string {
  return Array.from(new Uint8Array(buffer), (byte) => byte.toString(16).padStart(2, "0")).join("");
}
