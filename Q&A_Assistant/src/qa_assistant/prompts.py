"""Prompt construction placeholders."""

from qa_contracts.errors import FeatureNotImplemented


def build_rewrite_prompt(question: str, turns: list[object]) -> str:
    raise FeatureNotImplemented("rewrite prompt construction")


def build_grounded_prompt(context: object) -> str:
    raise FeatureNotImplemented("grounded generation prompt construction")


def build_support_prompt(sentence: object, evidence: list[object]) -> str:
    raise FeatureNotImplemented("support-check prompt construction")
