"""Command line utility for querying the Logitech Harmony."""

import argparse
import logging
import json
import sys

from pyharmony.client import HarmonyClient, HarmonyException

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

logging.getLogger('sleekxmpp').setLevel(logging.CRITICAL)
logging.getLogger('pyharmony').setLevel(logging.CRITICAL)


def harmony_command(func):
    def decorated(args):
        try:
            client = get_client(args)
        except HarmonyException:
            print 'Error in client initialization'
            return 1

        try:
            return func(client, args)
        except HarmonyException:
            print 'Error in command execution'
            return 1
        finally:
            client.disconnect(send_close=True)

    return decorated


def pprint(obj):
    """Pretty JSON dump of an object."""
    print(json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': ')))


def get_client(args):
    return HarmonyClient(args.hostname, args.port)


@harmony_command
def show_config(client, args):
    pprint(client.get_config())


@harmony_command
def show_current_activity(client, args):
    current_activity_id = int(client.get_current_activity())

    current_activity = client.get_activity(current_activity_id)

    print 'Current activity: ', current_activity['id'], current_activity['label']


@harmony_command
def list_activities(client, args):
    for activity in client.get_activities():
        print activity


@harmony_command
def list_devices(client, args):
    for device in client.get_devices():
        print device


@harmony_command
def list_commands(client, args):
    device_id = int(args.device)
    device = client.get_device(device_id)
    for command in device.get_commands():
        print command


@harmony_command
def sync(client, args):
    client.sync()


@harmony_command
def turn_off(client, args):
    client.turn_off()


@harmony_command
def start_activity(client, args):
    """
    Switches to a different activity, identified by id
    """

    activity_id = int(args.activity)
    target_activity = client.get_activity(activity_id)

    if target_activity is None:
        logger.error('Could not find activity: ' + args.activity)
        return 1

    client.start_activity(activity_id)

    print "started activity: {0} with id {1}".format(
        target_activity['label'], target_activity['id']
    )


@harmony_command
def send_command(client, args):
    """Send a simple command to specified device"""

    device_id = int(args.device)
    target_device = client.get_device(device_id)

    if target_device is None:
        logger.error('Could not find device: ' + device)
        return 1

    client.send_command(device_id, args.command)


def main():
    parser = argparse.ArgumentParser(
        description='pyharmony utility script',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    required_flags = parser.add_argument_group('required arguments')
    required_flags.add_argument(
        '--hostname', required=True, help='IP Address of the Harmony device.'
    )

    parser.add_argument(
        '--port', default=5222, type=int,
        help=('Network port that the Harmony is listening on.')
    )

    loglevels = dict(
        (logging.getLevelName(level), level) for level in [10, 20, 30, 40, 50]
    )
    parser.add_argument(
        '--loglevel', default='INFO', choices=loglevels.keys(),
        help='Logging level to print to the console.'
    )

    subparsers = parser.add_subparsers()

    show_config_parser = subparsers.add_parser(
        'show_config', help='Print the Harmony device configuration.'
    )
    show_config_parser.set_defaults(func=show_config)

    show_activity_parser = subparsers.add_parser(
        'current_activity', help='Print current activity label and id.'
    )
    show_activity_parser.set_defaults(func=show_current_activity)

    list_activities_parser = subparsers.add_parser(
        'list_activities', help='Print activities list with ids and labels.'
    )
    list_activities_parser.set_defaults(func=list_activities)

    list_devices_parser = subparsers.add_parser(
        'list_devices', help='Print devices list with ids and labels.'
    )
    list_devices_parser.set_defaults(func=list_devices)

    list_commands_parser = subparsers.add_parser(
        'list_commands', help='Print commands for specified device.'
    )
    list_commands_parser.add_argument(
        'device', help='Device ID.'
    )
    list_commands_parser.set_defaults(func=list_commands)

    start_activity_parser = subparsers.add_parser(
        'start_activity', help='Switch to a different activity.'
    )
    start_activity_parser.add_argument(
        'activity', help='Activity id to switch to.'
    )
    start_activity_parser.set_defaults(func=start_activity)

    sync_parser = subparsers.add_parser('sync', help='Sync the harmony.')
    sync_parser.set_defaults(func=sync)

    turn_off_parser = subparsers.add_parser(
        'turn_off', help='Send a turn off command to the harmony.'
    )
    turn_off_parser.set_defaults(func=turn_off)

    command_parser = subparsers.add_parser('send_command', help='Send a simple command.')
    command_parser.add_argument(
        '--command', help='IR Command to send to the device.', required=True
    )
    command_parser.add_argument(
        '--device', help='Specify the device id to which we will send the command.'
    )
    command_parser.set_defaults(func=send_command)

    args = parser.parse_args()

    logging.basicConfig(
        level=loglevels[args.loglevel],
        format='%(levelname)s:\t%(name)s\t%(message)s'
    )

    sys.exit(args.func(args))


if __name__ == '__main__':
    main()
