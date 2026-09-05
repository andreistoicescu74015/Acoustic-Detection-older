# The page

One service runs on the machine. It serves one page at `http://minipc.local`, and the page says
one of two sentences:

    The board is connected.
    The board is not connected.

It reads the USB bus and never opens the sound card, so it does not stand in the way of anything
that wants to record.

## The three files

| In this repository | On the machine |
|---|---|
| `status/status.py` | `/home/andrei/acoustic-detection/status/status.py` |
| `status/status.service` | `/etc/systemd/system/status.service` |
| `status/acoustic-detection.service` | `/etc/avahi/services/acoustic-detection.service` |

The machine holds a copy of these files, not a checkout, so the two can drift. Nothing yet keeps
them the same.

## How it decides

It walks `/sys/bus/usb/devices/` looking for a device whose vendor ID is `2752` and whose
product ID is `001d`. Nothing outside the Python standard library is used, and no external
command is run.

The USB product ID is asked rather than the sound card because the board answers `0x001C` on the
speakerphone firmware and `0x001D` on the raw one. Both appear as a card called `micArray`, and
only the second is useful here. See [`board.md`](board.md).

"Connected" therefore means the device is on the bus. It does not mean a driver is bound to it,
or that a sound card exists, or that it will record. A device deauthorised with
`echo 0 > /sys/bus/usb/devices/3-6/authorized` is still on the bus, and the page still says
connected.

The page carries `<meta http-equiv="refresh" content="5">`, so an open tab follows the cable
within five seconds. Access logging is off: at one request every five seconds per tab it would
be the only thing in the journal.

## The service

    ssh node 'systemctl cat status.service'

The parts that are decisions rather than boilerplate:

| Line | Why |
|---|---|
| `User=andrei` | Reading `/sys/bus/usb/devices` and serving a string need no privilege |
| `AmbientCapabilities=CAP_NET_BIND_SERVICE` | The one thing an ordinary account cannot do is bind a port below 1024. This grants exactly that and nothing more, which is what makes the address the name with no port after it |
| `NoNewPrivileges=yes` | The process can never gain privilege later |
| `-u` | Unbuffered, so anything printed reaches the journal when it happens |
| `Restart=on-failure`, `RestartSec=3` | If it dies, systemd puts it back |
| `WantedBy=multi-user.target` | What `systemctl enable` acts on, and why it returns after a power cut |

The socket is `AF_INET6` with `IPV6_V6ONLY` off, so one socket accepts both address families.
The machine publishes both an A and an AAAA record, and a client may choose either:

    ssh node 'ss -tlpn | grep :80'
      LISTEN 0 5 *:80 *:*

## Installing it

    scp status/status.py status/status.service status/acoustic-detection.service \
        node:~/acoustic-detection/status/
    ssh node 'sudo install -m644 ~/acoustic-detection/status/status.service /etc/systemd/system/'
    ssh node 'sudo install -m644 ~/acoustic-detection/status/acoustic-detection.service \
        /etc/avahi/services/'
    ssh node 'sudo systemctl daemon-reload && sudo systemctl enable --now status.service'

`.gitattributes` sets `eol=lf` for the whole repository, because a systemd unit with carriage
returns in it fails in ways that read as nonsense. If a checkout ever arrives with CRLF anyway,
`sed -i "s/\r$//" ~/acoustic-detection/status/*` fixes it.

Avahi watches its services directory and needs no restart.

## Checks

    curl http://minipc.local/                       200
    curl 'http://[fe80::a6c4:94ff:fe9e:1560%28]/'   200
    curl http://minipc.local/anything               404

Both sentences were produced against the real bus by removing the board and re-enumerating; the
commands are in [`journal.md`](journal.md). After `sudo systemctl reboot` the machine answered on
its name again 35 seconds later with nobody logged in.
