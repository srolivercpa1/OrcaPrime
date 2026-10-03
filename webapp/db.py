import time
import uuid
from sqlalchemy import create_engine, String, Text, Integer, Boolean, ForeignKey, JSON, LargeBinary, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def uid(): return uuid.uuid4().hex
class Base(DeclarativeBase): pass
class Company(Base):
    __tablename__='web_companies'
    id: Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
    name: Mapped[str]=mapped_column(String(160))
    active: Mapped[bool]=mapped_column(Boolean,default=True)
    expires: Mapped[int]=mapped_column(Integer)
    settings: Mapped[dict]=mapped_column(JSON,default=dict)
class User(Base):
    __tablename__='web_users'
    id: Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
    company_id: Mapped[str|None]=mapped_column(ForeignKey('web_companies.id'),nullable=True,index=True)
    email: Mapped[str]=mapped_column(String(254),unique=True)
    name: Mapped[str]=mapped_column(String(160))
    password: Mapped[str]=mapped_column(Text)
    role: Mapped[str]=mapped_column(String(20))
    active: Mapped[bool]=mapped_column(Boolean,default=True)
class Session(Base):
    __tablename__='web_sessions'
    id: Mapped[str]=mapped_column(String(64),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('web_users.id'),index=True)
    csrf: Mapped[str]=mapped_column(String(64))
    expires: Mapped[int]=mapped_column(Integer)
class Record(Base):
    __tablename__='web_records'
    id: Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
    company_id: Mapped[str]=mapped_column(ForeignKey('web_companies.id'),index=True)
    kind: Mapped[str]=mapped_column(String(20),index=True)
    data: Mapped[dict]=mapped_column(JSON)
    created: Mapped[int]=mapped_column(Integer,default=lambda:int(time.time()))
class Photo(Base):
    __tablename__='web_photos'
    id: Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
    company_id: Mapped[str]=mapped_column(ForeignKey('web_companies.id'),index=True)
    order_id: Mapped[str]=mapped_column(String(32),index=True)
    content: Mapped[bytes]=mapped_column(LargeBinary)
    name: Mapped[str]=mapped_column(String(160))
class Audit(Base):
    __tablename__='web_audit'
    id: Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
    company_id: Mapped[str|None]=mapped_column(String(32),nullable=True,index=True)
    actor: Mapped[str]=mapped_column(String(32))
    action: Mapped[str]=mapped_column(String(80))
    target: Mapped[str]=mapped_column(String(32))
    at: Mapped[int]=mapped_column(Integer,default=lambda:int(time.time()))

def database(url):
    engine=create_engine(url,**({'connect_args':{'check_same_thread':False,'timeout':30}} if url.startswith('sqlite') else {'pool_pre_ping':True}))
    if url.startswith('sqlite'):
        @event.listens_for(engine,'connect')
        def sqlite_setup(conn,record):
            conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    return engine,sessionmaker(engine,expire_on_commit=False)
