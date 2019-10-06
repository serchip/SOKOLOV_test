import logging

from aiohttp import web
import aioredis
from aiohttp_swagger import setup_swagger

from api.db import init_db
from api.routes import setup_routes

from settings import load_config, PACKAGE_NAME


log = logging.getLogger(__name__)


async def setup_redis(app):

    pool = await aioredis.create_redis_pool((
        app['config']['redis']['REDIS_HOST'],
        app['config']['redis']['REDIS_PORT']
    ))

    async def close_redis(app):
        pool.close()
        await pool.wait_closed()

    app.on_cleanup.append(close_redis)
    app['redis_pool'] = pool
    return pool


async def init_app(config):

    app = web.Application()

    app['config'] = config

    setup_routes(app)
    setup_swagger(app)

    db_pool = await init_db(app)

    redis_pool = await setup_redis(app)

    # needs to be after session setup because of `current_user_ctx_processor`

    log.debug(app['config'])

    return app


def main(configpath):
    config = load_config(configpath)
    logging.basicConfig(level=logging.DEBUG)
    app = init_app(config)
    web.run_app(app)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Provide path to config file")
    args = parser.parse_args()

    if args.config:
        main(args.config)
    else:
        parser.print_help()
