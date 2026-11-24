"""Configuration read from environment variables (12-factor style)."""
import os
import secrets


def _bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def load_config():
    return {
        # In production SECRET_KEY must be injected (K8s Secret / Jenkins credential).
        "SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        "DATABASE": os.environ.get(
            "DATABASE_PATH", os.path.join(os.getcwd(), "instance", "aceest.db")
        ),
        "APP_VERSION": os.environ.get("APP_VERSION", "dev"),
        "DEPLOY_COLOR": os.environ.get("DEPLOY_COLOR", "local"),  # blue / green
        "VARIANT": os.environ.get("VARIANT", "A"),  # A/B testing label
        "SHADOW_MODE": _bool("SHADOW_MODE"),  # drop all writes (shadow deployment)
        "CSRF_ENABLED": True,
        "BOOTSTRAP_ADMIN_USER": os.environ.get("ADMIN_USERNAME"),
        "BOOTSTRAP_ADMIN_PASSWORD": os.environ.get("ADMIN_PASSWORD"),
    }
