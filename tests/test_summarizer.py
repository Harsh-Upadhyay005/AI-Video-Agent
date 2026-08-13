import builtins
import importlib
import sys


def test_summarizer_falls_back_when_optional_llm_dependency_is_missing(monkeypatch):
    sys.modules.pop("core.summarizer", None)

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "langchain_mistralai" or name.startswith("langchain_mistralai"):
            raise ImportError("simulated missing dependency")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = importlib.import_module("core.summarizer")

    assert module.summarize("A short transcript") == "A short transcript"
    assert module.generate_title("A short transcript") == "A short transcript"
