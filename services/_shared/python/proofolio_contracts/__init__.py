"""Pydantic models generated from contracts/schemas (KAN-7).

    from proofolio_contracts import CvExtractRequested, ErrorCode
    event = CvExtractRequested.model_validate_json(message_body)

Field names stay camelCase, exactly as on the wire. The models are for typing and parsing;
the JSON Schemas in contracts/schemas remain the full check (Pydantic cannot express every
rule, for example the "must end in Z" pattern on timestamps).

models.py is generated: never edit it, run `make contracts-types` instead.
"""

from pydantic import ValidationError

from . import models as _models
from .models import *  # noqa: F401,F403

# Export only the classes defined by the generated module (not pydantic's own names).
__all__ = ["ValidationError"] + sorted(
    name
    for name, obj in vars(_models).items()
    if isinstance(obj, type) and obj.__module__ == _models.__name__ and name != "ProofolioContracts"
)
