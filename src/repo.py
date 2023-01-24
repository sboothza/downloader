import re
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, or_
from sqlalchemy.orm import Session, declarative_base

from config import Config
from utils import get_property, build_regex_dict, dump_props

Base = declarative_base()


class Downloadable:
    pass


class Downloadable(Base):
    __tablename__ = "downloadable"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=True)
    title = Column(String, nullable=True)
    audio_only = Column(Boolean, nullable=True)
    status = Column(String, nullable=True)
    errors = Column(String, nullable=True)
    retry_count = Column(Integer, nullable=True)
    filename = Column(String, nullable=True)
    create_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    length = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    callback = Column(String, nullable=True)

    def __init__(self, url: str = "", title: str = "", audio_only: bool = False, status: str = "",
                 errors: str = "", retry_count: int = 0, filename: str = "", create_date: datetime = datetime.min,
                 expiry_date: datetime = datetime.min, width: int = 0, height: int = 0, length: int = 0,
                 file_size: int = 0, callback: str = ""):
        self.url = url
        self.title = title
        self.audio_only = audio_only
        self.status = status
        self.errors = errors
        self.retry_count = retry_count
        self.filename = filename
        self.create_date = create_date
        self.expiry_date = expiry_date
        self.width = width
        self.height = height
        self.length = length
        self.file_size = file_size
        self.callback = callback

    def clone_to(self, target) -> Downloadable:
        for key, value in self.__dict__.items():
            if not key.startswith("_") and hasattr(target, key):
                try:
                    setattr(target, key, value)
                except:
                    pass
        return target

    def build_callback_info(self, config: Config) -> dict:
        callback_content = self.callback
        regex = r"<%(.+?)%>"
        match = re.search(regex, callback_content)
        # for match in matches:
        while match is not None:
            name = match.group(1)
            print(name)
            found, value = get_property(config, name)
            if not found:
                found, value = get_property(self, name)

            if found:
                callback_content = callback_content.replace("<%{}%>".format(name), value)

            match = re.search(regex, callback_content)

        callback_values = build_regex_dict(callback_content, r"<(([^:]+):([^:]*))>")

        return callback_values

    def __str__(self):
        return "Downloadable:\n\t" + dump_props(self, "\n\t")


class Repository:
    def __init__(self, config: Config):
        self.engine = create_engine(config.db_file, echo=False)

    def db_exists(self) -> bool:
        try:
            with (Session(self.engine) as session):
                return session.query(Downloadable.id).count() >= 0
        except:
            return False

    def create_db_if_not_exist(self) -> None:
        if not self.db_exists():
            Base.metadata.create_all(self.engine)

    def count(self):
        with (Session(self.engine) as session):
            return session.query(Downloadable.id).count()

    def count_done(self):
        with (Session(self.engine) as session):
            return session.query(Downloadable.id) \
                .filter(or_(Downloadable.status == "completed", Downloadable.status == "deleted")) \
                .count()

    def count_waiting(self):
        with (Session(self.engine) as session):
            return session.query(Downloadable.id) \
                .filter(Downloadable.status == "queued") \
                .count()

    def get_next_queue_item(self) -> Optional[Downloadable]:
        with (Session(self.engine) as session):
            result = session.query(Downloadable) \
                .filter(or_(Downloadable.status == "queued", Downloadable.status == "downloaded")) \
                .order_by(Downloadable.create_date)

            return result.first()

    def get_by_id(self, id: int) -> Optional[Downloadable]:
        with (Session(self.engine) as session):
            result = session.query(Downloadable) \
                .filter(Downloadable.id == id) \
                .filter(Downloadable.status == "completed")

            return result.first()

    def update_item(self, item: Downloadable) -> None:
        with (Session(self.engine) as session):
            result = session.query(Downloadable) \
                .filter(Downloadable.id == item.id)

            old_item: Downloadable = result.first()
            old_item = item.clone_to(old_item)
            session.commit()

    def add(self, item: Downloadable) -> bool:
        with (Session(self.engine) as session):
            try:
                session.add(item)
                session.commit()
                session.expunge_all()
                return True
            except Exception as e:
                if 'UNIQUE constraint failed' in str(e):
                    return False
                else:
                    raise e

    def get_expired_items(self):
        with (Session(self.engine) as session):
            result = session.query(Downloadable) \
                .filter(Downloadable.status == "completed") \
                .filter(Downloadable.expiry_date < datetime.now())

            return result.all()

    def flag_deleted(self, id: int):
        with (Session(self.engine) as session):
            result = session.query(Downloadable) \
                .filter(Downloadable.id == id)

            old_item: Downloadable = result.first()
            old_item.status = "deleted"
            session.commit()

    def reset_in_progress(self):
        with (Session(self.engine) as session):
            result = session.query(Downloadable) \
                .filter(Downloadable.status == "in_progress")

            for item in result.all():
                item.status = "queued"

            session.commit()

