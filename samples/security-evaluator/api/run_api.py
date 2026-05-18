"""Entry script to run the security-evaluator FastAPI service with HTTP/HTTPS support."""

from __future__ import annotations

import os

import uvicorn


def _as_bool(*, value: str) -> bool:
    """Parse boolean-like environment variable text.

    Args:
        value (str): Raw env text.

    Returns:
        bool: Parsed bool.
    """

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> None:
    """Run uvicorn server for the API app.

    Environment variables:
        API_HOST: Bind host. Defaults to 0.0.0.0.
        API_PORT: Bind port. Defaults to 8088.
        API_RELOAD: Auto-reload for development. Defaults to false.
        API_SSL_CERTFILE: Optional HTTPS certificate path.
        API_SSL_KEYFILE: Optional HTTPS private key path.
    """

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8088"))
    reload_enabled = _as_bool(value=os.getenv("API_RELOAD", "false"))
    ssl_certfile = os.getenv("API_SSL_CERTFILE")
    ssl_keyfile = os.getenv("API_SSL_KEYFILE")

    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=reload_enabled,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )


if __name__ == "__main__":
    main()
