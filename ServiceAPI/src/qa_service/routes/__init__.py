"""Route package: every handler validates input, then delegates to a service.

In P1 the services are placeholders and raise ``FeatureNotImplemented``, which
the error layer maps to 501. No handler contains business rules.
"""
