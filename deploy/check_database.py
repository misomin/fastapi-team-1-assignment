"""Check explicit production settings and DB authentication without printing secrets."""

import os
import sys


def main() -> int:
    required = (
        "DB_DIALECT", "DB_DRIVER", "DB_HOST", "DB_PORT", "DB_USER",
        "DB_PASSWORD", "DB_DATABASE", "ACCESS_TOKEN_SECRET", "REFRESH_TOKEN_SECRET",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if os.environ.get("ENV") != "prod" or missing:
        print("Explicit ENV=prod and all production variables are required. Missing: "
              + ", ".join(missing), file=sys.stderr)
        return 1
    if (os.environ["DB_DIALECT"] != "mysql"
            or os.environ["DB_DRIVER"] != "pymysql"
            or not os.environ["DB_HOST"].endswith(".rds.amazonaws.com")):
        print("Production DB must use the configured RDS MySQL endpoint.", file=sys.stderr)
        return 1
    try:
        from sqlalchemy import create_engine, text
        from wapang.database.settings import DB_SETTINGS

        engine = create_engine(DB_SETTINGS.url, connect_args={"connect_timeout": 5})
        try:
            with engine.connect() as connection:
                assert connection.scalar(text("SELECT 1")) == 1
        finally:
            engine.dispose()
    except Exception as error:
        # Full exceptions can contain connection details and settings values.
        print(f"Production DB check failed ({type(error).__name__}).", file=sys.stderr)
        return 1
    print("Production DB authentication and SELECT 1 succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
