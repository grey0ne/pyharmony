pyharmony
=========

Python library for connecting to and controlling the Logitech Harmony Link

Protocol
--------

As the harmony protocol is being worked out, notes are in PROTOCOL.md.

Status
------

* Authentication to harmony device working.
* Querying for entire device information
* Sending a simple command to harmony device working.

Usage
-----

To query your device's configuration state:

    harmony --hostname <harmony_host> show_config

It really helps to assign a static lease and hostname for your harmony
on your router interface, so you don't have to keep looking up the IP.

Some other commands you can invoke via command line:

    harmony --hostname <harmony_host> list_activities

    harmony --hostname <harmony_host> start_activity <activity_id>

    harmony --hostname <harmony_host> sync

    harmony --hostname <harmony_host> show_current_activity

    harmony --hostname <harmony_host> turn_off

To send device commands, look in list_devices and show_commands
for the device_id and command name.

    harmony --hostname <harmony_host> list_devices

    harmony --hostname <harmony_host> list_commands <device_id>

    harmony --hostname <harmony_host> send_command --device <device_id> --command PowerToggle

For full argument information on the command-line tool:

    harmony --help

TODO
----

* Figure out how to detect when the session token expires so we can get a new
  one.
* Figure out a good way of sending commands based on sync state.
* Is it possible to update device configuration?
