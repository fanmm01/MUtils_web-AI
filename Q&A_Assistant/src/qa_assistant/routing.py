"""Deterministic, authorized, model-free P2 knowledge-base selection."""

from __future__ import annotations

import asyncio
import re
import unicodedata
from uuid import uuid4

from qa_contracts.errors import PermissionDenied, ValidationFailed
from qa_contracts.models import InferenceBinding
from qa_contracts.operations import AccessScope
from qa_contracts.ports import KnowledgeCatalog, Reranker, SnapshotReader
from qa_contracts.selection import (
    AutoSelection,
    CatalogQuery,
    ExplicitSelection,
    KBDescriptor,
    KBTarget,
    PinnedKBTarget,
    PreparedSelection,
    ProbeBudget,
    ProbeResult,
    RankedKB,
    ResolvedScope,
    RetrievalSelection,
    RoutingContext,
    SelectionResult,
    SelectionStatus,
)

_TERM = re.compile(r"[㐀-鿿]+|[a-z0-9_]+(?:[-./][a-z0-9_]+)*")


def _terms(value: str) -> set[str]:
    terms: set[str] = set()
    for match in _TERM.finditer(unicodedata.normalize("NFKC", value).casefold()):
        token = match.group()
        if "㐀" <= token[0] <= "鿿" and len(token) > 1:
            terms.update(token[index : index + 2] for index in range(len(token) - 1))
        else:
            terms.add(token)
    return terms


class KnowledgeRouter:
    """Prepare pins authorized snapshots; selection probes only that captured set."""

    def __init__(
        self,
        *,
        catalog: KnowledgeCatalog,
        snapshots: SnapshotReader,
        retriever: object,
        reranker: Reranker | None = None,
    ) -> None:
        self._catalog = catalog
        self._snapshots = snapshots
        self._retriever = retriever
        self._reranker = reranker
        self._prepared: dict[str, tuple[PreparedSelection, AccessScope, RoutingContext, str]] = {}

    async def prepare(
        self,
        query: str,
        selection: RetrievalSelection,
        context: RoutingContext,
        access: AccessScope,
    ) -> PreparedSelection:
        if (
            not isinstance(access, AccessScope)
            or not isinstance(context, RoutingContext)
            or not query.strip()
        ):
            raise ValidationFailed()
        if isinstance(selection, ExplicitSelection):
            requested = selection.targets
            descriptors = await self._catalog.get_authorized(
                access, [target.kb_id for target in requested]
            )
            if [item.kb_id for item in descriptors] != [target.kb_id for target in requested]:
                raise PermissionDenied("retrieve knowledge base")
            pinned = (await self._snapshots.resolve_many(requested, access)).targets
            self._validate_targets(requested, pinned)
            ranked: list[RankedKB] = []
        elif isinstance(selection, AutoSelection):
            if selection.candidate_kb_ids is not None:
                descriptors = await self._catalog.get_authorized(access, selection.candidate_kb_ids)
                if [item.kb_id for item in descriptors] != selection.candidate_kb_ids:
                    raise PermissionDenied("retrieve knowledge base")
            else:
                descriptors = []
                cursor = None
                seen_cursors: set[str] = set()
                while True:
                    page = await self._catalog.list_authorized(
                        access, CatalogQuery(limit=200, cursor=cursor)
                    )
                    descriptors.extend(page.items)
                    if page.next_cursor is None:
                        break
                    if page.next_cursor in seen_cursors:
                        raise ValueError("catalog cursor did not advance")
                    seen_cursors.add(page.next_cursor)
                    cursor = page.next_cursor
            if len({item.kb_id for item in descriptors}) != len(descriptors):
                raise ValueError("catalog returned duplicate knowledge bases")
            if any(item.kb_id not in access.kb_ids or not item.version_id for item in descriptors):
                raise PermissionDenied("retrieve knowledge base")
            ranked = await self.rank_candidates(query, descriptors, context)
            if len(ranked) > 50:
                # ProbeBudget caps candidate reads; never silently omit likely KBs.
                raise ValueError("too many matching knowledge bases; narrow the candidates")
            requested = [
                KBTarget(kb_id=item.kb_id, version_id=item.version_id)
                for item in descriptors
                if any(rank.kb_id == item.kb_id for rank in ranked)
            ]
            pinned = (
                (await self._snapshots.resolve_many(requested, access)).targets if requested else []
            )
            self._validate_targets(requested, pinned)
        else:
            raise ValidationFailed()
        prepared = PreparedSelection(
            prepared_id=uuid4().hex,
            requested=selection,
            candidates=descriptors,
            ranked=ranked,
            pinned_targets=pinned,
        )
        self._prepared[prepared.prepared_id] = (
            prepared.model_copy(deep=True),
            access.model_copy(deep=True),
            context.model_copy(deep=True),
            query,
        )
        return prepared

    @staticmethod
    def _validate_targets(requested: list[KBTarget], pinned: list[PinnedKBTarget]) -> None:
        if len(requested) != len(pinned) or any(
            original.kb_id != actual.kb_id
            or (original.version_id is not None and original.version_id != actual.version_id)
            for original, actual in zip(requested, pinned, strict=True)
        ):
            raise ValueError("snapshot resolution changed the requested targets")

    async def select(
        self,
        query: str,
        prepared: PreparedSelection,
        context: RoutingContext,
        binding: InferenceBinding,
    ) -> SelectionResult:
        capture = self._prepared.get(prepared.prepared_id)
        if capture is None or capture[0] != prepared:
            raise PermissionDenied("use prepared knowledge selection")
        if capture[2] != context or capture[3] != query:
            raise PermissionDenied("use prepared knowledge selection")
        access = capture[1]
        if isinstance(prepared.requested, ExplicitSelection):
            del self._prepared[prepared.prepared_id]
            return SelectionResult(
                status=SelectionStatus.RESOLVED,
                mode="explicit",
                targets=prepared.pinned_targets,
                reason="explicit authorized targets pinned to immutable versions",
            )
        if not prepared.ranked:
            del self._prepared[prepared.prepared_id]
            return SelectionResult(
                status=SelectionStatus.NO_MATCH,
                mode="auto",
                reason="no matching catalog description",
            )
        if {item.kb_id for item in prepared.ranked} != {
            item.kb_id for item in prepared.pinned_targets
        }:
            raise ValueError("unresolved ranked candidate")
        maximum = prepared.requested.max_kbs or 1
        budget = ProbeBudget(max_kbs=len(prepared.pinned_targets), max_chunks_per_kb=5)
        probes = await self.probe(
            query,
            ResolvedScope(scope_id=prepared.prepared_id, targets=prepared.pinned_targets),
            budget,
            binding,
            access=access,
        )
        result = self.decide(prepared.ranked, probes, maximum)
        self._prepared.pop(prepared.prepared_id, None)
        return result

    async def rank_candidates(
        self,
        query: str,
        descriptors: list[KBDescriptor],
        context: RoutingContext,
    ) -> list[RankedKB]:
        if not isinstance(context, RoutingContext):
            from qa_contracts.errors import FeatureNotImplemented

            raise FeatureNotImplemented("knowledge candidate ranking")
        terms = _terms(query)
        if not terms:
            return []
        context_terms: set[str] = set()
        for question in context.user_questions:
            context_terms.update(_terms(question))
        # Current wording carries full weight; previous user questions can
        # disambiguate follow-ups but cannot replace a nonmatching current turn.
        routing_terms = terms | context_terms
        ranked: list[RankedKB] = []
        for item in descriptors:
            if not item.version_id:
                continue
            values = [item.name, item.description, *item.domain_tags, *item.routing_examples]
            coverage = max(
                (
                    (len(terms & _terms(value)) + 0.25 * len(context_terms & _terms(value)))
                    / len(routing_terms)
                    for value in values
                ),
                default=0,
            )
            if coverage > 0:
                ranked.append(
                    RankedKB(kb_id=item.kb_id, score=coverage, reason="catalog term match")
                )
        return sorted(ranked, key=lambda item: (-item.score, item.kb_id))

    async def probe(
        self,
        query: str,
        scope: ResolvedScope,
        budget: ProbeBudget,
        binding: InferenceBinding,
        *,
        access: AccessScope | None = None,
    ) -> list[ProbeResult]:
        if access is None:
            raise PermissionDenied("probe knowledge base")
        if len(scope.targets) != len({target.kb_id for target in scope.targets}):
            raise ValueError("probe targets must have unique knowledge bases")
        if len(scope.targets) > budget.max_kbs:
            raise ValueError("probe budget is smaller than the pinned targets")
        if any(target.kb_id not in access.kb_ids for target in scope.targets):
            raise PermissionDenied("probe knowledge base")
        terms = _terms(query)

        async def _one(target: PinnedKBTarget) -> ProbeResult:
            search_scope = await self._snapshots.search_scope(target, access)
            if (search_scope.kb_id, search_scope.version_id) != (target.kb_id, target.version_id):
                raise ValueError("snapshot reader changed the pinned target")
            hits = await self._retriever.retrieve(
                query, search_scope, binding, budget.max_chunks_per_kb
            )
            if len(hits) > budget.max_chunks_per_kb:
                raise ValueError("probe exceeded its per-KB chunk budget")
            if any(
                (hit.kb_id, hit.version_id) != (target.kb_id, target.version_id) for hit in hits
            ):
                raise ValueError("probe returned hits outside the pinned snapshot")
            coverage = max((len(terms & _terms(hit.text)) / len(terms) for hit in hits), default=0)
            return ProbeResult(
                kb_id=target.kb_id,
                version_id=target.version_id,
                has_evidence=coverage > 0,
                score=coverage,
            )

        # The complete candidate set shares a single deadline and bounded fanout.
        # A timed-out or failed probe aborts routing rather than becoming no_match.
        async with asyncio.timeout(budget.timeout_ms / 1000):
            outcomes = await asyncio.gather(
                *(_one(target) for target in scope.targets), return_exceptions=True
            )
        failures = [outcome for outcome in outcomes if isinstance(outcome, BaseException)]
        if failures:
            raise failures[0]
        return outcomes

    def decide(
        self,
        ranked: list[RankedKB],
        probes: list[ProbeResult],
        max_kbs: int,
    ) -> SelectionResult:
        if max_kbs < 1:
            raise ValueError("max_kbs must be positive")
        if any(item.failed for item in probes):
            raise ValueError("candidate probe failed; selection cannot proceed")
        scores = {item.kb_id: item.score for item in ranked}
        if len(scores) != len(ranked) or set(scores) != {item.kb_id for item in probes}:
            raise ValueError("probe set differs from the prepared candidates")
        relevant = sorted(
            (item for item in probes if item.has_evidence and item.score > 0),
            key=lambda item: (-item.score, -scores[item.kb_id], item.kb_id),
        )
        if not relevant:
            return SelectionResult(
                status=SelectionStatus.NO_MATCH,
                mode="auto",
                reason="no keyword evidence in authorized candidates",
            )
        if len(relevant) > max_kbs or (
            len(relevant) > 1
            and relevant[0].score == relevant[1].score
            and scores[relevant[0].kb_id] == scores[relevant[1].kb_id]
        ):
            return SelectionResult(
                status=SelectionStatus.NEEDS_CLARIFICATION,
                mode="auto",
                reason="multiple candidate knowledge bases have evidence; narrow the selection",
            )
        return SelectionResult(
            status=SelectionStatus.RESOLVED,
            mode="auto",
            targets=[
                PinnedKBTarget(kb_id=item.kb_id, version_id=item.version_id) for item in relevant
            ],
            reason="catalog match confirmed by keyword evidence",
        )
