"""P2 keyword routing/retrieval tests with fake pinned snapshots and readers."""

from __future__ import annotations

import pytest

from qa_assistant.retrieval import FederatedRetriever, HybridRetriever
from qa_assistant.routing import KnowledgeRouter
from qa_contracts.answers import Hit
from qa_contracts.base import Page
from qa_contracts.errors import PermissionDenied
from qa_contracts.knowledge import SearchScope
from qa_contracts.models import InferenceBinding, InferencePolicy
from qa_contracts.operations import AccessScope
from qa_contracts.selection import (
    AutoSelection,
    CatalogQuery,
    ExplicitSelection,
    KBDescriptor,
    KBTarget,
    PinnedKBTarget,
    ProbeBudget,
    ResolvedScope,
    RoutingContext,
    SelectionStatus,
)


class Catalog:
    def __init__(self):
        self.rows = [
            KBDescriptor(kb_id="product", name="产品", description="产品安装步骤", version_id="v1"),
            KBDescriptor(kb_id="ops", name="运维", description="服务故障 ERR-404", version_id="v2"),
        ]
        self.fail_after = None
        self.delay = 0

    async def list_authorized(self, access, query: CatalogQuery):
        rows = sorted(
            (item for item in self.rows if item.kb_id in access.kb_ids),
            key=lambda item: item.kb_id,
        )
        if query.cursor is not None:
            rows = [item for item in rows if item.kb_id > query.cursor]
        selected = rows[: query.limit]
        next_cursor = selected[-1].kb_id if len(rows) > query.limit else None
        if self.fail_after is not None and query.cursor == self.fail_after:
            raise RuntimeError("catalog page unavailable")
        return Page(items=selected, next_cursor=next_cursor)

    async def get_authorized(self, access, kb_ids):
        available = {item.kb_id: item for item in self.rows if item.kb_id in access.kb_ids}
        if any(kb_id not in available for kb_id in kb_ids):
            raise PermissionDenied("retrieve knowledge base")
        return [available[kb_id] for kb_id in kb_ids]


class Snapshots:
    def __init__(self):
        self.calls = []
        self.version = {"product": "v1", "ops": "v2"}
        self.delay = 0

    async def resolve_many(self, targets, access):
        self.calls.append(("resolve", tuple(item.kb_id for item in targets)))
        return ResolvedScope(
            scope_id="scope",
            targets=[
                PinnedKBTarget(
                    kb_id=item.kb_id, version_id=item.version_id or self.version[item.kb_id]
                )
                for item in targets
            ],
        )

    async def search_scope(self, target, access):
        assert target.kb_id in access.kb_ids
        self.calls.append(("search", target.kb_id, target.version_id))
        if self.delay:
            import asyncio

            await asyncio.sleep(self.delay)
        return SearchScope(
            kb_id=target.kb_id,
            version_id=target.version_id,
            keyword_profile="zh",
            index_ref="ref",
        )


class Keywords:
    def __init__(self):
        self.calls = []
        self.fail = None

    async def search(self, query, scope, k):
        self.calls.append((scope.kb_id, scope.version_id, k))
        if self.fail == scope.kb_id:
            raise RuntimeError("keyword snapshot unavailable")
        return (
            [
                Hit(
                    kb_id=scope.kb_id,
                    version_id=scope.version_id,
                    chunk_id=f"{scope.kb_id}-chunk",
                    text="安装服务故障 ERR-404 处理方法"
                    if scope.kb_id == "ops"
                    else "产品安装步骤",
                    score=10000 if scope.kb_id == "product" else 0.1,
                )
            ]
            if ("ERR-404" in query and scope.kb_id == "ops")
            or ("安装" in query and scope.kb_id == "product")
            else []
        )


def build():
    snapshots = Snapshots()
    keywords = Keywords()
    hybrid = HybridRetriever(keyword_reader=keywords)
    catalog = Catalog()
    router = KnowledgeRouter(catalog=catalog, snapshots=snapshots, retriever=hybrid)
    federation = FederatedRetriever(retriever=hybrid, snapshots=snapshots)
    access = AccessScope(principal_id="p", kb_ids=["product", "ops"])
    binding = InferenceBinding(binding_id="no-model", policy=InferencePolicy.LOCAL_ONLY)
    return router, federation, snapshots, keywords, access, binding


@pytest.mark.asyncio
async def test_explicit_single_and_multiple_pin_and_probe_no_extra_kb() -> None:
    router, federation, snapshots, keywords, access, binding = build()
    context = RoutingContext()
    selection = ExplicitSelection(targets=[KBTarget(kb_id="product")])
    prepared = await router.prepare("安装", selection, context, access)
    assert prepared.pinned_targets == [PinnedKBTarget(kb_id="product", version_id="v1")]
    result = await router.select("安装", prepared, context, binding)
    assert result.status == SelectionStatus.RESOLVED
    hits = await federation.retrieve(
        "安装", ResolvedScope(scope_id="s", targets=result.targets), binding, 3, access=access
    )
    assert [item.kb_id for item in hits] == ["product"]
    assert keywords.calls == [("product", "v1", 3)]

    prepared = await router.prepare(
        "安装 ERR-404",
        ExplicitSelection(targets=[KBTarget(kb_id="product"), KBTarget(kb_id="ops")]),
        context,
        access,
    )
    result = await router.select("安装 ERR-404", prepared, context, binding)
    hits = await federation.retrieve(
        "安装 ERR-404",
        ResolvedScope(scope_id="s2", targets=result.targets),
        binding,
        2,
        access=access,
    )
    assert {item.kb_id for item in hits} == {"product", "ops"}
    assert [item.kb_id for item in hits][0] == "ops"  # common text coverage, not raw BM25
    assert [item.score for item in hits][0] > [item.score for item in hits][1]
    assert snapshots.calls[-2:] == [("search", "product", "v1"), ("search", "ops", "v2")]
    assert keywords.calls[-2:] == [("product", "v1", 2), ("ops", "v2", 2)]


@pytest.mark.asyncio
async def test_auto_candidate_allowlist_no_match_ambiguity_and_pins() -> None:
    router, _, snapshots, keywords, access, binding = build()
    context = RoutingContext()
    prepared = await router.prepare("ERR-404", AutoSelection(max_kbs=1), RoutingContext(), access)
    assert [item.kb_id for item in prepared.ranked] == ["ops"]
    with pytest.raises(PermissionDenied):
        await router.select(
            "ERR-404", prepared, RoutingContext(user_questions=["different"]), binding
        )
    result = await router.select("ERR-404", prepared, RoutingContext(), binding)
    assert [(item.kb_id, item.version_id) for item in result.targets] == [("ops", "v2")]
    assert keywords.calls == [("ops", "v2", 5)]
    snapshots.version["ops"] = "v3"  # publication after pinning cannot change this turn

    prepared = await router.prepare("无关问题", AutoSelection(), context, access)
    assert (
        await router.select("无关问题", prepared, context, binding)
    ).status == SelectionStatus.NO_MATCH
    prepared = await router.prepare(
        "安装 ERR-404",
        AutoSelection(),
        RoutingContext(user_questions=["ERR-404"]),
        access,
    )
    assert [item.kb_id for item in prepared.ranked] == ["ops", "product"]
    result = await router.select(
        "安装 ERR-404", prepared, RoutingContext(user_questions=["ERR-404"]), binding
    )
    assert result.status == SelectionStatus.NEEDS_CLARIFICATION
    prepared = await router.prepare("安装", AutoSelection(), context, access)
    with pytest.raises(PermissionDenied):
        await router.select("其他", prepared, context, binding)
    prepared = await router.prepare(
        "产品安装步骤 运维服务故障 ERR-404", AutoSelection(max_kbs=1), context, access
    )
    assert (
        await router.select("产品安装步骤 运维服务故障 ERR-404", prepared, context, binding)
    ).status == SelectionStatus.NEEDS_CLARIFICATION
    prepared = await router.prepare(
        "产品安装步骤 运维服务故障 ERR-404", AutoSelection(max_kbs=2), context, access
    )
    assert (
        len(
            (
                await router.select("产品安装步骤 运维服务故障 ERR-404", prepared, context, binding)
            ).targets
        )
        == 2
    )

    with pytest.raises(PermissionDenied):
        await router.prepare(
            "私有", AutoSelection(candidate_kb_ids=["product", "private"]), context, access
        )
    only_product = await router.prepare(
        "ERR-404", AutoSelection(candidate_kb_ids=["product"]), context, access
    )
    assert (
        await router.select("ERR-404", only_product, context, binding)
    ).status == SelectionStatus.NO_MATCH


@pytest.mark.asyncio
async def test_pagination_and_probe_failures_never_become_partial_success() -> None:
    router, federation, _, keywords, access, binding = build()
    catalog = router._catalog
    catalog.rows = [
        KBDescriptor(kb_id=f"kb-{index:03}", name="安装知识库", version_id=f"v{index}")
        for index in range(201)
    ]
    access = access.model_copy(update={"kb_ids": [item.kb_id for item in catalog.rows]})
    catalog.fail_after = "kb-199"
    with pytest.raises(RuntimeError, match="catalog page"):
        await router.prepare("安装", AutoSelection(), RoutingContext(), access)
    catalog.fail_after = None
    catalog.rows = [
        KBDescriptor(kb_id=f"kb-{index:03}", name="安装知识库", version_id=f"v{index}")
        for index in range(52)
    ]
    access = access.model_copy(update={"kb_ids": [item.kb_id for item in catalog.rows]})
    with pytest.raises(ValueError, match="narrow the candidates"):
        await router.prepare("安装", AutoSelection(), RoutingContext(), access)
    catalog.rows = [
        KBDescriptor(kb_id="product", name="产品", description="产品安装步骤", version_id="v1"),
        KBDescriptor(kb_id="ops", name="运维", description="服务故障 ERR-404", version_id="v2"),
    ]
    access = access.model_copy(update={"kb_ids": ["product", "ops"]})

    prepared = await router.prepare(
        "安装 ERR-404",
        ExplicitSelection(targets=[KBTarget(kb_id="product"), KBTarget(kb_id="ops")]),
        RoutingContext(),
        access,
    )
    keywords.fail = "ops"
    with pytest.raises(RuntimeError, match="unavailable"):
        await federation.retrieve(
            "安装 ERR-404",
            ResolvedScope(scope_id="s", targets=prepared.pinned_targets),
            binding,
            4,
            access=access,
        )

    keywords.fail = None
    keywords.calls.clear()
    prepared = await router.prepare(
        "安装 ERR-404",
        ExplicitSelection(targets=[KBTarget(kb_id="product"), KBTarget(kb_id="ops")]),
        RoutingContext(),
        access,
    )
    result = await router.select("安装 ERR-404", prepared, RoutingContext(), binding)
    keywords.fail = "ops"
    with pytest.raises(RuntimeError, match="unavailable"):
        await federation.retrieve(
            "安装 ERR-404",
            ResolvedScope(scope_id="s", targets=result.targets),
            binding,
            4,
            access=access,
        )
    assert [call[0] for call in keywords.calls] == ["product", "ops"]
    with pytest.raises(PermissionDenied):
        await federation.retrieve(
            "安装",
            ResolvedScope(scope_id="s", targets=result.targets),
            binding,
            4,
            access=AccessScope(principal_id="other", kb_ids=["product"]),
        )


@pytest.mark.asyncio
async def test_probe_timeout_aborts_instead_of_reporting_no_match() -> None:
    import asyncio

    router, _, snapshots, _, access, binding = build()
    snapshots.delay = 0.05
    scope = ResolvedScope(
        scope_id="s",
        targets=[PinnedKBTarget(kb_id="product", version_id="v1")],
    )
    with pytest.raises(TimeoutError):
        await router.probe(
            "安装", scope, ProbeBudget(max_kbs=1, timeout_ms=1), binding, access=access
        )
    assert asyncio.get_running_loop().is_running()
