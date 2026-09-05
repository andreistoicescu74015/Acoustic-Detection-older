# Journal

What was done to the hardware, in order, with the commands. Newest entry last. Nothing is
edited out of an entry once it is written; a later entry corrects an earlier one.

## 2026-09-05 - the machine was stripped back and given one page

The mini PC had been carrying an earlier version of this project. It was taken off, the machine
was cut back towards the state the minimal server install left it in, and two things were put
on: a service record so the page is found by name, and a page that says whether the board is
connected.

### What was on the machine before

    ssh node 'ls -la ~; systemctl list-unit-files --state=enabled; ls /etc/systemd/system/'

A service called `listen` on port 8080, enabled at boot, serving four pages out of
`/home/andrei/acoustic-detection`. That directory held a copy of the earlier repository and a
Python virtual environment, 85 MB in all. Beside it, `~/page-backup-2026-08-27` with two HTML
files, and `~/.config/acoustic-detection/settings.json` holding nine numbers the old program
read. A udev rule at `/etc/udev/rules.d/70-uma8.rules` gave the board's USB node to the
`plugdev` group. A drop-in at `/etc/systemd/network/10-netplan-wlp3s0.network.d/request-ip.conf`
asked DHCP for the address 10.1.0.163.

Everything was copied off the machine before anything was deleted, and the copy was compared
against the repository it came from. It was an older state of the same files, so nothing on the
machine was unique to it.

### The service and the files

    ssh node 'sudo systemctl disable --now listen.service'
    ssh node 'sudo rm -f /etc/systemd/system/listen.service'
    ssh node 'sudo systemctl daemon-reload && sudo systemctl reset-failed'
    ssh node 'sudo rm -f /etc/udev/rules.d/70-uma8.rules'
    ssh node 'sudo udevadm control --reload-rules'
    ssh node 'rm -rf ~/acoustic-detection ~/page-backup-2026-08-27'
    ssh node 'rm -rf ~/.config/acoustic-detection ~/.cache/pip'

After this, port 8080 answered nothing and the only port listening was 22.

### The packages

The earlier work had pulled in a build toolchain, the Python packaging tools, two sound
libraries, raw USB libraries and two media programs. All of it went:

    ssh node 'sudo apt-get purge -y build-essential python3-dev python3-pip python3-venv \
        libportaudio2 libsndfile1 libusb-1.0-0-dev pkg-config python3-usb uhubctl sox ffmpeg'
    ssh node 'sudo apt-get autoremove --purge -y'
    ssh node 'sudo apt-get clean'

19 packages named, 206 more taken by `autoremove` as no longer required, almost all of them
dependencies of `ffmpeg`: the GTK stack, the X11 client libraries, the video codecs, the Mesa
drivers. Disk in use fell from 8.6 GB to 7.2 GB. 601 packages remain installed.

Two metapackages did less than their names suggest. `python3.12-venv` and `python3-pip-whl`
survived `python3-venv`, so `python3 -m venv` still works and still gives a pip inside the
environment; and `gcc`, `make`, `binutils` and `libc6-dev` survived `build-essential`. Both are
fine. Both are the difference between what the command reads like it did and what it did.

`network-manager` and `modemmanager` were found still installed, left behind as automatic
dependencies when cockpit was purged in August. They configure nothing: `nmcli device status`
reports every device unmanaged and the link is held by systemd-networkd through netplan. They
were **not** removed, because taking the network stack's spare parts off a machine reached only
over that network is the one step here that could not be undone from a laptop.

What was deliberately kept: `alsa-utils`, because it is how the board is looked at by hand;
`avahi-daemon`, because it is what publishes the name; `openssh-server`, `git`, and the shell
tools that make working on a headless machine bearable.

The board was recorded from immediately afterwards to prove nothing needed had been removed:

    ssh node 'arecord -D hw:1,0 -c 8 -f S32_LE -r 48000 -d 1 /tmp/p.wav'

One second, eight channels, 1 536 044 bytes. It works.

### The fixed address, removed

The machine is meant to be found by name so that no address has to be reserved for it. A
leftover drop-in was asking DHCP for a fixed address, and it was not even succeeding: it asked
for 10.1.0.163 and the machine was on 10.1.0.169.

    ssh node 'sudo rm -f /etc/systemd/network/10-netplan-wlp3s0.network.d/request-ip.conf'
    ssh node 'sudo rmdir /etc/systemd/network/10-netplan-wlp3s0.network.d'
    ssh node 'sudo netplan apply'

Nothing on the machine now asks for a particular address. The laptop's `~/.ssh/config` lost its
`node-ip` fallback stanza in the same move, for the same reason.

### The page

Three files went on, from `status/` in this repository:

    scp status/status.py status/status.service status/acoustic-detection.service \
        node:~/acoustic-detection/status/
    ssh node 'sudo install -m644 ~/acoustic-detection/status/status.service /etc/systemd/system/'
    ssh node 'sudo install -m644 ~/acoustic-detection/status/acoustic-detection.service \
        /etc/avahi/services/'
    ssh node 'sudo systemctl daemon-reload && sudo systemctl enable --now status.service'

Avahi picks up its services directory without being restarted, and said so in the journal:
`Service "minipc" (/services/acoustic-detection.service) successfully established`.

### What was tested

**Both address families.** The first version of the page bound IPv4 only. The machine publishes
an A record and an AAAA record under the same name, so a browser is free to try either, and over
the link-local IPv6 address the page did not answer. The socket was changed to `AF_INET6` with
`IPV6_V6ONLY` off, which answers both, and both were then checked:

    curl http://minipc.local/                         -> 200
    curl 'http://[fe80::a6c4:94ff:fe9e:1560%28]/'     -> 200

**Both sentences.** The page was made to say the other thing, by taking the board off the bus
and putting it back:

    ssh node 'sudo sh -c "echo 1 > /sys/bus/usb/devices/3-6/remove"'
    curl http://minipc.local/     -> The board is not connected.
    ssh node 'sudo sh -c "echo 3-0:1.0 > /sys/bus/usb/drivers/hub/unbind"'
    ssh node 'sudo sh -c "echo 3-0:1.0 > /sys/bus/usb/drivers/hub/bind"'
    curl http://minipc.local/     -> The board is connected.

Deauthorising the device with `echo 0 > .../authorized` was tried first and did not do it: a
deauthorised device is still on the bus and still readable in sysfs, so the page still said
connected. That is correct behaviour, not a bug, but it is worth knowing that the page answers
"is this device on the bus", not "is this device usable".

**A reboot.** `sudo systemctl reboot`, then a wait. The machine answered on its name again 35
seconds later, with the page up, avahi up, the wireless on the same address, the board
enumerated and the sound card at the same number. The journal confirms nobody logged in:
avahi started at 17:41:43, `status.service` at 17:41:44, and the first ssh session was accepted
at 17:41:56, twelve seconds after the page was already serving.

### Then the machine was interrogated

With the machine in its finished state, it was asked about itself across seven areas: the
hardware, the operating system, the board over USB, the board through ALSA, the network and the
name, the access surface, and this project's own service. Every claim in
[`board.md`](board.md), [`machine.md`](machine.md), [`system.md`](system.md) and
[`network.md`](network.md) comes from that pass and carries the command that produced it.

Three things it found that had been assumed rather than checked:

**The usual way of listing hand-installed packages does not work here and fails silently.**
Comparing `apt-mark showmanual` against `/var/log/installer/initial-status.gz` is the standard
trick, but subiquity unpacks a squashfs instead of running debian-installer and never writes that
file. With `2>/dev/null` on the `gzip`, the second list is empty and `comm -23` returns the whole
first list, so you get a plausible answer that is really just `apt-mark showmanual`. The question
is answered instead by `/var/log/apt/history.log`, which records `Requested-By` on every
user-run transaction, cross-checked against first-install dates in `/var/log/dpkg.log`.

**The board declares 24 bits and delivers 29.** The greatest common divisor of every non-zero
sample is 8 and the OR of all bits is `0xFFFFFFF8`, so only the low three bits are always zero.
A 24-bit value left-justified in a 32-bit slot would leave the low eight zero. Nothing on the
machine explains it. The practical consequence is that a sample must be scaled as a 32-bit
number and not shifted.

**The board names no channels.** `bmChannelConfig` is `0x00000000` and `iChannelNames` points at
an empty string. The `FL FR FC LFE RL RR FLC FRC` map ALSA prints is ALSA's own default fill-in
and carries no information about where a capsule sits.

One small thing was fixed as a result: the page's `Server` header read `board ` with a trailing
space, because `BaseHTTPRequestHandler` joins `server_version` and `sys_version` with a space and
the second was empty. `version_string` is now overridden whole.
