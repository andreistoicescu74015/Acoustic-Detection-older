# The system

Ubuntu 24.04.4 LTS, kernel 6.8.0-138-generic, installed 2026-07-17 from the server image by
autoinstall. Read on 2026-09-05.

    ssh node 'cat /var/log/installer/media-info'
      Ubuntu-Server 24.04.4 LTS "Noble Numbat" - Release amd64 (20260210)

    ssh node 'sudo grep -A2 "source:" /var/log/installer/autoinstall-user-data'
        source:
          id: ubuntu-server-minimal

The minimized variant: `ubuntu-server-minimal` is installed, `ubuntu-server` and
`ubuntu-desktop` are not. There is no display manager, no Xorg and no `gnome-shell`. The default
target is `graphical.target` and it is active, but with nothing to draw it resolves to
`multi-user.target` plus a getty on tty1.

604 packages known to dpkg, 601 in state `ii`. The three others are configuration leftovers of
the removed 6.8.0-136 kernel. Nothing is half-installed and `apt-get check` is clean.

## What is installed by hand

Ubuntu Server 24.04 installs through subiquity, which unpacks a squashfs rather than running
debian-installer, so **there is no `/var/log/installer/initial-status.gz`** and the usual
"compare against what the image shipped" trick does not work here. What does work is the apt
history, which records who asked for what:

    ssh node 'grep -B3 "Requested-By" /var/log/apt/history.log'
    ssh node 'zgrep " status installed <package>:" /var/log/dpkg.log'

Fourteen packages were installed by hand and are still here:

| Package | Why it is kept |
|---|---|
| `alsa-utils` | `arecord` and `amixer`. How the board is looked at without writing a program |
| `avahi-daemon` | Publishes `minipc.local`. Without it the machine has no name |
| `git` | The repository will be checked out here rather than copied |
| `iw`, `net-tools`, `iputils-ping` | Looking at the network from the machine |
| `htop`, `btop`, `tmux`, `mc`, `ncdu`, `tree`, `duf`, `nano` | Working at the shell on a machine with no screen |

The rest of `apt-mark showmanual` (40 entries) is the image's own metapackages and the
installer's apt stage: `ubuntu-server-minimal`, `linux-generic`, `openssh-server`,
`wpasupplicant`, `grub-efi-amd64`, `unattended-upgrades`, `lxd-installer` and the base utilities.

Python is 3.12.3 at `/usr/bin/python3`. **`pip` is gone** and `python3 -m pip` reports no module.
`python3.12-venv` and `python3-pip-whl` survived, so `python3 -m venv` still works and gives a
working pip inside an environment. Nothing in this repository needs either: the page uses only
the standard library.

`gcc`, `make`, `binutils` and `libc6-dev` survived the `build-essential` purge. They are marked
automatic, but `apt-get -s autoremove` proposes removing nothing, so something still depends on
them.

No snap packages are installed, though `snapd` is present and running. `cron` is not installed.
The locale is `C.UTF-8`.

## What was taken off

Recorded because a reader should be able to see the machine's whole history, not just its
current state.

| When | What | Why |
|---|---|---|
| 2026-08-24 | `cockpit` and its six components, `mosquitto`, `mosquitto-clients`, `dfu-util` | The earlier, drone-only version of this project |
| 2026-09-05 | `build-essential`, `python3-dev`, `python3-pip`, `python3-venv`, `libportaudio2`, `libsndfile1`, `libusb-1.0-0-dev`, `pkg-config`, `python3-usb`, `uhubctl`, `sox`, `ffmpeg`, and 206 more by `autoremove` | Nothing in this repository needs any of it. Almost all of the 206 were `ffmpeg` dependencies: the GTK stack, X11, Mesa, the video codecs |

Disk in use fell from 8.6 GB to 7.2 GB. The board was recorded from immediately afterwards to
prove nothing needed had gone. See [`journal.md`](journal.md).

`network-manager` and `modemmanager` are still installed and running. They were pulled in as
automatic dependencies of `cockpit-networkmanager` and left behind when cockpit was purged. They
configure nothing: `nmcli device status` reports every device unmanaged, and the link is held by
systemd-networkd through netplan.

## What runs

    ssh node 'systemctl list-units --type=service --state=running'

21 services, zero failed, `systemctl is-system-running` reports `running`, and no
error-priority entry was logged this boot.

**Exactly one enabled unit is not shipped by a package:** `status.service`, at
`/etc/systemd/system/status.service`. It is the only regular file in that directory; everything
else there is a stock symlink or a `.wants` directory. See [`page.md`](page.md).

Two audio units exist and neither holds the card: `alsa-restore.service` (active, exited) and
`alsa-state.service` (inactive).

## Updates

Unattended upgrades are on for both halves, with the stock four allowed origins and an empty
blacklist:

    ssh node 'cat /etc/apt/apt.conf.d/20auto-upgrades'
      APT::Periodic::Update-Package-Lists "1";
      APT::Periodic::Unattended-Upgrade "1";

They fire: on 2026-09-04 they upgraded 23 packages including `openssh-server`. At the time of
writing 31 packages are upgradable, including the kernel to 6.8.0-139, and no reboot is pending.

The clock is UTC, the RTC is in UTC, and `systemd-timesyncd` synchronises against
`ntp.ubuntu.com`, stratum 2. **Every timestamp this project writes is UTC**, not local time.

## Access

`sshd` refuses passwords. `/etc/ssh/sshd_config.d/99-keys-only.conf` sets
`PasswordAuthentication no` and `KbdInteractiveAuthentication no`, and it sorts after the
cloud-init file that cloud-init owns and rewrites.

`/etc/sudoers.d` holds only the packaged `README`. There is no passwordless rule; every `sudo`
is authenticated.

The account `andrei` is in `sudo` for administration and in `audio` for the board. `audio` is
what lets it record without being root: the nodes under `/dev/snd` are `root:audio` mode 0660.

Raw USB is different. The board's node is `/dev/bus/usb/003/002`, `root:root` mode 0664, and
**no udev rule on the machine mentions vendor 2752**, so an ordinary account gets read-only
access to it and `lsusb -v` warns that information is missing. Reading or writing the board's
firmware without `sudo` would take a udev rule, and there is none. There was one until
2026-09-05; it was removed because nothing here does that any more.

`/opt`, `/srv` and `/usr/local` are all empty of anything but the stock skeleton, and the only
non-dotfile in `/home/andrei` is `acoustic-detection`, 20 KB.
