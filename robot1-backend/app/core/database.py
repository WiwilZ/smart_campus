import os
from collections.abc import Generator
from sqlmodel import SQLModel, create_engine, Session

# DB 文件固定指向 main-backend 下的 smart_campus.db
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "main-backend", "smart_campus.db")
sqlite_url = f"sqlite:///{DB_FILE}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
