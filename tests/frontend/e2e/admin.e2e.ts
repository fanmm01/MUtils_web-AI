/**
 * Admin main flow in a real browser against the real qa-api + qa-worker
 * (playwright.config.ts starts both): create a knowledge base → upload a
 * directory → preview → confirm → job → publish → edit content (incl. a real
 * 409) → second import → diff → rollback. Nothing is faked.
 */

import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test, type Page } from "@playwright/test";

/** Collect browser errors and failed API responses; a 409 is allowed only where the test provokes it. */
function watchErrors(page: Page): { problems: string[]; allowConflict: (pattern: RegExp) => void } {
  const problems: string[] = [];
  const allowed: RegExp[] = [];
  page.on("pageerror", (error) => problems.push(`pageerror: ${error.message}`));
  page.on("console", (message) => {
    // Page requests that fail are reported below with their URL. This console line has
    // no URL and also fires for the browser's own /favicon.ico request (WebUI has no icon).
    if (message.type() === "error" && !message.text().startsWith("Failed to load resource")) {
      problems.push(`console: ${message.text()}`);
    }
  });
  page.on("response", (response) => {
    if (response.status() < 400) return;
    const url = new URL(response.url());
    const call = `${response.request().method()} ${url.pathname}`;
    if (response.status() === 409 && allowed.some((pattern) => pattern.test(call))) return;
    problems.push(`${response.status()} ${call}`);
  });
  return { problems, allowConflict: (pattern) => allowed.push(pattern) };
}

/** Click a page in the main navigation (pages also contain links such as “在版本页查看”). */
async function nav(page: Page, label: string): Promise<void> {
  await page.getByRole("navigation", { name: "主导航" }).getByRole("link", { name: label, exact: true }).click();
}

/** Confirm the rendered preview, wait for its new job card (listed first) and return the built version. */
async function confirmImport(page: Page): Promise<string> {
  const jobs = page.locator("article.job");
  const before = await jobs.count();
  await page.getByRole("button", { name: "确认导入" }).click();
  await expect(jobs).toHaveCount(before + 1);
  return resultVersion(page);
}

async function resultVersion(page: Page): Promise<string> {
  const card = page.locator("article.job").first();
  await expect(card).toHaveAttribute("data-state", "succeeded", { timeout: 30_000 });
  const id = await card.locator("dt", { hasText: "结果版本" }).locator("xpath=following-sibling::dd[1]").innerText();
  expect(id).toMatch(/^ver_/);
  return id.trim();
}

test("admin main flow against the real API", async ({ page }, testInfo) => {
  const errors = watchErrors(page);
  const corpus = join(testInfo.outputDir, "运维资料");
  rmSync(corpus, { recursive: true, force: true });
  mkdirSync(join(corpus, "faq"), { recursive: true });
  writeFileSync(join(corpus, "deploy.md"), "# 部署\n\n先运行 qa-migrate，再启动 qa-api 和 qa-worker。\n");
  writeFileSync(join(corpus, "faq", "upgrade.txt"), "问：怎么升级？\n答：导入新资料后发布新版本。\n");

  await page.goto("/");
  await expect(page.locator(".service-badge")).toContainText("服务：运行中");
  await expect(page.locator("main tbody")).toContainText("还没有知识库");
  const create = page.locator("form[aria-label=新建知识库]");
  await create.getByLabel("名称").fill("运维手册");
  await create.getByLabel("领域标签").fill("运维, 部署");
  await create.getByRole("button", { name: "创建" }).click();
  await expect(page.locator("main")).toContainText("已创建知识库");
  await expect(page.locator("main tbody tr[aria-current=true]")).toContainText("运维手册");

  await nav(page, "导入");
  await expect(page.locator("main")).toContainText("还没有导入来源");
  const sourceForm = page.locator("form[aria-label=新建上传来源]");
  await sourceForm.getByLabel("来源名称").fill("运维目录");
  await sourceForm.getByRole("button", { name: "新建上传来源" }).click();
  await expect(page.locator("main")).toContainText("上传本机目录 · 运维目录");

  await page.locator("input[name=directory]").setInputFiles(corpus);
  await expect(page.locator("main")).toContainText("已在浏览器中选择 2 个文件，勾选 2 个");
  await expect(page.locator(".file-list")).toContainText("faq/upgrade.txt");
  await page.getByRole("button", { name: "上传所选文件" }).click();
  await expect(page.locator("main")).toContainText("服务端已核验 2 个文件");

  await page.getByRole("button", { name: "生成导入预览" }).click();
  await expect(page.locator("[aria-label=导入预览结果]")).toContainText("新增2");
  const first = await confirmImport(page);
  await page.getByRole("button", { name: "发布此版本" }).click();
  await page.getByRole("button", { name: "确认发布" }).click();
  await expect(page.locator("main")).toContainText(`已发布：版本 ${first} 现在是活动版本`);
  // A changed source file → second import → a new version with one modified document.
  // (Imports run before any content edit: the import preview reports no conflicts yet, so
  // importing a changed source file over a manually edited document would replace the
  // edit instead of asking, which plan §3.3 requires.)
  writeFileSync(join(corpus, "deploy.md"), "# 部署\n\n第二版：先备份，再迁移和启动。\n");
  await page.locator("input[name=directory]").setInputFiles(corpus);
  await page.getByRole("button", { name: "上传所选文件" }).click();
  await expect(page.locator("main")).toContainText("服务端已核验 2 个文件");
  await page.getByRole("button", { name: "生成导入预览" }).click();
  await expect(page.locator("[aria-label=导入预览结果]")).toContainText("修改1");
  const second = await confirmImport(page);
  expect(second).not.toBe(first);
  await page.getByRole("button", { name: "发布此版本" }).click();
  await page.getByRole("button", { name: "确认发布" }).click();
  await expect(page.locator("main")).toContainText(`已发布：版本 ${second} 现在是活动版本`);

  // Versions: diff the two imports, then roll back to the first.
  await nav(page, "版本");
  await expect(page.locator("tr[data-version-id]")).toHaveCount(2);
  await expect(page.locator(`tr[data-version-id="${second}"]`)).toContainText("活动版本");
  await page.locator("select[name=left]").selectOption(first);
  await page.locator("select[name=right]").selectOption(second);
  await page.getByRole("button", { name: "比较" }).click();
  const diff = page.locator("[aria-label=版本差异结果]");
  await expect(diff).toContainText("修改文档1");
  await expect(diff).toContainText("新增文档0");
  await expect(diff).toContainText("移除文档0");
  await expect(diff).toContainText("deploy.md");
  await page.getByRole("button", { name: `回滚到此版本 ${first}` }).click();
  await page.getByRole("button", { name: "确认回滚" }).click();
  await expect(page.locator("main")).toContainText(`已回滚：版本 ${first} 现在是活动版本`);
  await expect(page.locator(`tr[data-version-id="${first}"]`)).toContainText("活动版本");

  // Content: rollback moved only the active pointer; edit, publish, and a real 409.
  await nav(page, "内容");
  await expect(page.locator("tr[data-document-id]")).toHaveCount(2);
  await page.getByRole("button", { name: "查看文档 deploy.md" }).click();
  const editor = page.locator("form[aria-label=编辑文档]");
  await expect(editor.locator("textarea[name=text]")).toHaveValue(/第二版/);
  await editor.locator("textarea[name=text]").fill("部署步骤：先迁移数据库，再启动服务。");
  await editor.getByRole("button", { name: "保存为新修订" }).click();
  await expect(editor).toContainText("已保存为新修订");
  // The server rebuilds the whole base into a ready version; the editor offers to publish it.
  await expect(editor).toContainText("新版本已构建");
  const edited = (await editor.locator("dt", { hasText: "结果版本" }).locator("xpath=following-sibling::dd[1]").innerText()).trim();
  expect(edited).toMatch(/^ver_/);
  await editor.getByRole("button", { name: "发布此版本" }).click();
  await editor.getByRole("button", { name: "确认发布" }).click();
  await expect(editor).toContainText(`已发布：版本 ${edited} 现在是活动版本`);
  await expect(editor.getByRole("button", { name: "保存为新修订" })).toBeEnabled();

  const documentId = (await page.locator("tr[data-document-id]", { hasText: "deploy.md" }).getAttribute("data-document-id")) ?? "";
  const current = await (await page.request.get(`/v1/documents/${documentId}`)).json();
  const kbId = current.document.kb_id as string;
  const other = await page.request.patch(`/v1/documents/${documentId}`, {
    data: { kb_id: kbId, title: "deploy.md", text: "另一处保存的正文", expected_revision_id: current.document.latest_revision_id },
  });
  expect(other.status()).toBe(200);
  const otherVersion = (await other.json()).version_id as string;
  expect(otherVersion).toMatch(/^ver_/);
  errors.allowConflict(/^PATCH \/v1\/documents\//);
  await editor.locator("textarea[name=text]").fill("我的修改");
  await editor.getByRole("button", { name: "保存为新修订" }).click();
  await expect(editor).toContainText("状态冲突");
  await expect(editor).toContainText("CONFLICT");
  await page.getByRole("button", { name: "重新加载" }).click();
  await expect(page.locator("form[aria-label=编辑文档] textarea[name=text]")).toHaveValue("另一处保存的正文");

  // Versions: two imports, the published edit, and the other client's unpublished edit.
  await nav(page, "版本");
  await expect(page.locator("tr[data-version-id]")).toHaveCount(4);
  await expect(page.locator(`tr[data-version-id="${edited}"]`)).toContainText("活动版本");
  await expect(page.locator(`tr[data-version-id="${otherVersion}"]`)).toContainText("就绪，未发布");
  await expect(page.locator(`tr[data-version-id="${first}"]`)).toContainText("曾发布");
  await expect(page.locator(`tr[data-version-id="${second}"]`)).toContainText("曾发布");
  const kb = await (await page.request.get(`/v1/kbs/${kbId}`)).json();
  expect(kb.active_version_id).toBe(edited);

  expect(errors.problems).toEqual([]);
});
