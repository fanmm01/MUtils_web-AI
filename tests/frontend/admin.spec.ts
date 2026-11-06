/**
 * P2-B admin acceptance against the in-memory fake of the management API
 * (fake-api.ts): the main flow 创建→上传→预览→确认→任务→内容→版本 plus loading,
 * empty, failure, 409, cancel and navigation states. The real SDK, pages and
 * job polling run unchanged; only fetch is replaced.
 */

import { afterEach, expect, test, vi } from "vitest";
import { dispose, mount, navigate } from "../../WebUI/src/main.js";
import { createFakeApi, type Call, type FakeApi } from "./fake-api.js";

vi.setConfig({ testTimeout: 20_000 });

/** Mount the admin UI on a fresh fake; `setup` seeds data and returns the starting hash. */
function mountAdmin(
  options: { pollMs?: number; setup?: (fake: FakeApi) => string } = {},
): { fake: FakeApi; root: HTMLElement } {
  const fake = createFakeApi();
  const hash = options.setup?.(fake);
  if (hash) history.replaceState(null, "", hash);
  const root = document.createElement("div");
  document.body.append(root);
  mount(root, { client: fake.client, jobPollMs: options.pollMs ?? 10 });
  return { fake, root };
}

afterEach(() => {
  dispose();
  document.body.replaceChildren();
  history.replaceState(null, "", "/");
});

function find<T extends Element>(scope: ParentNode, selector: string, text?: string): T {
  const match = [...scope.querySelectorAll<T>(selector)].find(
    (element) => text === undefined || element.textContent?.trim() === text,
  );
  if (!match) throw new Error(`no ${selector}${text === undefined ? "" : ` with text "${text}"`}`);
  return match;
}
const click = (scope: ParentNode, label: string): void => find<HTMLButtonElement>(scope, "button", label).click();
const textOf = (scope: ParentNode, selector = "main"): string => scope.querySelector(selector)?.textContent ?? "";
const waitText = (scope: ParentNode, text: string, selector = "main"): Promise<void> =>
  vi.waitFor(() => expect(textOf(scope, selector)).toContain(text), { timeout: 5_000 });
const callsTo = (fake: FakeApi, method: string, path: string | RegExp): Call[] =>
  fake.calls.filter((call) => call.method === method && (typeof path === "string" ? call.path === path : path.test(call.path)));

function fill(form: HTMLFormElement, values: Record<string, string>): void {
  for (const [name, value] of Object.entries(values)) {
    const control = form.querySelector<HTMLInputElement | HTMLTextAreaElement>(`[name="${name}"]`);
    if (!control) throw new Error(`form has no control ${name}`);
    control.value = value;
  }
}
/** Simulate the browser directory picker: files carry `<folder>/<path>` like webkitRelativePath. */
function pickDirectory(root: ParentNode, folder: string, entries: Record<string, string>): File[] {
  const picker = find<HTMLInputElement>(root, "input[name=directory]");
  const files = Object.entries(entries).map(([path, text]) => {
    const file = new File([text], path.split("/").pop() ?? path, { type: "text/plain" });
    Object.defineProperty(file, "webkitRelativePath", { value: `${folder}/${path}` });
    return file;
  });
  Object.defineProperty(picker, "files", { value: files, configurable: true });
  picker.dispatchEvent(new Event("change"));
  return files;
}

async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

/** Pick a folder, optionally uncheck files, upload, and wait for the server's verdict. */
async function upload(root: HTMLElement, fake: FakeApi, entries: Record<string, string>, uncheck: string[] = []): Promise<void> {
  pickDirectory(root, "docs", entries);
  for (const path of uncheck) {
    const box = [...root.querySelectorAll<HTMLLabelElement>(".file-list label")]
      .find((item) => item.textContent?.includes(` ${path}（`))
      ?.querySelector<HTMLInputElement>("input[type=checkbox]");
    if (!box) throw new Error(`no checkbox for ${path}`);
    box.click();
  }
  const before = callsTo(fake, "POST", /\/complete$/).length;
  click(root, "上传所选文件");
  await vi.waitFor(() => expect(callsTo(fake, "POST", /\/complete$/).length).toBe(before + 1), { timeout: 5_000 });
  await vi.waitFor(() => expect(find<HTMLButtonElement>(root, "button", "上传所选文件").disabled).toBe(false));
}

/** Generate a preview in `mode` and wait until it is rendered. */
async function preview(root: HTMLElement, fake: FakeApi, mode: "merge" | "mirror" = "merge"): Promise<HTMLElement> {
  const select = find<HTMLSelectElement>(root, "select[name=mode]");
  if (select.value !== mode) {
    select.value = mode;
    select.dispatchEvent(new Event("change"));
  }
  const before = callsTo(fake, "POST", /\/imports\/preview$/).length;
  click(root, "生成导入预览");
  await vi.waitFor(() => expect(callsTo(fake, "POST", /\/imports\/preview$/).length).toBe(before + 1));
  return vi.waitFor(() => find<HTMLElement>(root, "[aria-label=导入预览结果]"));
}

/** Confirm the rendered preview and return the new (first-listed) job card. */
async function confirmImport(root: HTMLElement): Promise<HTMLElement> {
  const before = root.querySelectorAll("article.job").length;
  click(root, "确认导入");
  await vi.waitFor(() => expect(root.querySelectorAll("article.job").length).toBe(before + 1));
  return find<HTMLElement>(root, "article.job");
}

function seedUploadSource(fake: FakeApi, kbId: string): string {
  const id = "src_upload_1";
  fake.state.sources.set(id, { source_id: id, kb_id: kbId, kind: "upload", display_name: "资料目录", revision: "r1" });
  return id;
}
test("testSelectAndImportDirectory", async () => {
  const { fake, root } = mountAdmin();
  await waitText(root, "还没有知识库");
  const create = find<HTMLFormElement>(root, "form[aria-label=新建知识库]");
  fill(create, { name: "产品手册", description: "产品说明", domain_tags: "产品, 安装", routing_examples: "怎么安装？\n如何升级？" });
  create.requestSubmit();
  await waitText(root, "已创建知识库");
  const [kb] = [...fake.state.kbs.values()];
  if (!kb) throw new Error("knowledge base was not created");
  expect(location.hash).toBe(`#/knowledge?kb=${kb.kb_id}`);
  expect(callsTo(fake, "POST", "/v1/kbs")[0]?.body).toEqual({
    name: "产品手册", description: "产品说明", domain_tags: ["产品", "安装"], routing_examples: ["怎么安装？", "如何升级？"],
  });
  await vi.waitFor(() => expect(textOf(root, `tr[data-kb-id="${kb.kb_id}"]`)).toContain("当前"));

  navigate("imports");
  await waitText(root, "还没有导入来源");
  expect(textOf(root, ".kb-bar")).toContain(kb.kb_id);
  expect(textOf(root)).toContain("服务端没有配置授权目录");
  const sourceForm = find<HTMLFormElement>(root, "form[aria-label=新建上传来源]");
  fill(sourceForm, { display_name: "产品目录" });
  sourceForm.requestSubmit();
  await waitText(root, "上传本机目录 · 产品目录");
  const [source] = [...fake.state.sources.values()];
  expect(source).toMatchObject({ kb_id: kb.kb_id, kind: "upload", display_name: "产品目录", revision: "r1" });

  const entries = { "guide.md": "# 安装\n\n先下载安装包。\n", "faq/install.txt": "问：怎么升级？答：重新安装。", "notes/2026.md": "发布说明" };
  pickDirectory(root, "产品手册", entries);
  expect(textOf(root)).toContain("已在浏览器中选择 3 个文件，勾选 3 个");
  // Paths are relative to the chosen folder, like the CLI upload.
  expect(textOf(root, ".file-list")).toContain("faq/install.txt");
  expect(textOf(root, ".file-list")).not.toContain("产品手册/");
  click(root, "上传所选文件");
  await waitText(root, "服务端已核验 3 个文件");
  expect(textOf(root)).toContain("这是完整上传");
  const begin = callsTo(fake, "POST", "/v1/uploads")[0]?.body as { selection: unknown; files: unknown[] };
  expect(begin.selection).toEqual({});
  expect(begin.files).toEqual(
    await Promise.all(
      Object.entries(entries).sort(([a], [b]) => (a < b ? -1 : 1)).map(async ([path, text]) => ({
        relative_path: path, digest: await sha256Hex(text), size: new TextEncoder().encode(text).length,
      })),
    ),
  );
  expect(callsTo(fake, "PUT", /\/files$/).map((call) => call.query.get("relative_path")).sort()).toEqual(Object.keys(entries).sort());

  const result = await preview(root, fake);
  expect(result.textContent).toContain("新增3");
  const card = await confirmImport(root);
  expect(card.dataset.state).toBe("queued");
  expect(card.textContent).toContain("qa-worker");
  expect(find<HTMLButtonElement>(root, "button", "确认导入").disabled).toBe(true);

  fake.runWorker();
  await vi.waitFor(() => expect(card.dataset.state).toBe("succeeded"));
  expect(card.textContent).toContain("服务端没有报告失败或跳过的文件");
  await waitText(root, "新版本已构建");
  const [version] = [...fake.state.versions.values()];
  if (!version) throw new Error("no version was built");
  click(root, "发布此版本");
  click(root, "确认发布");
  await waitText(root, `已发布：版本 ${version.version_id} 现在是活动版本`);
  expect(callsTo(fake, "POST", `/v1/versions/${version.version_id}/publish`)[0]?.body).toEqual({ expected_active_version_id: null });
  expect(fake.state.kbs.get(kb.kb_id)?.active_version_id).toBe(version.version_id);

  navigate("content");
  await vi.waitFor(() => expect(root.querySelectorAll("tr[data-document-id]")).toHaveLength(3));
  navigate("versions");
  await vi.waitFor(() => expect(textOf(root, `tr[data-version-id="${version.version_id}"]`)).toContain("活动版本"));
});
test("testEditAndPublishContent", async () => {
  let kbId = "";
  let docId = "";
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      kbId = fake.seedKB("运维").kb_id;
      docId = fake.seedDocument(kbId, "部署手册", "第一版正文", "src_x", "deploy.md").document_id;
      return `#/content?kb=${kbId}`;
    },
  });
  const docRow = await vi.waitFor(() => find<HTMLTableRowElement>(root, `tr[data-document-id="${docId}"]`));
  find<HTMLButtonElement>(docRow, "button").click();
  const editor = await vi.waitFor(() => find<HTMLFormElement>(root, "form[aria-label=编辑文档]"));
  expect(find<HTMLTextAreaElement>(editor, "textarea[name=text]").value).toBe("第一版正文");
  expect(textOf(root, ".editor")).toContain("deploy.md");
  const firstRevision = fake.state.documents.get(docId)?.doc.latest_revision_id;

  fill(editor, { text: "第二版正文" });
  editor.requestSubmit();
  await waitText(root, "已保存为新修订", ".editor");
  // The P2 server rebuilds the whole base into a ready version (receipt.version_id); nothing is live yet.
  await waitText(root, "新版本已构建", ".editor");
  const built = [...fake.state.versions.values()].at(-1);
  expect(built?.state).toBe("ready");
  expect(fake.state.kbs.get(kbId)?.active_version_id ?? null).toBeNull();
  expect(textOf(root, ".editor")).not.toContain("已生效");
  find<HTMLButtonElement>(editor, "button", "发布此版本").click();
  click(editor, "确认发布");
  await waitText(root, `已发布：版本 ${built?.version_id} 现在是活动版本`, ".editor");
  expect(fake.state.kbs.get(kbId)?.active_version_id).toBe(built?.version_id);
  expect(callsTo(fake, "POST", `/v1/versions/${built?.version_id}/publish`)[0]?.body).toEqual({ expected_active_version_id: null });
  const [firstPatch] = callsTo(fake, "PATCH", `/v1/documents/${docId}`);
  expect(firstPatch?.body).toMatchObject({ kb_id: kbId, text: "第二版正文", relative_path: "deploy.md", expected_revision_id: firstRevision });

  // The next save names the revision the previous save created.
  await vi.waitFor(() => expect(find<HTMLButtonElement>(editor, "button", "保存为新修订").disabled).toBe(false));
  const secondRevision = fake.state.documents.get(docId)?.doc.latest_revision_id;
  expect(secondRevision).not.toBe(firstRevision);
  fill(editor, { text: "第三版正文" });
  editor.requestSubmit();
  await vi.waitFor(() => expect(callsTo(fake, "PATCH", `/v1/documents/${docId}`)).toHaveLength(2));
  expect(callsTo(fake, "PATCH", `/v1/documents/${docId}`)[1]?.body).toMatchObject({ expected_revision_id: secondRevision });
  await vi.waitFor(() => expect(find<HTMLButtonElement>(editor, "button", "保存为新修订").disabled).toBe(false));

  // Someone else saves first: 409 with a reload that shows their text.
  const latest = fake.state.documents.get(docId)?.doc.latest_revision_id ?? null;
  await fake.client.updateDocument(docId, { kb_id: kbId, title: "部署手册", text: "另一处的修改", expected_revision_id: latest });
  fill(editor, { text: "我的修改" });
  editor.requestSubmit();
  await waitText(root, "状态冲突", ".editor");
  expect(textOf(root, ".editor")).toContain("CONFLICT");
  click(root, "重新加载");
  await vi.waitFor(() =>
    expect(find<HTMLTextAreaElement>(root, "form[aria-label=编辑文档] textarea[name=text]").value).toBe("另一处的修改"),
  );

  // QA pairs: create, edit, delete, each with the server's revision.
  const qaForm = find<HTMLFormElement>(root, "form[aria-label=新建问答对]");
  fill(qaForm, { question: "怎么回滚？", answer: "在版本页选择旧版本。" });
  qaForm.requestSubmit();
  await waitText(root, "已新建问答对");
  const qaRow = await vi.waitFor(() => find<HTMLTableRowElement>(root, "tr[data-qa-id]"));
  // The QA pair is also stored as a document; the document list leaves it out.
  click(root, "刷新文档");
  await vi.waitFor(() => expect(root.querySelectorAll("tr[data-document-id]")).toHaveLength(1));
  find<HTMLButtonElement>(qaRow, "button").click();
  const qaEditor = await vi.waitFor(() => find<HTMLFormElement>(root, "form[aria-label=编辑问答对]"));
  fill(qaEditor, { answer: "在版本页回滚到旧版本。" });
  qaEditor.requestSubmit();
  await waitText(root, "已保存问答对");
  await vi.waitFor(() => expect(find<HTMLButtonElement>(qaEditor, "button", "删除问答对").disabled).toBe(false));
  const [pair] = [...fake.state.qa.values()];
  expect(pair?.answer).toBe("在版本页回滚到旧版本。");
  click(qaEditor, "删除问答对");
  click(qaEditor, "确认删除");
  await waitText(root, "已删除问答对");
  const remove = callsTo(fake, "DELETE", /^\/v1\/qa-pairs\//)[0];
  expect(remove?.query.get("expected_revision_id")).toBe(pair?.revision_id);
});

test("testVersionRollback", async () => {
  let kbId = "";
  const ids: Record<string, string> = {};
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      kbId = fake.seedKB("产品").kb_id;
      const doc1 = fake.seedDocument(kbId, "安装指南", "v1");
      const doc2 = fake.seedDocument(kbId, "升级说明", "v1");
      ids.doc1 = doc1.document_id;
      ids.v1 = fake.seedVersion(kbId, "published", { [doc1.document_id]: "rev_a" }, true).version_id;
      ids.v2 = fake.seedVersion(kbId, "published", { [doc1.document_id]: "rev_b", [doc2.document_id]: "rev_c" }, true).version_id;
      ids.v3 = fake.seedVersion(kbId, "ready", { [doc2.document_id]: "rev_c" }).version_id;
      return `#/versions?kb=${kbId}`;
    },
  });
  await vi.waitFor(() => expect(root.querySelectorAll("tr[data-version-id]")).toHaveLength(3));
  // Newest first; the active version is marked; only valid actions are offered.
  expect([...root.querySelectorAll<HTMLElement>("tr[data-version-id]")].map((tr) => tr.dataset.versionId)).toEqual([ids.v3, ids.v2, ids.v1]);
  expect(textOf(root, `tr[data-version-id="${ids.v2}"]`)).toContain("活动版本");
  expect(textOf(root, `tr[data-version-id="${ids.v3}"]`)).toContain("就绪，未发布");

  find<HTMLButtonElement>(root, `button[aria-label="回滚到此版本 ${ids.v1}"]`).click();
  click(root, "确认回滚");
  await waitText(root, `已回滚：版本 ${ids.v1} 现在是活动版本`);
  expect(callsTo(fake, "POST", `/v1/kbs/${kbId}/rollback`)[0]?.body).toEqual({ target_version_id: ids.v1, expected_active_version_id: ids.v2 });
  await vi.waitFor(() => expect(textOf(root, `tr[data-version-id="${ids.v1}"]`)).toContain("活动版本"));

  // Another tab publishes v3 meanwhile: our publish of v3 is a 409 and the list refreshes.
  await fake.client.publishVersion(ids.v3 as string, { expected_active_version_id: ids.v1 });
  find<HTMLButtonElement>(root, `button[aria-label="回滚到此版本 ${ids.v2}"]`).click();
  click(root, "确认回滚");
  await waitText(root, "活动版本已被其他操作改变");
  expect(textOf(root)).toContain("CONFLICT");
  await vi.waitFor(() => expect(textOf(root, `tr[data-version-id="${ids.v3}"]`)).toContain("活动版本"));

  // Document-level diff with titles.
  const left = find<HTMLSelectElement>(root, "select[name=left]");
  const right = find<HTMLSelectElement>(root, "select[name=right]");
  left.value = ids.v1 as string;
  right.value = ids.v2 as string;
  click(root, "比较");
  const diff = await vi.waitFor(() => find<HTMLElement>(root, "[aria-label=版本差异结果]"));
  expect(diff.textContent).toContain("新增文档1");
  expect(diff.textContent).toContain("修改文档1");
  expect(diff.textContent).toContain("升级说明");
  expect(diff.textContent).toContain(`安装指南（${ids.doc1}）`);
});
test("loading, empty, failure, 409 and 422 states are shown as the server sent them", async () => {
  const fake = createFakeApi();
  const releaseList = fake.hold("GET", "/v1/kbs");
  const root = document.createElement("div");
  document.body.append(root);
  mount(root, { client: fake.client, jobPollMs: 10 });
  await waitText(root, "正在加载…", "tbody");
  releaseList();
  await waitText(root, "还没有知识库", "tbody");

  fake.failNext("GET", "/v1/kbs", 500, "INTERNAL_ERROR", "internal error");
  click(root, "刷新列表");
  await waitText(root, "加载失败：服务内部错误", "tbody");
  expect(textOf(root)).toMatch(/INTERNAL_ERROR · request_id: req-\d+/);

  const form = find<HTMLFormElement>(root, "form[aria-label=新建知识库]");
  fake.failNext("POST", "/v1/kbs", 422, "VALIDATION_FAILED", "request validation failed", [{ field: "name", reason: "String should have at most 200 characters" }]);
  fill(form, { name: "过长的名字" });
  form.requestSubmit();
  await waitText(root, "创建知识库：参数错误", "form[aria-label=新建知识库]");
  expect(textOf(root, "form[aria-label=新建知识库]")).toContain("name：String should have at most 200 characters");

  form.requestSubmit();
  await waitText(root, "已创建知识库");
  const [kb] = [...fake.state.kbs.values()];
  if (!kb) throw new Error("no knowledge base");
  const editor = await vi.waitFor(() => find<HTMLFormElement>(root, "form[aria-label=编辑知识库]"));
  await fake.client.updateKB(kb.kb_id, { name: "别处改的名字" }, kb.etag);
  fill(editor, { name: "我改的名字" });
  editor.requestSubmit();
  await waitText(root, "知识库已被其他操作修改", "form[aria-label=编辑知识库]");
  click(editor, "重新加载");
  await vi.waitFor(() =>
    expect(find<HTMLInputElement>(root, "form[aria-label=编辑知识库] input[name=name]").value).toBe("别处改的名字"),
  );
  const fresh = find<HTMLFormElement>(root, "form[aria-label=编辑知识库]");
  fill(fresh, { name: "我改的名字" });
  fresh.requestSubmit();
  await waitText(root, "已保存", "form[aria-label=编辑知识库]");
  expect(fake.state.kbs.get(kb.kb_id)?.name).toBe("我改的名字");

  click(fresh, "删除知识库");
  click(fresh, "确认删除");
  await waitText(root, "已删除知识库");
  expect(fake.state.kbs.size).toBe(0);
  expect(location.hash).toBe("#/knowledge");
});

test("deleting a knowledge base that still has content is refused and explained", async () => {
  let kbId = "";
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      kbId = fake.seedKB("仍有内容").kb_id;
      fake.seedDocument(kbId, "手册", "正文");
      return `#/knowledge?kb=${kbId}`;
    },
  });
  const editor = await vi.waitFor(() => find<HTMLFormElement>(root, "form[aria-label=编辑知识库]"));
  click(editor, "删除知识库");
  click(editor, "确认删除");
  await waitText(root, "删除知识库：状态冲突", "form[aria-label=编辑知识库]");
  expect(textOf(root, "form[aria-label=编辑知识库]")).toContain("documents still exist");
  expect(textOf(root, "form[aria-label=编辑知识库]")).toContain("只能删除空的、没有版本的知识库");
  expect(fake.state.kbs.has(kbId)).toBe(true);
  expect(location.hash).toBe(`#/knowledge?kb=${kbId}`);
});

test("job failure diagnostics, cancel and the cancel/complete race", async () => {
  let kbId = "";
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      kbId = fake.seedKB("资料").kb_id;
      seedUploadSource(fake, kbId);
      return `#/imports?kb=${kbId}`;
    },
  });
  await waitText(root, "上传本机目录 · 资料目录");

  // First import into an empty base with only corrupt content: nothing to index, the job
  // fails with the server's code and offers a retry. (Later imports carry earlier content.)
  await upload(root, fake, { "bad.pdf": "%CORRUPT%" });
  await preview(root, fake);
  const failed = await confirmImport(root);
  fake.runWorker();
  await vi.waitFor(() => expect(failed.dataset.state).toBe("failed"));
  expect(failed.textContent).toContain("IMPORT_FAILED");
  expect(failed.textContent).toContain("one or more source files failed to index");
  expect(find<HTMLButtonElement>(failed, "button", "重新生成预览")).toBeTruthy();

  // A bad file alongside a good one fails closed: no partial version is published.
  await upload(root, fake, { "good.md": "正常内容", "bad.pdf": "%CORRUPT% v2" });
  await preview(root, fake);
  const partial = await confirmImport(root);
  fake.runWorker();
  await vi.waitFor(() => expect(partial.dataset.state).toBe("failed"));
  expect(partial.querySelectorAll("tr[data-status=failed]")).toHaveLength(1);
  expect(partial.textContent).toContain("PARSE_FAILED");
  expect(fake.state.versions.size).toBe(0);

  // Cancel a queued job.
  await upload(root, fake, { "bad.pdf": "%CORRUPT% v3" });
  await preview(root, fake);
  const queued = await confirmImport(root);
  click(queued, "取消任务");
  await vi.waitFor(() => expect(queued.dataset.state).toBe("cancelled"));
  await vi.waitFor(() => expect(queued.querySelector(".job-log")?.textContent).toContain("已取消"));
  expect(fake.runWorker()).toEqual([]);
});

test("cancelling a job that already finished reports the race and refreshes", async () => {
  let kbId = "";
  const { fake, root } = mountAdmin({
    pollMs: 60_000,
    setup: (fake) => {
      kbId = fake.seedKB("资料").kb_id;
      seedUploadSource(fake, kbId);
      return `#/imports?kb=${kbId}`;
    },
  });
  await waitText(root, "上传本机目录 · 资料目录");
  await upload(root, fake, { "a.md": "内容" });
  await preview(root, fake);
  const card = await confirmImport(root);
  await vi.waitFor(() => expect(card.dataset.state).toBe("queued"));
  fake.runWorker();
  click(card, "取消任务");
  await vi.waitFor(() => expect(card.textContent).toContain("任务已经结束，无法取消"));
  expect(card.dataset.state).toBe("succeeded");
});
test("mirror deletion needs explicit consent; a partial upload never deletes; a stale preview is a 409", async () => {
  let kbId = "";
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      kbId = fake.seedKB("资料").kb_id;
      seedUploadSource(fake, kbId);
      return `#/imports?kb=${kbId}`;
    },
  });
  await waitText(root, "上传本机目录 · 资料目录");
  await upload(root, fake, { "a.md": "甲", "b.md": "乙" });
  await preview(root, fake);
  const first = await confirmImport(root);
  fake.runWorker();
  await vi.waitFor(() => expect(first.dataset.state).toBe("succeeded"));

  // Partial upload (b.md unchecked): the batch is partial, mirror removes nothing.
  await upload(root, fake, { "a.md": "甲二", "b.md": "乙" }, ["b.md"]);
  expect(textOf(root)).toContain("这是部分上传");
  expect(callsTo(fake, "POST", "/v1/uploads").at(-1)?.body).toMatchObject({ selection: { relative_paths: ["a.md"] } });
  let result = await preview(root, fake, "mirror");
  // The preview names the batch's own selection (the server rejects any other).
  expect(callsTo(fake, "POST", /\/imports\/preview$/).at(-1)?.body).toMatchObject({ selection: { relative_paths: ["a.md"] } });
  expect(result.textContent).toContain("将删除0");
  expect(result.querySelector("input[name=confirm_removal]")).toBeNull();

  // Complete upload without b.md: mirror lists the deletion and waits for consent.
  await upload(root, fake, { "a.md": "甲二" });
  expect(textOf(root)).toContain("这是完整上传");
  result = await preview(root, fake, "mirror");
  expect(result.textContent).toContain("将删除1");
  expect(result.textContent).toContain("将从知识库删除的文件（1）");
  const confirmButton = find<HTMLButtonElement>(result, "button", "确认导入");
  expect(confirmButton.disabled).toBe(true);
  find<HTMLInputElement>(result, "input[name=confirm_removal]").click();
  expect(confirmButton.disabled).toBe(false);

  // Another client uploads before we confirm: the server rejects the stale preview.
  const batch = await fake.client.beginUpload({
    source_id: "src_upload_1",
    files: [{ relative_path: "c.md", digest: await sha256Hex("丙"), size: new TextEncoder().encode("丙").length }],
  });
  await fake.client.putUploadFile(batch.batch_id, "c.md", new Blob(["丙"]));
  await fake.client.completeUpload(batch.batch_id);
  confirmButton.click();
  await waitText(root, "这份预览已失效", "[aria-label=导入预览结果]");
  expect(confirmButton.disabled).toBe(true);
});

test("a directory with more than 200 files lists every file; only checked files are uploaded", async () => {
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      const kbId = fake.seedKB("大目录").kb_id;
      seedUploadSource(fake, kbId);
      return `#/imports?kb=${kbId}`;
    },
  });
  await waitText(root, "上传本机目录 · 资料目录");
  const entries: Record<string, string> = {};
  for (let i = 0; i < 205; i += 1) entries[`f${String(i).padStart(3, "0")}.md`] = `第 ${i} 个文件`;
  pickDirectory(root, "docs", entries);
  // Every file is shown with its own checkbox; none is selected out of sight.
  expect(root.querySelectorAll(".file-list input[type=checkbox]")).toHaveLength(205);
  expect(textOf(root)).toContain("已在浏览器中选择 205 个文件，勾选 205 个");
  await upload(root, fake, entries, ["f204.md"]);
  const begin = callsTo(fake, "POST", "/v1/uploads").at(-1)?.body as { selection: { relative_paths?: string[] }; files: unknown[] };
  expect(begin.files).toHaveLength(204);
  expect(begin.selection.relative_paths).toHaveLength(204);
  expect(begin.selection.relative_paths).not.toContain("f204.md");
  const sent = callsTo(fake, "PUT", /\/files$/).map((call) => call.query.get("relative_path"));
  expect(sent).toHaveLength(204);
  expect(sent).not.toContain("f204.md");
  expect(textOf(root)).toContain("服务端已核验 204 个文件。这是部分上传");
});

test("a partial upload keeps its selection through preview and confirm; mirror stays ineligible", async () => {
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      const kbId = fake.seedKB("部分上传").kb_id;
      seedUploadSource(fake, kbId);
      return `#/imports?kb=${kbId}`;
    },
  });
  await waitText(root, "上传本机目录 · 资料目录");
  await upload(root, fake, { "a.md": "甲", "b.md": "乙" });
  await preview(root, fake);
  const first = await confirmImport(root);
  fake.runWorker();
  await vi.waitFor(() => expect(first.dataset.state).toBe("succeeded"));

  await upload(root, fake, { "a.md": "甲二", "b.md": "乙" }, ["b.md"]);
  const result = await preview(root, fake, "mirror");
  expect(result.textContent).toContain("将删除0");
  expect(result.textContent).toContain("部分上传");
  const card = await confirmImport(root);
  const [request] = callsTo(fake, "POST", /\/imports$/).slice(-1);
  expect(request?.body).toMatchObject({ mode: "mirror", selection: { relative_paths: ["a.md"] } });
  fake.runWorker();
  await vi.waitFor(() => expect(card.dataset.state).toBe("succeeded"));
  // b.md was outside the partial batch: it stays in the new version.
  const version = fake.state.versions.get(fake.state.jobs.get(card.dataset.jobId as string)?.job.result_version_id ?? "");
  const docB = [...fake.state.documents.values()].find((item) => item.path === "b.md");
  expect(Object.keys(version?.document_revisions ?? {})).toContain(docB?.doc.document_id);
});

test("previewing a partial batch uploaded earlier (e.g. before a reload) asks for a new upload", async () => {
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      const kbId = fake.seedKB("刷新后").kb_id;
      const sourceId = seedUploadSource(fake, kbId);
      fake.state.uploads.set(sourceId, {
        source_id: sourceId,
        files: [{ relative_path: "a.md", digest: "d", size: 1 }],
        selection: { relative_paths: ["a.md"] },
        scan_scope: "partial",
        scan_status: "succeeded",
        complete: false,
        scanned_at: "2026-11-06T00:00:00Z",
      });
      return `#/imports?kb=${kbId}`;
    },
  });
  await waitText(root, "上传本机目录 · 资料目录");
  click(root, "生成导入预览");
  await waitText(root, "生成导入预览：参数错误");
  expect(textOf(root)).toContain("请重新选择目录并上传");
  expect(root.querySelector("[aria-label=导入预览结果]")).toBeNull();
  expect(fake.calls.some((call) => call.method === "POST" && /\/imports$/.test(call.path))).toBe(false);
});

test("server-side authorized root: create a source and sync it in merge mode", async () => {
  let kbId = "";
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      kbId = fake.seedKB("服务端资料").kb_id;
      fake.state.roots = ["docs-root"];
      return `#/imports?kb=${kbId}`;
    },
  });
  const form = await vi.waitFor(() => find<HTMLFormElement>(root, "form[aria-label=新建服务端目录来源]"));
  expect(find<HTMLSelectElement>(form, "select[name=root_id]").value).toBe("docs-root");
  fill(form, { root_display_name: "共享目录" });
  form.requestSubmit();
  await waitText(root, "服务端目录 · 共享目录");
  const [source] = [...fake.state.sources.values()];
  expect(source).toMatchObject({ kind: "local_root", root_id: "docs-root", kb_id: kbId });
  fake.state.rootFiles.set(source?.source_id as string, [{ relative_path: "x.md", digest: "d1", size: 1 }]);
  click(root, "立即同步（合并）");
  const card = await vi.waitFor(() => find<HTMLElement>(root, "article.job"));
  expect(callsTo(fake, "POST", `/v1/sources/${source?.source_id}/sync`)[0]?.body).toEqual({});
  fake.runWorker();
  await vi.waitFor(() => expect(card.dataset.state).toBe("succeeded"));
  await waitText(root, "新版本已构建");
});

test("issue list shows the server's 501 and real issues; actions stay disabled until P4", async () => {
  const { fake, root } = mountAdmin({ setup: () => "#/issues" });
  await waitText(root, "加载失败", "tbody");
  expect(textOf(root)).toContain("FEATURE_NOT_IMPLEMENTED");
  expect(root.querySelector<HTMLFieldSetElement>("main fieldset")?.disabled).toBe(true);

  fake.state.issues = [
    { issue_id: "iss_1", answer_id: "ans_1", question: "怎么导出？", status: "open", revision: 1, created_at: "2026-11-06T00:00:00Z" },
    { issue_id: "iss_2", answer_id: "ans_2", question: "支持离线吗？", status: "resolved", revision: 2, created_at: "2026-11-06T00:01:00Z" },
  ];
  const filter = find<HTMLSelectElement>(root, "select[name=status]");
  filter.value = "open";
  click(root, "查询");
  await vi.waitFor(() => expect(root.querySelectorAll("tr[data-issue-id]")).toHaveLength(1));
  expect(callsTo(fake, "GET", "/v1/issues").at(-1)?.query.get("status")).toBe("open");
  click(root, "查看");
  await waitText(root, "iss_1");
});

test("leaving a page aborts its in-flight requests", async () => {
  let kbId = "";
  const { fake, root } = mountAdmin({
    setup: (fake) => {
      kbId = fake.seedKB("产品").kb_id;
      return `#/content?kb=${kbId}`;
    },
  });
  const release = fake.hold("GET", `/v1/kbs/${kbId}/documents`);
  await vi.waitFor(() => expect(callsTo(fake, "GET", `/v1/kbs/${kbId}/documents`)).toHaveLength(1));
  const pending = callsTo(fake, "GET", `/v1/kbs/${kbId}/documents`)[0];
  navigate("versions");
  expect(pending?.signal?.aborted).toBe(true);
  release();
  await waitText(root, "还没有版本");
  expect(root.querySelector("tr[data-document-id]")).toBeNull();
});
