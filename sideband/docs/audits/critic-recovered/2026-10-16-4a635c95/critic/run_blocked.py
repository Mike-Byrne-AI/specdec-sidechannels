import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "src")
mode = sys.argv[1]
if mode == "blocked":
    sys.modules["torch"] = None          # find_spec -> None, import -> ImportError
elif mode == "dummy":
    import types
    sys.modules["torch"] = types.ModuleType("torch")
import pytest
args = ["-q", "-p", "no:cacheprovider", "-rs", "-o", "pythonpath=src"] + sys.argv[2:]
sys.exit(pytest.main(args))
