"""Command line utility for querying Logitech Harmony devices."""

import asyncio
import json
import logging
import sys

import click
import click_log

from .auth import login
from .client import HarmonyClient

log = logging.getLogger(__name__)


@click.group()
@click.option('--email', required=True, help='Logitech username in the form of an email address.')
@click.option('--password', required=True, help='Logitech password')
@click.option('--hostname', required=True, help='Hostname or IP Address of the Harmony device.')
@click.option('--port', default=5222, type=int, help='Network port that the Harmony is listening on.')
@click_log.simple_verbosity_option()
@click_log.init(__name__)
@click.pass_context
def cli(ctx, email, password, hostname, port):
    ctx.obj = {
        'email': email,
        'password': password,
        'hostname': hostname,
        'port': port,
    }


@cli.command()
@click.pass_context
def show_config(ctx):
    """Connects to the Harmony and prints its configuration."""

    token = login(**ctx.obj)
    client = HarmonyClient(ctx.obj['hostname'], ctx.obj['port'], token)

    tasks = asyncio.gather(*[client.get_config()])
    client.loop.run_until_complete(tasks)
    client.disconnect()

    print(json.dumps(next(iter(tasks.result())), indent=2))

    sys.exit(0)
