from sqlalchemy import MetaData

from api.db import construct_db_url, get_engine
from api.db import Users, Message
from api.security import generate_password_hash
from settings import load_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def get_session(f):
    def wrapper(*args, **kwargs):
        target_config = kwargs.get('target_config')
        if target_config:
            engine = get_engine(target_config)
            session = sessionmaker(bind=engine)()
            kwargs['session'] = session
        return f(*args, **kwargs)
    return wrapper

def setup_db(executor_config=None, target_config=None):
    engine = get_engine(executor_config)

    db_name = target_config['DB_NAME']
    db_user = target_config['DB_USER']
    db_pass = target_config['DB_PASS']

    with engine.connect() as conn:
        teardown_db(executor_config=executor_config,
                    target_config=target_config)

        conn.execute("CREATE USER %s WITH PASSWORD '%s'" % (db_user, db_pass))
        conn.execute("CREATE DATABASE %s" % db_name)
        conn.execute("GRANT ALL PRIVILEGES ON DATABASE %s TO %s" %
                     (db_name, db_user))


def teardown_db(executor_config=None, target_config=None):
    engine = get_engine(executor_config)

    db_name = target_config['DB_NAME']
    db_user = target_config['DB_USER']

    with engine.connect() as conn:
        # terminate all connections to be able to drop database
        conn.execute("""
          SELECT pg_terminate_backend(pg_stat_activity.pid)
          FROM pg_stat_activity
          WHERE pg_stat_activity.datname = '%s'
            AND pid <> pg_backend_pid();""" % db_name)
        conn.execute("DROP DATABASE IF EXISTS %s" % db_name)
        conn.execute("DROP ROLE IF EXISTS %s" % db_user)

def create_tables(target_config=None):
    engine = get_engine(target_config)
    meta = MetaData()
    meta.create_all(bind=engine, tables=[Users.__table__, Message.__table__])


def drop_tables(target_config=None):
    engine = get_engine(target_config)
    Base.metadata.drop_all(engine)
    meta = MetaData()
    meta.drop_all(bind=engine, tables=[Users.__table__, Message.__table__])


def create_sample_data(target_config=None):
    engine = get_engine(target_config)
    session = sessionmaker(bind=engine)()
    session.add(Users(username='Adam', email='adam@one.com',
                      password_hash=generate_password_hash('adam')
                      )
                )
    session.add(Users(username='user2', email='user2@one.com',
                      password_hash=generate_password_hash('user2')
                      )
                )
    session.add(Users(username='user3', email='user3@one.com',
                      password_hash=generate_password_hash('user3')
                      )
                )
    session.commit()

if __name__ == '__main__':
    user_db_config = load_config('deployment/config/user_config.toml')['database']
    admin_db_config = load_config('deployment/config/admin_config.toml')['database']

    import argparse
    parser = argparse.ArgumentParser(description='DB related shortcuts')
    parser.add_argument("-c", "--create",
                        help="Create empty database and user with permissions",
                        action='store_true')
    parser.add_argument("-d", "--drop",
                        help="Drop database and user role",
                        action='store_true')
    parser.add_argument("-r", "--recreate",
                        help="Drop and recreate database and user",
                        action='store_true')
    parser.add_argument("-a", "--all",
                        help="Create sample data",
                        action='store_true')
    args = parser.parse_args()

    if args.create:
        setup_db(executor_config=admin_db_config,
                 target_config=user_db_config)
    elif args.drop:
        teardown_db(executor_config=admin_db_config,
                    target_config=user_db_config)
    elif args.recreate:
        teardown_db(executor_config=admin_db_config,
                    target_config=user_db_config)
        setup_db(executor_config=admin_db_config,
                 target_config=user_db_config)
    elif args.all:
        teardown_db(executor_config=admin_db_config,
                    target_config=user_db_config)
        setup_db(executor_config=admin_db_config,
                 target_config=user_db_config)
        create_tables(target_config=user_db_config)
        create_sample_data(target_config=user_db_config)
    else:
        parser.print_help()
