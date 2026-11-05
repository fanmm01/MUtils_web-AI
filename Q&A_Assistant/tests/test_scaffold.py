from __future__ import annotations

from typing import get_type_hints

import pytest

from qa_assistant import QAService
from qa_contracts.errors import FeatureNotImplemented


def test_core_import_does_not_require_transport_or_runtime_packages() -> None:
    import sys

    assert "fastapi" not in sys.modules
    assert "httpx" not in sys.modules
    assert "ollama" not in sys.modules


@pytest.mark.asyncio
async def test_public_service_has_no_implicit_provider_side_effects() -> None:
    class NeverCall:
        def __getattr__(self, name: str) -> object:
            pytest.fail(f"provider method {name} was called")

    service = QAService(
        router=NeverCall(),
        retriever=NeverCall(),
        context_builder=NeverCall(),
        evidence_guard=NeverCall(),
        generator=NeverCall(),
    )

    with pytest.raises(FeatureNotImplemented):
        service.answer(None, None, None, None)


def test_contract_types_are_publicly_importable() -> None:
    from qa_assistant import ContextBuilder, EvidenceGuard, KnowledgeRouter
    from qa_contracts.answers import AnswerEvent, SearchRequest
    from qa_contracts.models import InferenceBinding
    from qa_contracts.ports import QAServicePort
    from qa_contracts.selection import RetrievalSelection

    assert AnswerEvent is not None
    assert SearchRequest is not None
    assert InferenceBinding is not None
    assert get_type_hints(QAService.__init__)
    assert RetrievalSelection is not None
    assert isinstance(
        QAService(
            router=KnowledgeRouter(
                catalog=object(), snapshots=object(), retriever=object(), reranker=object()
            ),
            retriever=object(),
            context_builder=ContextBuilder(token_counter=object()),
            evidence_guard=EvidenceGuard(snapshots=object(), support_checker=object()),
            generator=object(),
        ),
        QAServicePort,
    )
