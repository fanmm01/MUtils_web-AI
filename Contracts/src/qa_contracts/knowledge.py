"""Knowledge-base entities, content payloads and import/version commands."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, Field

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


class SourceManifest(ContractModel):
    source_id: ID
    complete: bool = True
    files: list[ManifestFile] = Field(default_factory=list)
    scanned_at: AwareDatetime = Field(default_factory=utc_now)


class ManifestFile(ContractModel):
    relative_path: str
    digest: str
    size: int = Field(ge=0)


class Selection(ContractModel):
    """File selection for an import or source scan (not knowledge selection)."""

    include_globs: list[str] = Field(default_factory=list)
    exclude_globs: list[str] = Field(default_factory=list)
    relative_paths: list[str] = Field(default_factory=list)


class Snapshot(ContractModel):
    version_id: ID
    kb_id: ID
    parent_version_id: ID | None = None
    state: SnapshotState = SnapshotState.DRAFT
    indexed_file_ids: list[str] = Field(default_factory=list)
    embedding_profile: str | None = None
    vector_index: Literal["present", "absent"] = "absent"
    created_at: AwareDatetime = Field(default_factory=utc_now)


class SearchScope(ContractModel):
    """One knowledge base pinned to one immutable version."""

    kb_id: ID
    version_id: ID
    scope_id: ID | None = None


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


class ImportRequest(ContractModel):
    kb_id: ID
    source_id: ID
    mode: Literal["merge", "mirror"] = "merge"
    selection: Selection = Field(default_factory=Selection)
    expected_preview_hash: str | None = None


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


SourceManifest.model_rebuild()
