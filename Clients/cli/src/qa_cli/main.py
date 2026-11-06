"""``qa`` CLI: management, Q&A and model commands.

Every command calls the shared SDK over HTTP. The CLI has no local retrieval
logic, no bypass around install confirmation and no implicit confirmation in
non-interactive mode.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from qa_client import Client, QAError
from qa_client.files import upload_directory
from qa_contracts.errors import ErrorCode

app = typer.Typer(add_completion=False, help="Knowledge-base Q&A assistant client.")
kb_app = typer.Typer(help="Knowledge base management.")
content_app = typer.Typer(help="Document and QA-pair management.")
models_app = typer.Typer(help="Model runtimes, profiles and installs.")
jobs_app = typer.Typer(help="Background jobs.")
app.add_typer(kb_app, name="kb")
app.add_typer(content_app, name="content")
app.add_typer(models_app, name="models")
app.add_typer(jobs_app, name="jobs")

State = dict[str, Any]


def _client(ctx: typer.Context) -> Client:
    state: State = ctx.obj
    return Client(state["base_url"], credential=state.get("token"), timeout=state["timeout"])


@app.callback()
def main_callback(
    ctx: typer.Context,
    base_url: Annotated[str, typer.Option("--base-url", envvar="QA_BASE_URL")] = "http://127.0.0.1:8000",
    token: Annotated[str | None, typer.Option("--token", envvar="QA_TOKEN")] = None,
    timeout: Annotated[float, typer.Option("--timeout")] = 30.0,
    json_output: Annotated[bool, typer.Option("--json", help="machine-readable output")] = False,
) -> None:
    ctx.obj = {"base_url": base_url, "token": token, "timeout": timeout, "json": json_output}


def _emit(ctx: typer.Context, payload: object) -> None:
    if ctx.obj["json"]:
        typer.echo(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    if payload is None:
        typer.echo("ok")
        return
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _selection(
    kb: list[str] | None, auto: bool, candidate_kb: list[str] | None, max_kbs: int | None
) -> dict[str, object] | None:
    """Translate repeatable ``--kb`` / ``--auto`` flags into one selection DTO."""
    if kb and auto:
        raise typer.BadParameter("--kb and --auto are mutually exclusive")
    if kb:
        targets = []
        for item in kb:
            kb_id, _, version = item.partition("@")
            target: dict[str, object] = {"kb_id": kb_id}
            if version:
                target["version_id"] = version
            targets.append(target)
        return {"mode": "explicit", "targets": targets}
    if auto:
        selection: dict[str, object] = {"mode": "auto"}
        if candidate_kb:
            selection["candidate_kb_ids"] = candidate_kb
        if max_kbs is not None:
            selection["max_kbs"] = max_kbs
        return selection
    return None


# -- knowledge bases ------------------------------------------------------
@kb_app.command("create")
def kb_create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name")],
    description: Annotated[str, typer.Option("--description")] = "",
) -> None:
    _emit(ctx, _client(ctx).create_kb({"name": name, "description": description}))


@kb_app.command("list")
def kb_list(ctx: typer.Context) -> None:
    _emit(ctx, _client(ctx).list_kbs())


@kb_app.command("get")
def kb_get(ctx: typer.Context, kb_id: str) -> None:
    _emit(ctx, _client(ctx).get_kb(kb_id))


@kb_app.command("delete")
def kb_delete(
    ctx: typer.Context,
    kb_id: str,
    expected_etag: Annotated[str | None, typer.Option("--expected-etag")] = None,
) -> None:
    _emit(ctx, _client(ctx).delete_kb(kb_id, expected_etag))


@kb_app.command("catalog")
def kb_catalog(ctx: typer.Context) -> None:
    _emit(ctx, _client(ctx).get_knowledge_catalog())


# -- content --------------------------------------------------------------
@content_app.command("put-document")
def content_put_document(
    ctx: typer.Context,
    kb_id: Annotated[str, typer.Option("--kb")],
    title: Annotated[str, typer.Option("--title")],
    text: Annotated[str, typer.Option("--text")] = "",
) -> None:
    _emit(ctx, _client(ctx).create_document(kb_id, {"kb_id": kb_id, "title": title, "text": text}))


@content_app.command("put-qa")
def content_put_qa(
    ctx: typer.Context,
    kb_id: Annotated[str, typer.Option("--kb")],
    question: Annotated[str, typer.Option("--question")],
    answer: Annotated[str, typer.Option("--answer")],
) -> None:
    _emit(
        ctx,
        _client(ctx).create_qa(
            kb_id, {"kb_id": kb_id, "question": question, "answer": answer}
        ),
    )


@content_app.command("import-preview")
def content_import_preview(
    ctx: typer.Context,
    kb_id: Annotated[str, typer.Option("--kb")],
    source_id: Annotated[str, typer.Option("--source")],
    mirror: Annotated[bool, typer.Option("--mirror")] = False,
) -> None:
    _emit(
        ctx,
        _client(ctx).preview_import(
            kb_id,
            {
                "kb_id": kb_id,
                "source_id": source_id,
                "mode": "mirror" if mirror else "merge",
                "selection": {},
            },
        ),
    )


@content_app.command("import")
def content_import(
    ctx: typer.Context,
    kb_id: Annotated[str, typer.Option("--kb")],
    source_id: Annotated[str, typer.Option("--source")],
    preview_hash: Annotated[str, typer.Option("--preview-hash")],
    mirror: Annotated[bool, typer.Option("--mirror")] = False,
) -> None:
    _emit(
        ctx,
        _client(ctx).import_documents(
            kb_id,
            {
                "kb_id": kb_id,
                "source_id": source_id,
                "mode": "mirror" if mirror else "merge",
                "selection": {},
                "expected_preview_hash": preview_hash,
            },
        ),
    )


@kb_app.command("publish")
def kb_publish(
    ctx: typer.Context,
    version_id: str,
    expected_active: Annotated[str | None, typer.Option("--expected-active")] = None,
) -> None:
    _emit(
        ctx,
        _client(ctx).publish_version(
            version_id, {"expected_active_version_id": expected_active}
        ),
    )


@kb_app.command("versions")
def kb_versions(ctx: typer.Context, kb_id: str) -> None:
    _emit(ctx, _client(ctx).list_versions(kb_id))


@kb_app.command("rollback")
def kb_rollback(
    ctx: typer.Context,
    kb_id: str,
    target: Annotated[str, typer.Option("--target")],
    expected_active: Annotated[str | None, typer.Option("--expected-active")] = None,
) -> None:
    _emit(
        ctx,
        _client(ctx).rollback(
            kb_id,
            {"target_version_id": target, "expected_active_version_id": expected_active},
        ),
    )


@kb_app.command("sources")
def kb_sources(ctx: typer.Context, kb_id: str) -> None:
    _emit(ctx, _client(ctx).list_sources(kb_id))


@kb_app.command("source-roots")
def kb_source_roots(ctx: typer.Context) -> None:
    _emit(ctx, _client(ctx).list_roots())


@kb_app.command("scan-root")
def kb_scan_root(ctx: typer.Context, root_id: str) -> None:
    _emit(ctx, _client(ctx).scan_root(root_id))


@content_app.command("upload-dir")
def content_upload_dir(
    ctx: typer.Context,
    kb_id: Annotated[str, typer.Option("--kb")],
    source_id: Annotated[str, typer.Option("--source")],
    root: Annotated[str, typer.Option("--root", help="local directory to upload")],
    path: Annotated[list[str] | None, typer.Option("--path", help="relative file only")] = None,
) -> None:
    """Upload a client-local directory; the server re-validates every byte."""
    client = _client(ctx)
    selection = {"relative_paths": list(path)} if path else {}
    _emit(
        ctx,
        upload_directory(
            client, Path(root), selection, source_id=source_id, kb_id=kb_id
        ),
    )


# -- Q&A ------------------------------------------------------------------
@app.command("search")
def search(
    ctx: typer.Context,
    question: str,
    kb: Annotated[
        list[str] | None, typer.Option("--kb", help="repeatable; kb_id[@version]")
    ] = None,
    auto: Annotated[bool, typer.Option("--auto")] = False,
    candidate_kb: Annotated[list[str] | None, typer.Option("--candidate-kb")] = None,
    max_kbs: Annotated[int | None, typer.Option("--max-kbs")] = None,
    top_k: Annotated[int, typer.Option("--top-k")] = 10,
) -> None:
    selection = _selection(kb, auto, candidate_kb, max_kbs)
    _emit(ctx, _client(ctx).search(question, selection=selection, top_k=top_k))


@app.command("ask")
def ask(
    ctx: typer.Context,
    question: str,
    kb: Annotated[
        list[str] | None, typer.Option("--kb", help="repeatable; kb_id[@version]")
    ] = None,
    auto: Annotated[bool, typer.Option("--auto")] = False,
    candidate_kb: Annotated[list[str] | None, typer.Option("--candidate-kb")] = None,
    max_kbs: Annotated[int | None, typer.Option("--max-kbs")] = None,
    inference_profile: Annotated[str | None, typer.Option("--inference-profile")] = None,
    inference_policy: Annotated[str, typer.Option("--inference-policy")] = "local_only",
    session_id: Annotated[str | None, typer.Option("--session")] = None,
    key: Annotated[str | None, typer.Option("--idempotency-key")] = None,
) -> None:
    selection = _selection(kb, auto, candidate_kb, max_kbs)
    inference = {"profile_id": inference_profile, "policy": inference_policy}
    _emit(ctx, _client(ctx).ask(question, selection, inference, session_id, key))


@app.command("history")
def history(ctx: typer.Context, session_id: str) -> None:
    _emit(ctx, _client(ctx).get_history(session_id))


# -- session selection / inference ---------------------------------------
@app.command("session-selection")
def session_selection(ctx: typer.Context, session_id: str) -> None:
    _emit(ctx, _client(ctx).get_session_selection(session_id))


@app.command("set-session-selection")
def set_session_selection(
    ctx: typer.Context,
    session_id: str,
    kb: Annotated[list[str], typer.Option("--kb")],
    expected_revision: Annotated[int, typer.Option("--expected-revision")],
) -> None:
    selection = _selection(kb, False, None, None)
    _emit(
        ctx,
        _client(ctx).set_session_selection(
            session_id,
            {"selection": selection, "expected_scope_revision": expected_revision},
        ),
    )


@app.command("session-inference")
def session_inference(ctx: typer.Context, session_id: str) -> None:
    _emit(ctx, _client(ctx).get_session_inference(session_id))


@app.command("set-session-inference")
def set_session_inference(
    ctx: typer.Context,
    session_id: str,
    profile: Annotated[str | None, typer.Option("--profile")],
    policy: Annotated[str, typer.Option("--policy")] = "local_only",
    expected_revision: Annotated[int, typer.Option("--expected-revision")] = 0,
) -> None:
    _emit(
        ctx,
        _client(ctx).set_session_inference(
            session_id,
            {
                "inference": {"profile_id": profile, "policy": policy},
                "expected_inference_revision": expected_revision,
            },
        ),
    )


# -- models ---------------------------------------------------------------
@models_app.command("capabilities")
def models_capabilities(ctx: typer.Context) -> None:
    _emit(ctx, _client(ctx).model_capabilities())


@models_app.command("discover")
def models_discover(
    ctx: typer.Context, target_id: Annotated[list[str] | None, typer.Option("--target")] = None,
) -> None:
    _emit(ctx, _client(ctx).discover_runtimes(list(target_id or [])))


@models_app.command("runtimes")
def models_runtimes(ctx: typer.Context) -> None:
    _emit(ctx, _client(ctx).list_runtimes())


@models_app.command("list")
def models_list(ctx: typer.Context) -> None:
    _emit(ctx, _client(ctx).list_models())


@models_app.command("profiles")
def models_profiles(ctx: typer.Context) -> None:
    _emit(ctx, _client(ctx).list_profiles())


@models_app.command("show-profile")
def models_show_profile(ctx: typer.Context, profile_id: str) -> None:
    _emit(ctx, _client(ctx).get_profile(profile_id))


@models_app.command("put-profile")
def models_put_profile(
    ctx: typer.Context,
    profile_id: Annotated[str | None, typer.Option("--profile")] = None,
    expected_revision: Annotated[str | None, typer.Option("--expected-revision")] = None,
) -> None:
    _emit(
        ctx,
        _client(ctx).put_profile(
            {"expected_revision": expected_revision}, profile_id=profile_id
        ),
    )


@models_app.command("disable-profile")
def models_disable_profile(
    ctx: typer.Context,
    profile_id: str,
    expected_revision: Annotated[str, typer.Option("--expected-revision")],
) -> None:
    _emit(
        ctx,
        _client(ctx).disable_profile(profile_id, {"expected_revision": expected_revision}),
    )


@models_app.command("install-preview")
def models_install_preview(
    ctx: typer.Context,
    target_id: Annotated[str, typer.Option("--target")],
    model_ref: Annotated[str, typer.Option("--model")],
) -> None:
    _emit(ctx, _client(ctx).preview_install({"target_id": target_id, "model_ref": model_ref}))


@models_app.command("install-confirm")
def models_install_confirm(
    ctx: typer.Context,
    preview_id: Annotated[str, typer.Option("--preview-id")],
    preview_hash: Annotated[str, typer.Option("--preview-hash")],
    key: Annotated[str, typer.Option("--idempotency-key")],
    yes: Annotated[bool, typer.Option("--yes", help="explicit confirmation")] = False,
) -> None:
    # Non-interactive callers must pass --yes; nothing is confirmed implicitly.
    if not yes:
        raise typer.BadParameter("confirming an install requires --yes")
    _emit(
        ctx,
        _client(ctx).confirm_install(
            {"preview_id": preview_id, "preview_hash": preview_hash, "confirmed": True},
            idempotency_key=key,
        ),
    )


@models_app.command("verify")
def models_verify(
    ctx: typer.Context,
    model_id: str,
    role: Annotated[list[str], typer.Option("--role")],
    key: Annotated[str, typer.Option("--idempotency-key")],
) -> None:
    _emit(ctx, _client(ctx).verify_model(model_id, {"roles": role}, idempotency_key=key))


# -- jobs -----------------------------------------------------------------
@jobs_app.command("get")
def jobs_get(ctx: typer.Context, job_id: str) -> None:
    _emit(ctx, _client(ctx).get_job(job_id))


@jobs_app.command("events")
def jobs_events(ctx: typer.Context, job_id: str) -> None:
    for event in _client(ctx).job_events(job_id):
        typer.echo(json.dumps(event, ensure_ascii=False))


@jobs_app.command("cancel")
def jobs_cancel(ctx: typer.Context, job_id: str) -> None:
    _emit(ctx, _client(ctx).cancel_job(job_id))


def main(argv: list[str] | None = None) -> None:
    """Entry point; maps API errors to a stable non-zero exit code.

    Exit codes: 0 success, 1 general failure, 3 feature not implemented.
    The error line on stderr is JSON so a calling program can parse it.
    """
    try:
        app(prog_name="qa", args=argv)
    except QAError as error:
        typer.echo(
            json.dumps(
                {
                    "code": error.code,
                    "message": error.message,
                    "request_id": error.request_id,
                    "details": [detail.model_dump() for detail in error.details],
                },
                ensure_ascii=False,
            ),
            err=True,
        )
        raise SystemExit(1 if error.code != ErrorCode.FEATURE_NOT_IMPLEMENTED else 3) from error


if __name__ == "__main__":
    main(sys.argv[1:])
