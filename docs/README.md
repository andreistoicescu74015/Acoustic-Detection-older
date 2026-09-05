# docs

One folder, one rule: everything in here describes something that is actually on the hardware,
and everything on the hardware is described in here. Nothing is aspirational, nothing is a plan,
and nothing is left out because it is dull.

Every claim carries the command that produced it. If you want to check a sentence in these
files, run its command against the machine and compare. When the hardware changes, the file
changes in the same commit.

## The files

| File | What it describes |
|---|---|
| [`board.md`](board.md) | The miniDSP UMA-8 v2: what it is, how it presents itself over USB, what it delivers through ALSA |
| [`machine.md`](machine.md) | The Dell OptiPlex 3020M: processor, memory, disk, ports, firmware |
| [`system.md`](system.md) | Ubuntu on that machine: what is installed, what runs, what was taken off and why |
| [`network.md`](network.md) | How the machine is reached by name, and why no address is reserved for it |
| [`page.md`](page.md) | The one service this project runs, and the page it serves |
| [`journal.md`](journal.md) | What was done to the hardware, in order, with the commands |

## The split with the wiki

These files say what is there. The [wiki](https://github.com/andreistoicescu74015/Acoustic-Detection/wiki)
says how it got there and why it was done that way: the reasoning, the options that were not
taken, and every command in the order it was run. A file here should be readable in a minute. A
wiki page is allowed to take longer.

## What is not in here

The board's firmware images are miniDSP's own and are not redistributed. They are not in this
repository and not on the machine. miniDSP publish them behind a login on their downloads page,
along with the product brief and the user manual.
