"""Selection and retrieval consumer-contract tests use no provider or storage."""

import pytest
from pydantic import ValidationError

from qa_assistant.retrieval import FederatedRetriever, HybridRetriever
from qa_assistant.routing import KnowledgeRouter
from qa_contracts.errors import FeatureNotImplemented
from qa_contracts.selection import AutoSelection, ExplicitSelection, KBTarget


def test_explicit_selection_accepts_one_or_multiple_distinct_knowledge_bases() -> None:
    single = ExplicitSelection(targets=[KBTarget(kb_id="kb-a")])
    multiple = ExplicitSelection(
        targets=[KBTarget(kb_id="kb-a"), KBTarget(kb_id="kb-b", version_id="v1")]
    )

    assert len(single.targets) == 1
    assert len(multiple.targets) == 2


def test_selection_contract_rejects_empty_or_duplicate_targets() -> None:
    with pytest.raises(ValidationError):
        ExplicitSelection(targets=[])
    with pytest.raises(ValidationError):
        ExplicitSelection(targets=[KBTarget(kb_id="kb-a"), KBTarget(kb_id="kb-a")])
    with pytest.raises(ValidationError):
        AutoSelection(candidate_kb_ids=[])


@pytest.mark.asyncio
async def test_router_and_retrievers_never_fabricate_results() -> None:
    router = KnowledgeRouter(
        catalog=object(),
        snapshots=object(),
        retriever=object(),
        reranker=object(),
    )
    hybrid = HybridRetriever(
        keyword_reader=object(), vector_reader=object(), embedder=object()
    )
    federated = FederatedRetriever(retriever=hybrid, embedder=object(), reranker=object())

    with pytest.raises(FeatureNotImplemented):
        await router.rank_candidates("question", [], object())
    with pytest.raises(FeatureNotImplemented):
        await hybrid.retrieve("question", object(), object())
    with pytest.raises(FeatureNotImplemented):
        await federated.retrieve("question", object(), object())
