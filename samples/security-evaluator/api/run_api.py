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
        API_HOST: Bind host. Defaults to 127.0.0.1.
        API_PORT: Bind port. Defaults to 8088.
        API_ALLOW_REMOTE_HOST: Allow non-local bind host when true. Defaults to false.
        API_AUTH_ENABLED: Enable bearer token auth for /api/v1/* endpoints. Defaults to false.
        API_BEARER_TOKEN: Required only when API_AUTH_ENABLED is true.
        API_RELOAD: Auto-reload for development. Defaults to false.
        API_SSL_CERTFILE: Optional HTTPS certificate path.
        API_SSL_KEYFILE: Optional HTTPS private key path.
    """

    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8088"))
    allow_remote_host = _as_bool(value=os.getenv("API_ALLOW_REMOTE_HOST", "false"))
    auth_enabled = _as_bool(value=os.getenv("API_AUTH_ENABLED", "false"))
    bearer_token = os.getenv("API_BEARER_TOKEN", "")
    reload_enabled = _as_bool(value=os.getenv("API_RELOAD", "false"))
    ssl_certfile = os.getenv("API_SSL_CERTFILE")
    ssl_keyfile = os.getenv("API_SSL_KEYFILE")

    normalized_host = host.strip().lower()
    is_local_host = normalized_host in {"127.0.0.1", "localhost", "::1"}
    if not is_local_host and not allow_remote_host:
        raise ValueError(
            "Refusing non-local API_HOST. Set API_ALLOW_REMOTE_HOST=true if remote binding is intentional."
        )

    if auth_enabled and not bearer_token:
        raise ValueError("API_AUTH_ENABLED=true requires API_BEARER_TOKEN to be set.")

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
