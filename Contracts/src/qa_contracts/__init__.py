"""Public contract surface.

``import qa_contracts`` must stay side-effect free: no database, no network, no
model loading, no FastAPI import.
"""

from __future__ import annotations

from .base import ID, SCHEMA_VERSION, ContractModel, Page, utc_now
from .errors import (
    STATUS_BY_CODE,
    APIError,
    APIErrorResponse,
    Conflict,
    ErrorBody,
    ErrorCode,
    ErrorDetail,
    EvidenceInsufficient,
    FeatureNotImplemented,
    InferencePolicyViolation,
    ModelCapabilityMissing,
    ModelChanged,
    ModelUnavailable,
    NotFound,
    PermissionDenied,
    ProviderUnavailable,
    ResourceGone,
    ValidationFailed,
)

__all__ = [
    "APIError",
    "APIErrorResponse",
    "Conflict",
    "ContractModel",
    "ErrorBody",
    "ErrorCode",
    "ErrorDetail",
    "EvidenceInsufficient",
    "FeatureNotImplemented",
    "ID",
    "InferencePolicyViolation",
    "ModelCapabilityMissing",
    "ModelChanged",
    "ModelUnavailable",
    "NotFound",
    "Page",
    "PermissionDenied",
    "ProviderUnavailable",
    "ResourceGone",
    "SCHEMA_VERSION",
    "STATUS_BY_CODE",
    "ValidationFailed",
    "utc_now",
]
