import os
import sys

from app.config.settings import get_settings

# Known-bad default secrets that must never be used in production
_KNOWN_BAD_SECRETS = {
    "change-this-to-a-random-secret-key-at-least-32-chars",
    "change-this-to-a-random-encryption-key-32-characters",
    "change-this-password",
    "change-this-minio-secret",
    "secret",
    "password",
    "changeme",
}


class EnvironmentValidator:
    REQUIRED_VARS = [
        "SECRET_KEY",
        "ENCRYPTION_KEY",
        "POSTGRES_PASSWORD",
        "MINIO_SECRET_KEY",
    ]

    @classmethod
    def validate(cls) -> None:
        settings = get_settings()
        missing = []

        for var in cls.REQUIRED_VARS:
            value = getattr(settings, var, None)
            if not value or (isinstance(value, str) and value.startswith("${")):
                missing.append(var)

        if "production" in settings.ENVIRONMENT and missing:
            print(f"FATAL: Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)

        if settings.ENVIRONMENT == "production":
            if settings.DEBUG:
                print("FATAL: DEBUG must be False in production", file=sys.stderr)
                sys.exit(1)
            if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
                print("FATAL: SECRET_KEY must be at least 32 characters in production", file=sys.stderr)
                sys.exit(1)

            # Reject known-bad default secrets
            for var in cls.REQUIRED_VARS:
                value = getattr(settings, var, "")
                if isinstance(value, str) and value.lower().strip() in _KNOWN_BAD_SECRETS:
                    print(
                        f"FATAL: {var} is set to a known default value. "
                        f"Generate a secure random value before deploying to production.",
                        file=sys.stderr,
                    )
                    sys.exit(1)

            # Validate CORS origins are not wildcard in production
            if "*" in settings.CORS_ORIGINS:
                print("FATAL: CORS_ORIGINS must not contain '*' in production", file=sys.stderr)
                sys.exit(1)

            # Validate allowed hosts are not wildcard in production
            if "*" in settings.ALLOWED_HOSTS or "0.0.0.0" in settings.ALLOWED_HOSTS:
                print("FATAL: ALLOWED_HOSTS must not contain '*' or '0.0.0.0' in production", file=sys.stderr)
                sys.exit(1)

    @classmethod
    def validate_env_file(cls, env_path: str = ".env") -> bool:
        if not os.path.exists(env_path):
            return False
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key in cls.REQUIRED_VARS and (not value or value.startswith("${")):
                        return False
        return True
