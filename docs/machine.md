# The machine

A Dell OptiPlex 3020M: a desktop about the size of a hardback book, built out of laptop parts. It
runs with no screen and no keyboard on it and is reached over the network. The microphone board
plugs into one of its USB sockets, and that cable is the only way sound gets into any of this.

Read on 2026-09-05. Serial numbers and hardware addresses are deliberately left out.

## What is in it

| Part | What it is |
|---|---|
| Firmware | Dell BIOS A15, dated 2019-05-20, UEFI, 8 MB ROM. The machine boots in UEFI mode |
| Processor | Intel Core i5-4590T, Haswell, 4 cores and 4 threads. No Hyper-Threading: the kernel's SMT control reads `notsupported` |
| Clock | 2.0 GHz base, 3.0 GHz scaling maximum, 800 MHz minimum. `intel_cpufreq` driver, `schedutil` governor, turbo enabled |
| Instructions | AVX, AVX2, FMA, SSE4.2, AES-NI, F16C, BMI2 |
| Cache | L1d 4x32 KiB, L1i 4x32 KiB, L2 4x256 KiB, L3 6 MiB |
| Memory | 11.6 GiB usable. Two SODIMM slots, both full and none free: 8 GB dual-rank plus 4 GB single-rank, DDR3 at 1600 MT/s. The board takes 16 GB at most |
| Swap | A 4 GB file at `/swap.img`, 0 B used. No swap partition |
| Disk | One 465.8 GiB SATA Samsung SSD 860 EVO, non-rotational. GPT: 1 G EFI, 2 G `/boot`, the rest one LVM volume carrying `/`. The volume group has no free extents |
| Wired network | Realtek RTL8111/8168 gigabit on the mainboard, driver `r8169`. No cable in it |
| Wireless | Intel Dual Band Wireless-AC 7260, driver `iwlwifi`. This is the connection in use |
| USB | An Intel xHCI controller at PCI 00:14.0 with a 10-port high-speed root hub and a 2-port SuperSpeed root hub, plus two EHCI controllers with 2 ports each. DMI lists six external connectors and does not say which are which |
| Graphics | Intel integrated, five connectors, all five disconnected |
| Expansion | One free PCI Express x1 slot |

    ssh node 'lscpu; free -h; lsblk -f; lspci'

## Heat and power

    ssh node 'for f in /sys/class/thermal/thermal_zone*/; do cat $f/type; cat $f/temp; done'

At idle: two ACPI zones at 27.8 C and 29.8 C, CPU package 48 to 49 C, per core 46 to 49 C,
against a max of 69 C and a critical of 75 C.

CPU package power is exposed through Intel RAPL, with a 35 W long-term limit. Measured at idle
over 2.006 s, the package drew **1.36 W**. Reading the RAPL counters needs root; they are not
world-readable. The machine exposes nothing about wall-plug draw: there is no DMI power supply
record and `/sys/class/power_supply` is empty.

`lm-sensors` and `smartctl` are not installed, so fan speeds, board voltages and the SSD's wear
level are not readable. Only the kernel's own thermal zones and `coretemp` are.

## What the sound path costs it

Eight channels at 48000 readings a second, four bytes a reading, is 1.5 MB a second coming off
the cable and 5.5 GB an hour if every second of it were kept. Moving that is nothing for this
machine: at 1.36 W idle it is not working at all. The four cores are there for what happens to
the samples afterwards.

## Where the board sits

    ssh node 'lsusb -t'
      /:  Bus 003.Port 001: Dev 001, Class=root_hub, Driver=xhci_hcd/10p, 480M
          |__ Port 006: Dev 002, If 0, Class=Audio, Driver=snd-usb-audio, 480M

Port 6 of the bus 3 root hub, on the xHCI controller, at high speed. The kernel places that
socket on the back panel, left, vertically centred. The only other thing on that bus is the
machine's own Bluetooth radio, at 12 Mbit/s.

Neither the socket nor the ALSA card number is fixed. Plug the board into a different port and
the kernel hands it the next free card number, so anything holding a remembered `hw:0,0` ends up
talking to nothing. Find it by name. See [`board.md`](board.md).

## Reaching it

No screen is attached and no display manager is installed, so there is nothing for it to draw
even if one were. The machine is reached over the network as `minipc.local`; see
[`network.md`](network.md).

Boot takes 19.1 s in total, of which 11.4 s is Dell's firmware and 3.0 s is userspace.

    ssh node 'systemd-analyze'
      Startup finished in 11.351s (firmware) + 3.015s (loader) + 1.717s (kernel)
                          + 3.021s (userspace) = 19.106s
