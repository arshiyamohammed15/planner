from __future__ import annotations

from database.postgresql_setup import Base, get_engine
import database.models  # noqa: F401 - ensure models are imported for metadata


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Tables created.")


if __name__ == "__main__":
    main()

