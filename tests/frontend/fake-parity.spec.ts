import { expect, test } from "vitest";
import { createFakeApi } from "./fake-api.js";

async function digest(text: string): Promise<string> {
  const bytes = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

test("A to B to A imports create new jobs while replaying one preview reuses its job", async () => {
  const fake = createFakeApi();
  const kb = fake.seedKB("baseline parity");
  const sourceId = "src_cycle";
  fake.state.sources.set(sourceId, {
    source_id: sourceId,
    kb_id: kb.kb_id,
    kind: "upload",
    display_name: "source",
    revision: "r1",
  });

  const upload = async (text: string): Promise<void> => {
    const bytes = new TextEncoder().encode(text);
    const batch = await fake.client.beginUpload({
      source_id: sourceId,
      files: [{ relative_path: "a.md", digest: await digest(text), size: bytes.byteLength }],
    });
    await fake.client.putUploadFile(batch.batch_id, "a.md", new Blob([bytes]));
    const manifest = await fake.client.completeUpload(batch.batch_id);
    expect(manifest.scan_status).toBe("succeeded");
  };

  const submit = async (): Promise<{ jobId: string; preview: { modified?: string[]; added?: string[] } }> => {
    const body = { kb_id: kb.kb_id, source_id: sourceId, mode: "merge" as const, selection: {} };
    const preview = await fake.client.previewImport(kb.kb_id, body);
    const receipt = await fake.client.importDocuments(kb.kb_id, {
      ...body,
      expected_preview_hash: preview.preview_hash,
    });
    expect(receipt.job_id).toBeTruthy();
    const replay = await fake.client.importDocuments(kb.kb_id, {
      ...body,
      expected_preview_hash: preview.preview_hash,
    });
    expect(replay.job_id).toBe(receipt.job_id);
    return { jobId: receipt.job_id as string, preview };
  };

  const publish = async (jobId: string, expected: string | null): Promise<string> => {
    expect(fake.runWorker()).toContain(jobId);
    const job = await fake.client.getJob(jobId);
    expect(job.state).toBe("succeeded");
    const version = job.result_version_id as string;
    await fake.client.publishVersion(version, { expected_active_version_id: expected });
    return version;
  };

  await upload("# A\n\nfirst\n");
  const first = await submit();
  expect(first.preview.added).toEqual(["a.md"]);
  const v1 = await publish(first.jobId, null);

  await upload("# B\n\nsecond\n");
  const second = await submit();
  expect(second.preview.modified).toEqual(["a.md"]);
  expect(second.jobId).not.toBe(first.jobId);
  const v2 = await publish(second.jobId, v1);

  await upload("# A\n\nfirst\n");
  const third = await submit();
  expect(third.preview.modified).toEqual(["a.md"]);
  expect(third.jobId).not.toBe(first.jobId);
  expect(third.jobId).not.toBe(second.jobId);
  const v3 = await publish(third.jobId, v2);
  expect(v3).not.toBe(v1);
  expect((await fake.client.getKB(kb.kb_id)).active_version_id).toBe(v3);
});
