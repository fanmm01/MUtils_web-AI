"""Knowledge-base entities, content payloads and import/version commands."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, Field, field_validator, model_validator

from .base import ID, ContractModel, utc_now


class ContentKind(StrEnum):
    DOCUMENT = "document"
    QA_PAIR = "qa_pair"


class SnapshotState(StrEnum):
    DRAFT = "draft"
    STAGING = "staging"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"


class LocatorKind(StrEnum):
    MARKDOWN_LINES = "markdown_lines"
    TEXT_LINES = "text_lines"
    WORD_PARAGRAPH = "word_paragraph"
    WORD_TABLE = "word_table"
    EXCEL_RANGE = "excel_range"
    PDF_PAGE = "pdf_page"
    QA_FIELDS = "qa_fields"


class Locator(ContractModel):
    """Traceable original position. Never invent a page number a format lacks."""

    kind: LocatorKind
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    page: int | None = Field(default=None, ge=1)
    sheet: str | None = None
    cell_range: str | None = None
    paragraph: int | None = Field(default=None, ge=0)
    heading: str | None = None


class BlobRef(ContractModel):
    digest: str = Field(min_length=1)
    size: int = Field(ge=0)
    media_type: str = "application/octet-stream"


class ParsedBlock(ContractModel):
    text: str
    locator: Locator
    heading: str | None = None


class ParsedDocument(ContractModel):
    blocks: list[ParsedBlock] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    needs_ocr: bool = False


class ChunkProfile(ContractModel):
    """Explicit corpus-tested settings; the Gate does not certify a default size."""

    target_tokens: int = Field(ge=1)
    overlap_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def _overlap_smaller_than_target(self) -> ChunkProfile:
        if self.overlap_tokens >= self.target_tokens:
            raise ValueError("chunk overlap must be smaller than the target length")
        return self


class Chunk(ContractModel):
    chunk_id: ID
    kb_id: ID
    version_id: ID
    revision_id: ID
    content_hash: str
    text: str
    locator: Locator
    ordinal: int = Field(ge=0)


class KnowledgeBase(ContractModel):
    kb_id: ID
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    domain_tags: list[str] = Field(default_factory=list)
    routing_examples: list[str] = Field(default_factory=list)
    active_version_id: ID | None = None
    etag: str
    updated_at: AwareDatetime = Field(default_factory=utc_now)


class Revision(ContractModel):
    revision_id: ID
    document_id: ID
    parent_revision_id: ID | None = None
    content_kind: ContentKind = ContentKind.DOCUMENT
    source_id: ID | None = None
    relative_path: str | None = None
    blob: BlobRef | None = None
    normalized_text: str = ""
    diagnostics: list[str] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=utc_now)


class Document(ContractModel):
    document_id: ID
    kb_id: ID
    title: str
    latest_revision_id: ID
    content_kind: ContentKind = ContentKind.DOCUMENT
    deleted: bool = False
    updated_at: AwareDatetime = Field(default_factory=utc_now)


class DocumentDetail(ContractModel):
    document: Document
    revision: Revision


class QAPair(ContractModel):
    qa_id: ID
    kb_id: ID
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    revision_id: ID
    deleted: bool = False
    updated_at: AwareDatetime = Field(default_factory=utc_now)


class Source(ContractModel):
    source_id: ID
    kb_id: ID
    kind: Literal["local_root", "upload"]
    root_id: str | None = None
    display_name: str
    revision: ID
    created_at: AwareDatetime = Field(default_factory=utc_now)


class Selection(ContractModel):
    """File selection for an import or source scan (not knowledge selection)."""

    include_globs: list[str] = Field(default_factory=list)
    exclude_globs: list[str] = Field(default_factory=list)
    relative_paths: list[str] = Field(default_factory=list)

    @field_validator("relative_paths")
    @classmethod
    def _safe_selected_paths(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_relative_path(value)
        return values


class UploadManifest(ContractModel):
    """Untrusted client file claims; these never authorize mirror deletions."""

    source_id: ID
    selection: Selection = Field(default_factory=Selection)
    files: list[ManifestFile] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_files(self) -> UploadManifest:
        paths = [entry.relative_path for entry in self.files]
        if len(set(paths)) != len(paths):
            raise ValueError("manifest file paths must be unique")
        selected = self.selection.relative_paths
        if len(set(selected)) != len(selected):
            raise ValueError("selected file paths must be unique")
        if selected and set(selected) != set(paths) and not (
            isinstance(self, SourceManifest) and self.scan_status == "failed"
        ):
            raise ValueError("selected file paths must match the upload manifest")
        return self


class SourceManifest(UploadManifest):
    """Server-verified scan result; only a successful full scan can be complete."""

    scan_scope: Literal["full", "partial"]
    scan_status: Literal["succeeded", "failed"]
    complete: bool
    scanned_at: AwareDatetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _complete_only_for_successful_full_scan(self) -> SourceManifest:
        if self.complete and (
            self.scan_scope != "full"
            or self.scan_status != "succeeded"
            or self.selection.include_globs
            or self.selection.exclude_globs
            or self.selection.relative_paths
        ):
            raise ValueError("complete requires an unrestricted successful full source scan")
        return self


class UploadBatch(ContractModel):
    batch_id: ID
    source_id: ID


def _validate_relative_path(value: str) -> None:
    path = value.replace("\\", "/")
    parts = path.split("/")
    if (
        not value or value != path or path.startswith("/") or ":" in path
        or any(part in {"", ".", ".."} for part in parts)
        or any(ord(char) < 32 for char in path)
    ):
        raise ValueError("relative paths must stay within the source directory")


class ManifestFile(ContractModel):
    relative_path: str = Field(min_length=1)
    digest: str = Field(min_length=1)
    size: int = Field(ge=0)

    @field_validator("relative_path")
    @classmethod
    def _safe_relative_path(cls, value: str) -> str:
        _validate_relative_path(value)
        return value


class Snapshot(ContractModel):
    version_id: ID
    kb_id: ID
    parent_version_id: ID | None = None
    state: SnapshotState = SnapshotState.DRAFT
    indexed_file_ids: list[str] = Field(default_factory=list)
    document_revisions: dict[ID, ID] = Field(default_factory=dict)
    keyword_profile: str | None = None
    keyword_index_ref: str | None = None
    embedding_profile: str | None = None
    vector_index: Literal["present", "absent"] = "absent"
    created_at: AwareDatetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _published_keyword_index_is_readable(self) -> Snapshot:
        if self.state in {SnapshotState.READY, SnapshotState.PUBLISHED} and not (
            self.keyword_profile and self.keyword_index_ref
        ):
            raise ValueError("ready snapshots require a keyword index and profile")
        return self


class SearchScope(ContractModel):
    """One knowledge base pinned to one immutable version and index profile."""

    kb_id: ID
    version_id: ID
    scope_id: ID | None = None
    keyword_profile: str = Field(min_length=1)
    index_ref: str = Field(min_length=1)
    embedding_profile: str | None = None


class CreateKB(ContractModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    domain_tags: list[str] = Field(default_factory=list)
    routing_examples: list[str] = Field(default_factory=list)


class UpdateKB(ContractModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    domain_tags: list[str] | None = None
    routing_examples: list[str] | None = None


class PutDocument(ContractModel):
    kb_id: ID
    title: str = Field(min_length=1, max_length=400)
    text: str = ""
    relative_path: str | None = None
    expected_revision_id: ID | None = None


class PutQA(ContractModel):
    kb_id: ID
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    expected_revision_id: ID | None = None


class ImportPreviewRequest(ContractModel):
    kb_id: ID
    source_id: ID
    mode: Literal["merge", "mirror"] = "merge"
    selection: Selection = Field(default_factory=Selection)


class ImportRequest(ImportPreviewRequest):
    expected_preview_hash: str = Field(min_length=1)


class ImportPreview(ContractModel):
    preview_id: ID
    kb_id: ID
    preview_hash: str
    added: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=utc_now)


class ChangeSet(ContractModel):
    added: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    unchanged: list[str] = Field(default_factory=list)


class ChangeReceipt(ContractModel):
    kb_id: ID
    document_id: ID | None = None
    version_id: ID | None = None
    job_id: ID | None = None
    requires_publish: bool = True


class PublishRequest(ContractModel):
    expected_active_version_id: ID | None = None


class RollbackRequest(ContractModel):
    target_version_id: ID
    expected_active_version_id: ID | None = None


UploadManifest.model_rebuild()
SourceManifest.model_rebuild()
