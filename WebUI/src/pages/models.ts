/**
 * Models page. Detection runs on the backend host, only against runtimes the
 * server allow-lists. This page never probes the browser's machine, never
 * accepts an endpoint, path or key, and never shows a runtime it was not given.
 */

import type { Client } from "@qa/client";
import {
  button,
  createStatusArea,
  describeError,
  field,
  h,
  note,
  pageHeader,
  runAction,
  section,
  toolbar,
  type StatusArea,
} from "../components/ui.js";
import type { PageContext } from "../state.js";

const STATE_FIELDS: ReadonlyArray<readonly [string, string]> = [
  ["installed", "部署器程序或安装证据存在"],
  ["running", "部署器的协议服务可以访问"],
  ["downloaded", "部署器登记了完整的模型"],
  ["loaded", "模型当前驻留在内存或显存"],
  ["verified_roles", "通过了哪些角色（生成、嵌入、支持校验等）的最小调用验证"],
  ["unknown", "无法确认；未知不等于不存在"],
];

export function renderModelsPage(ctx: PageContext): HTMLElement {
  const capabilityStatus = createStatusArea();
  const facts = h("dl", { class: "facts" });
  const runtimeStatus = createStatusArea();
  const modelStatus = createStatusArea();
  const profileStatus = createStatusArea();
  void loadCapabilities(ctx.client, facts, capabilityStatus);

  const stateTable = h(
    "table",
    { class: "table" },
    h("thead", {}, h("tr", {}, h("th", {}, "状态字段"), h("th", {}, "含义"))),
    h(
      "tbody",
      {},
      ...STATE_FIELDS.map(([name, meaning]) => h("tr", {}, h("td", {}, h("code", {}, name)), h("td", {}, meaning))),
    ),
  );

  return h(
    "div",
    { class: "page" },
    pageHeader(
      "模型",
      "模型发现、配置、按需安装与角色验证将在 P3 实现。检测在后端服务所在主机进行，本页不扫描浏览器所在电脑。",
    ),
    section("服务端模型能力", capabilityStatus.element, facts),
    section("状态字段说明", stateTable, note("已下载不等于已验证；未通过角色验证的模型不能被选为推理配置。")),
    section(
      "运行时",
      toolbar(
        button("刷新运行时列表", () => void loadRuntimes(ctx.client, runtimeStatus)),
        h("button", { type: "button", disabled: true }, "检测运行时"),
      ),
      runtimeStatus.element,
      note("检测只针对服务端配置允许的运行时；当前没有可检测的运行时，检测按钮不可用。"),
    ),
    section(
      "模型与推理配置",
      toolbar(
        button("刷新模型列表", () => void loadModels(ctx.client, modelStatus)),
        button("刷新推理配置", () => void loadProfiles(ctx.client, profileStatus)),
      ),
      modelStatus.element,
      profileStatus.element,
      h(
        "fieldset",
        { class: "form", disabled: true },
        h("legend", {}, "编辑推理配置"),
        field("生成模型", h("select", {}, h("option", {}, "（无已验证模型）"))),
        field("嵌入模型", h("select", {}, h("option", {}, "（无已验证模型）"))),
        field("推理策略", h("select", {}, h("option", {}, "local_only（仅本地）"))),
        h("button", { type: "button" }, "保存为新修订"),
      ),
      note("推理配置编辑尚未实现，需要先有通过角色验证的模型。"),
    ),
    section(
      "按需安装",
      h(
        "fieldset",
        { class: "form", disabled: true },
        field("运行时", h("select", {}, h("option", {}, "（无可用运行时）"))),
        field("模型标签", h("input", { placeholder: "如 qwen3:8b" })),
        toolbar(h("button", { type: "button" }, "生成安装预览"), h("button", { type: "button" }, "确认安装")),
      ),
      note("安装分两步：先生成预览（标签、大小、摘要、许可、未知项），不下载；确认后才开始下载。当前没有可用运行时。"),
    ),
    section("模型任务", note("安装与验证任务尚未实现，没有任务进度可显示。")),
  );
}

/** Static scaffold capabilities from the server; this is not a runtime probe. */
export async function loadCapabilities(
  client: Client,
  facts: HTMLElement,
  status: StatusArea,
): Promise<void> {
  status.pending("读取服务端模型能力…");
  try {
    const caps = await client.modelCapabilities();
    const runtimes = Array.isArray(caps.runtimes) ? caps.runtimes.length : null;
    const rows: Array<readonly [string, string]> = [
      ["模式", typeof caps.mode === "string" ? caps.mode : "未知"],
      ["已配置运行时", runtimes === null ? "未知" : runtimes === 0 ? "0（服务端未配置任何运行时）" : String(runtimes)],
      ["安装需显式确认", caps.install_requires_confirmation === true ? "是" : "未知"],
      ["检测主机与时间", "尚未检测"],
    ];
    facts.replaceChildren(...rows.flatMap(([term, value]) => [h("dt", {}, term), h("dd", {}, value)]));
    status.done("以上为服务端返回的静态能力说明，不代表已检测本机。");
  } catch (error) {
    facts.replaceChildren();
    status.fail("读取服务端模型能力", describeError(error));
  }
}

export function loadRuntimes(client: Client, status: StatusArea): Promise<void> {
  return runAction(status, "刷新运行时列表", () => client.listRuntimes());
}

export function loadModels(client: Client, status: StatusArea): Promise<void> {
  return runAction(status, "刷新模型列表", () => client.listModels());
}

export function loadProfiles(client: Client, status: StatusArea): Promise<void> {
  return runAction(status, "刷新推理配置", () => client.listProfiles());
}
