# The name

The machine is reached as `minipc.local` and never by address. No address is reserved for it
anywhere, and nothing on the machine asks DHCP for a particular one.

    ssh node                    a shell
    http://minipc.local         the page

## What makes it work

| Piece | Where | What it does |
|---|---|---|
| `/etc/hostname` | mini PC | Holds `minipc`. `hostnamectl` reports the source as `static`, so nothing at boot can change it |
| `avahi-daemon` | mini PC | Claims `minipc.local` on each link that comes up and answers mDNS for it. Enabled, so it returns at boot |
| `/etc/avahi/services/acoustic-detection.service` | mini PC | Announces `_http._tcp` on port 80 under the name `%h`, which avahi replaces with the hostname |
| An mDNS resolver | whatever is looking | Built into Windows and macOS. On Linux it is the `hosts` line in `/etc/nsswitch.conf` |

    ssh node 'hostnamectl'
      Static hostname: minipc
      Hostname source: static

    ssh node 'grep ^hosts /etc/nsswitch.conf'
      hosts: files mdns4_minimal [NOTFOUND=return] dns

`mdns4_minimal` resolves other `.local` names over IPv4 only. It does not affect anything
reaching this machine.

## What is published

Two address records and one service record:

    Resolve-DnsName minipc.local
      minipc.local AAAA fe80::a6c4:94ff:fe9e:1560
      minipc.local    A 10.1.0.169

    ssh node 'journalctl -u avahi-daemon'
      Registering new address record for 10.1.0.169 on wlp3s0.IPv4.
      Registering new address record for fe80::a6c4:94ff:fe9e:1560 on wlp3s0.*.
      Service "minipc" (/services/acoustic-detection.service) successfully established.

Because both an A and an AAAA record exist, a client may choose either. The page's socket
therefore accepts both families; see [`page.md`](page.md).

## The link

The wired port has no cable in it. The machine is on wireless, on an address DHCP chose:

    ssh node 'ip -brief addr'
      lo       UNKNOWN  127.0.0.1/8 ::1/128
      enp2s0   DOWN
      wlp3s0   UP       10.1.0.169/24 metric 600 fe80::a6c4:94ff:fe9e:1560/64

Three netplan files, all mode 0600:

| File | What it says |
|---|---|
| `50-cloud-init.yaml` | DHCP on the wired port. Written by the installer |
| `90-wifi.yaml` | The two access points and their password, DHCP, `optional: true`, route metric 600 |
| `91-cable.yaml` | Marks the wired port optional, so boot does not wait a minute and a half for a cable that is not there |

There are no drop-ins under `/etc/systemd/network`. There was one, asking DHCP for 10.1.0.163;
it was removed on 2026-09-05 and the directory with it. See [`journal.md`](journal.md).

    ssh node 'sudo find /etc/systemd/network -type f | wc -l'
      0

## Ports that answer from outside

    ssh node 'ss -tulpn'

| Port | Protocol | What |
|---|---|---|
| 22 | TCP | `sshd`. Keys only: `/etc/ssh/sshd_config.d/99-keys-only.conf` sets `PasswordAuthentication no` |
| 80 | TCP | The page, bound `*:80` so both address families reach it |
| 5353 | UDP | `avahi-daemon`. Multicast, and the reason the name resolves at all |

No firewall is installed. `ufw`, `nftables` and `iptables` are all absent from the machine.

## Where the name does not reach

mDNS is link-local by design. `minipc.local` does not resolve from another subnet, through a
router, or on a guest network with client isolation, and some access points block multicast
outright. If another machine on the link claims `minipc`, avahi renames the loser to
`minipc-2.local`.
