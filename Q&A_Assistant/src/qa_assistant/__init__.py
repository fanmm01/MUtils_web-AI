"""Transport-agnostic Q&A core scaffold."""

from .context import ContextBuilder
from .events import AnswerEventSequenceValidator, EventSequenceError
from .evidence import EvidenceGuard
from .generation import GroundedGenerator, SentenceBuffer
from .model_binding import InferenceBindingValidator
from .retrieval import FederatedRetriever, HybridRetriever
from .routing import KnowledgeRouter
from .service import QAService

__all__ = [
    "AnswerEventSequenceValidator",
    "ContextBuilder",
    "EvidenceGuard",
    "EventSequenceError",
    "FederatedRetriever",
    "GroundedGenerator",
    "HybridRetriever",
    "InferenceBindingValidator",
    "KnowledgeRouter",
    "QAService",
    "SentenceBuffer",
]
