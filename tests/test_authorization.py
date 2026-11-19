from pathlib import Path

import pytest

from autoqa.authorization import AuthorizationContext, require_authorization


def test_authorization_is_explicit_project_and_operation_bound(tmp_path: Path):
    context = AuthorizationContext(tmp_path, frozenset({"plan"}))
    require_authorization(context, tmp_path, "plan")
    with pytest.raises(ValueError, match="Explicit"):
        require_authorization(None, tmp_path, "plan")
    with pytest.raises(ValueError, match="Explicit"):
        require_authorization(context, tmp_path / "other", "plan")
    with pytest.raises(ValueError, match="Explicit"):
        require_authorization(context, tmp_path, "review")
