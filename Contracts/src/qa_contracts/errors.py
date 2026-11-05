"""Stable error codes and domain exceptions shared by API, SDK and CLI.

The HTTP mapping is deliberate: clients only branch on ``code``, never on a
provider-specific message. Messages must not leak credentials, local paths or
stack traces.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from .base import ContractModel


class ErrorCode(StrEnum):
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    GONE = "GONE"
    RATE_LIMITED = "RATE_LIMITED"
    FEATURE_NOT_IMPLEMENTED = "FEATURE_NOT_IMPLEMENTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    EVIDENCE_INSUFFICIENT = "EVIDENCE_INSUFFICIENT"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_CHANGED = "MODEL_CHANGED"
    MODEL_CAPABILITY_MISSING = "MODEL_CAPABILITY_MISSING"
    INFERENCE_POLICY_VIOLATION = "INFERENCE_POLICY_VIOLATION"
    INTERNAL_ERROR = "INTERNAL_ERROR"


STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_FAILED: 422,
    ErrorCode.UNAUTHENTICATED: 401,
    ErrorCode.PERMISSION_DENIED: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.GONE: 410,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.FEATURE_NOT_IMPLEMENTED: 501,
    ErrorCode.PROVIDER_UNAVAILABLE: 503,
    ErrorCode.EVIDENCE_INSUFFICIENT: 200,
    ErrorCode.MODEL_UNAVAILABLE: 503,
    ErrorCode.MODEL_CHANGED: 409,
    ErrorCode.MODEL_CAPABILITY_MISSING: 503,
    ErrorCode.INFERENCE_POLICY_VIOLATION: 403,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ErrorDetail(ContractModel):
    field: str | None = None
    reason: str = Field(min_length=1)


class ErrorBody(ContractModel):
    code: ErrorCode
    message: str = Field(min_length=1)
    details: list[ErrorDetail] = Field(default_factory=list)


class APIErrorResponse(ContractModel):
    error: ErrorBody
    request_id: str


class APIError(Exception):
    """Base domain error carrying a stable code and safe public details."""

    code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str, details: list[ErrorDetail] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []

    @property
    def status_code(self) -> int:
        return STATUS_BY_CODE[self.code]

    def body(self, request_id: str) -> dict[str, object]:
        return APIErrorResponse(
            error=ErrorBody(code=self.code, message=self.message, details=self.details),
            request_id=request_id,
        ).model_dump(mode="json")


class FeatureNotImplemented(APIError):
    code = ErrorCode.FEATURE_NOT_IMPLEMENTED

    def __init__(self, feature: str) -> None:
        super().__init__(f"'{feature}' is not implemented in the scaffold build")
        self.feature = feature


class ValidationFailed(APIError):
    code = ErrorCode.VALIDATION_FAILED

    def __init__(self, details: list[ErrorDetail] | None = None) -> None:
        super().__init__("request validation failed", details)


class NotFound(APIError):
    code = ErrorCode.NOT_FOUND

    def __init__(self, resource: str) -> None:
        super().__init__(f"{resource} was not found")
        self.resource = resource


class Conflict(APIError):
    code = ErrorCode.CONFLICT

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"expected {expected}, actual {actual}")
        self.expected = expected
        self.actual = actual


class PermissionDenied(APIError):
    code = ErrorCode.PERMISSION_DENIED

    def __init__(self, action: str) -> None:
        super().__init__(f"permission denied for {action}")
        self.action = action


class ProviderUnavailable(APIError):
    code = ErrorCode.PROVIDER_UNAVAILABLE

    def __init__(self, reason: str) -> None:
        super().__init__(f"required provider is unavailable: {reason}")
        self.reason = reason


class EvidenceInsufficient(APIError):
    code = ErrorCode.EVIDENCE_INSUFFICIENT

    def __init__(self, reason: str) -> None:
        super().__init__(f"evidence is insufficient: {reason}")
        self.reason = reason


class ModelUnavailable(APIError):
    code = ErrorCode.MODEL_UNAVAILABLE

    def __init__(self, model_id: str, reason: str) -> None:
        super().__init__(f"model {model_id} is unavailable: {reason}")
        self.model_id = model_id
        self.reason = reason


class ModelChanged(APIError):
    code = ErrorCode.MODEL_CHANGED

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"model identity changed: expected {expected}, actual {actual}")
        self.expected = expected
        self.actual = actual


class InferencePolicyViolation(APIError):
    code = ErrorCode.INFERENCE_POLICY_VIOLATION

    def __init__(self, role: str) -> None:
        super().__init__(f"inference policy is violated for role {role}")
        self.role = role


class ModelCapabilityMissing(APIError):
    code = ErrorCode.MODEL_CAPABILITY_MISSING

    def __init__(self, role: str) -> None:
        super().__init__(f"no verified model is bound for role {role}")
        self.role = role


class ResourceGone(APIError):
    code = ErrorCode.GONE

    def __init__(self, resource: str) -> None:
        super().__init__(f"{resource} has been purged")
        self.resource = resource
