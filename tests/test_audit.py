from src.common.audit import log_audit


def test_log_audit_signature():
    import inspect
    sig = inspect.signature(log_audit)
    params = list(sig.parameters.keys())
    assert "db" in params
    assert "action" in params
    assert "entity_type" in params
    assert "entity_id" in params
    assert log_audit.__doc__ is None  # no unnecessary docstrings
