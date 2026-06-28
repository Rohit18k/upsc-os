import os
import sys

from app.config.settings import get_settings


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
