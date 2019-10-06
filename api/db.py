import datetime

import asyncpgsa
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Boolean, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.sql import select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def construct_db_url(config):
    DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"
    return DSN.format(
        user=config['DB_USER'],
        password=config['DB_PASS'],
        database=config['DB_NAME'],
        host=config['DB_HOST'],
        port=config['DB_PORT'],
    )

def get_engine(db_config):
    db_url = construct_db_url(db_config)
    engine = create_engine(db_url, isolation_level='AUTOCOMMIT')
    return engine

def datatime_format(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return o

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, unique=True)
    email = Column(String(120))
    password_hash = Column(String(128), nullable=False)

class Message(Base):
    __tablename__ = 'messages'
    INBOX = 0
    SENT = 1
    TYPE_CHOICES = (
        (INBOX, "Входящие"),
        (SENT, "Исходящие"),
    )

    id = Column(Integer, primary_key=True)
    body = Column(String(1500))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    read = Column(Boolean, index=True, default=False)
    type = Column(Integer, default=INBOX)
    from_user_id = Column(Integer, ForeignKey('users.id'))
    to_user_id = Column(Integer, ForeignKey('users.id'))

    def as_dict(self):
        return {c.name: datatime_format(getattr(self, c.name)) for c in self.__table__.columns}


async def init_db(app):
    dsn = construct_db_url(app['config']['database'])
    pool = await asyncpgsa.create_pool(dsn=dsn)
    app['db_pool'] = pool
    Session = sessionmaker(bind=get_engine(app['config']['database']))
    session = scoped_session(Session)
    app['db_session'] = session
    return pool


async def get_user_by_id(conn, id):
    result = await conn.fetchrow(
        Users
        .select()
        .where(Users.c.id == int(id))
    )
    return result


async def get_users_by_in(conn, ids):
    records = await conn.fetch(
            Users.select()
            .where(Users.c.id.in_(set(ids)))
            .order_by(Users.c.id)
        )
    return records


async def get_messages_with_user(conn, to_user_id):
    records = await conn.fetch(
        Message.select().where(Users.c.id == int(id)).order_by(Message.c.id)
    )
    return records


async def get_posts_with_joined_users(conn):
    j = posts.join(users, posts.c.user_id == users.c.id)
    stmt = select(
        [posts, users.c.username]).select_from(j).order_by(posts.c.timestamp)
    records = await conn.fetch(stmt)
    return records


async def create_message(conn, mes_body, from_user_id, to_user_id, catalog_type):
    stmt = message.insert().values(body=mes_body, user_id=from_user_id)
    await conn.execute(stmt)
