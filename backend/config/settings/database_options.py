import environ


def postgresql_options(env: environ.Env) -> dict[str, int]:
    # Without these, libpq keeps the kernel defaults and a dead peer is noticed only after about 2 hours.
    return {
        "keepalives": 1,
        "keepalives_idle": env.int("DATABASE_KEEPALIVES_IDLE", 30),
        "keepalives_interval": env.int("DATABASE_KEEPALIVES_INTERVAL", 10),
        "keepalives_count": env.int("DATABASE_KEEPALIVES_COUNT", 3),
        "tcp_user_timeout": env.int("DATABASE_TCP_USER_TIMEOUT_MS", 60000),
    }
