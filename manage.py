import click

from settings import BACKEND_HOST, BACKEND_PORT
import uvicorn
import logging
from app.main import app

logger = logging.getLogger(__name__)


@click.group()
def group():
    pass


@group.command()
def run():
    logger.debug(f"starting server")
    uvicorn.run(app, host=BACKEND_HOST, port=int(BACKEND_PORT), log_level="info")
    logger.debug("shutting down")


if __name__ == "__main__":
    group()
