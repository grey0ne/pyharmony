"""Command line utility for querying Logitech Harmony devices."""

import logging
import pprint
import sys

import click
import click_log

from .auth import login
from .client import create_and_connect_client


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
    client = create_and_connect_client(ctx.obj['hostname'], ctx.obj['port'], token)
    pprint.pprint(client.get_config())
    client.disconnect()

    sys.exit(0)
