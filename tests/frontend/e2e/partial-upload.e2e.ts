import { randomUUID } from "node:crypto";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test, type Page } from "@playwright/test";

async function importAndPublish(page: Page): Promise<string> {
  await page.getByRole("button", { name: "生成导入预览" }).click();
  await expect(page.locator("[aria-label=导入预览结果]")).toBeVisible();
  const jobs = page.locator("article.job");
  const before = await jobs.count();
  await page.getByRole("button", { name: "确认导入" }).click();
  await expect(jobs).toHaveCount(before + 1);
  const card = jobs.first();
  await expect(card).toHaveAttribute("data-state", "succeeded", { timeout: 30_000 });
  const versionId = (
    await card.locator("dt", { hasText: "结果版本" }).locator("xpath=following-sibling::dd[1]").innerText()
  ).trim();
  expect(versionId).toMatch(/^ver_/);
  await page.getByRole("button", { name: "发布此版本" }).first().click();
  await page.getByRole("button", { name: "确认发布" }).click();
  await expect(page.locator("main")).toContainText(`已发布：版本 ${versionId} 现在是活动版本`);
  return versionId;
}

test("partial browser upload keeps unselected source content in the published snapshot", async ({ page }, testInfo) => {
  const corpus = join(testInfo.outputDir, "partial-corpus");
  mkdirSync(corpus, { recursive: true });
  writeFileSync(join(corpus, "a.md"), "# A\n\nfirst content\n");
  writeFileSync(join(corpus, "b.md"), "# B\n\nkeep this content\n");

  const created = await page.request.post("/v1/kbs", { data: { name: "partial-upload-e2e" } });
  expect(created.status()).toBe(201);
  const kbId = (await created.json()).kb_id as string;
  const sourceId = `src_${randomUUID().replaceAll("-", "")}`;
  const source = await page.request.post(`/v1/kbs/${kbId}/sources`, {
    data: { source_id: sourceId, kb_id: kbId, kind: "upload", display_name: "folder", revision: "r1" },
  });
  expect(source.status()).toBe(201);

  const importRequests: Array<{ path: string; selection: unknown }> = [];
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (request.method() !== "POST" || !/\/imports(?:\/preview)?$/.test(path)) return;
    importRequests.push({ path, selection: request.postDataJSON()?.selection });
  });
  await page.goto(`/#/imports?kb=${encodeURIComponent(kbId)}`);
  await expect(page.locator("main")).toContainText("上传本机目录 · folder");
  await page.locator("input[name=directory]").setInputFiles(corpus);
  await expect(page.locator(".file-list input[type=checkbox]")).toHaveCount(2);
  await page.getByRole("button", { name: "上传所选文件" }).click();
  await expect(page.locator("main")).toContainText("服务端已核验 2 个文件");
  const first = await importAndPublish(page);
  const firstVersion = await (await page.request.get(`/v1/versions/${first}`)).json();
  expect(Object.keys(firstVersion.document_revisions)).toHaveLength(2);

  writeFileSync(join(corpus, "a.md"), "# A\n\nupdated content\n");
  await page.locator("input[name=directory]").setInputFiles(corpus);
  const b = page.locator(".file-list label", { hasText: " b.md（" });
  await b.locator("input[type=checkbox]").uncheck();
  await expect(page.locator("main")).toContainText("勾选 1 个");
  await page.getByRole("button", { name: "上传所选文件" }).click();
  await expect(page.locator("main")).toContainText("这是部分上传");
  const second = await importAndPublish(page);
  expect(second).not.toBe(first);

  expect(importRequests.slice(-2)).toEqual([
    { path: `/v1/kbs/${kbId}/imports/preview`, selection: { include_globs: [], exclude_globs: [], relative_paths: ["a.md"] } },
    { path: `/v1/kbs/${kbId}/imports`, selection: { include_globs: [], exclude_globs: [], relative_paths: ["a.md"] } },
  ]);
  const secondVersion = await (await page.request.get(`/v1/versions/${second}`)).json();
  expect(Object.keys(secondVersion.document_revisions)).toHaveLength(2);
  const docs = await (await page.request.get(`/v1/kbs/${kbId}/documents`)).json();
  const bDocument = await Promise.all(
    (docs.items as Array<{ document_id: string }>).map(async (doc) =>
      (await (await page.request.get(`/v1/documents/${doc.document_id}`)).json()),
    ),
  );
  const preserved = bDocument.find((doc) => doc.revision.relative_path === "b.md");
  expect(preserved).toBeDefined();
  expect(secondVersion.document_revisions[preserved.document.document_id]).toBe(
    firstVersion.document_revisions[preserved.document.document_id],
  );
});
