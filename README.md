# Acoustic detection

A personal project, built to learn. One microphone board with seven capsules, one mini PC, and
a network name that finds the machine wherever it is.

This is the beginning of it. What runs today is a single page that says whether the board is
connected. Everything else that will read the board is not built, and this repository does not
pretend otherwise.

## The hardware

[The board](docs/board.md) is a miniDSP UMA-8 v2: seven MEMS capsules on a disc 90 mm across,
one in the middle and six on a ring around it, joined to the machine by one USB cable that
carries their power in and their sound out. It runs the firmware that sends all seven capsules
up the cable separately rather than mixing them into one voice channel.

[The machine](docs/machine.md) is a Dell OptiPlex 3020M running Ubuntu 24.04 with no screen and
no keyboard on it. It is reached over the network as `minipc.local`, [by name and never by
address](docs/network.md).

## What is in this repository

    status/     the one program that runs on the machine, and the two files that install it
    docs/       what is on the hardware, one file per thing, with the commands that prove it

[`docs/`](docs/README.md) is the record of the hardware. The
[wiki](https://github.com/andreistoicescu74015/Acoustic-Detection/wiki) is the long form: the
steps that were taken, in order, and why each one.

## The page

    http://minipc.local

It says one of two sentences. It reads the USB bus and never opens the sound card, so it does
not stand in the way of anything that wants to record. [How it works](docs/page.md).
