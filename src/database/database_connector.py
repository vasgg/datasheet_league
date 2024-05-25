from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class DatabaseConnector:
    def __init__(self, url: str, echo: bool = False) -> None:
        self.engine = create_async_engine(url=url, echo=echo)
        self.session_factory = async_sessionmaker(
            bind=self.engine, expire_on_commit=False, autocommit=False, autoflush=False,
        )
