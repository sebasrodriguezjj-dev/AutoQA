"""Explicit, project-bound authorization for side-effecting application operations.

This context records the operator's intent; it is not an authentication system.
Network scope and case approval remain separate mandatory checks.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Operation = Literal["plan", "review", "generate", "execute", "discover"]


@dataclass(frozen=True)
class AuthorizationContext:
    project_root: Path
    operations: frozenset[Operation]

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_root", self.project_root.resolve())
        object.__setattr__(self, "operations", frozenset(self.operations))


def require_authorization(
    context: AuthorizationContext | None, project_root: Path, operation: Operation
) -> None:
    """Reject missing, mismatched, or insufficient authorization before side effects."""
    if (
        not isinstance(context, AuthorizationContext)
        or context.project_root != project_root.resolve()
        or operation not in context.operations
    ):
        raise ValueError(f"Explicit {operation} authorization is required for this project.")
