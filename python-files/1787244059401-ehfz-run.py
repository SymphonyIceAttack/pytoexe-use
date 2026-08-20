"""Verify all modules import and optionally start the server."""
from __future__ import annotations

import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def verify_compile() -> bool:
    ok = compileall.compile_dir(str(ROOT / "backend"), quiet=1)
    compileall.compile_dir(str(ROOT / "tests"), quiet=1)
    return bool(ok)


def verify_import() -> str:
    from backend.api.app import app  # noqa: F401
    return app.title


if __name__ == "__main__":
    print("Compiling Python files...")
    if not verify_compile():
        print("COMPILE FAILED")
        sys.exit(1)
    print("Compile OK")

    print("Importing app...")
    title = verify_import()
    print(f"Import OK: {title}")

    if "--serve" in sys.argv:
        import uvicorn
        from backend.config import SERVER_CONFIG

        print(f"Starting server on http://127.0.0.1:{SERVER_CONFIG.PORT}")
        uvicorn.run(
            "backend.api.app:app",
            host="127.0.0.1",
            port=SERVER_CONFIG.PORT,
            reload=False,
        )
