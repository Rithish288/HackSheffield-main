import importlib
import os
import sys


def test_app_starts_without_openai_key(monkeypatch):
    """Ensure importing the app does not raise when OPENAI_API_KEY is missing
    and the `client` is set to None.
    """
    # Ensure the environment var is not present
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Force re-import so we get a fresh module state
    if "ReplyChallenge.main" in sys.modules:
        del sys.modules["ReplyChallenge.main"]

    main = importlib.import_module("ReplyChallenge.main")

    # The module should define 'client' and it should be None when the key is absent
    assert hasattr(main, "client")
    assert main.client is None
