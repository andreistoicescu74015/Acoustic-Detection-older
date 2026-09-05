# The board

A miniDSP UMA-8 v2. Seven MEMS microphones on a disc 90 mm across, with one mini USB cable
carrying their power in and their sound out. It runs the raw firmware, which sends all seven
capsules up the cable separately.

Every figure below was read off this board on 2026-09-05.

## How it identifies itself

    ssh node 'lsusb'
      Bus 003 Device 002: ID 2752:001d miniDSP micArray RAW SPK

| | |
|---|---|
| Vendor, product | `0x2752` : `0x001d`. `0x001c` would be the speakerphone firmware |
| Strings | Manufacturer `miniDSP`, product `micArray RAW SPK`. No serial number: `iSerial` is 0 and there is no `serial` file in sysfs, so two of these boards cannot be told apart over USB |
| `bcdDevice` | 1.12 |
| USB | 2.00, enumerated at high speed, 480 Mbit/s |
| Class | `239` Miscellaneous / `2` / `1`, an Interface Association device |
| Power | Bus powered, `bMaxPower` 500 mA, the most a USB 2.0 device may ask for |
| Sysfs | `/sys/devices/pci0000:00/0000:00:14.0/usb3/3-6`, reached as `/sys/bus/usb/devices/3-6` |

The kernel describes the socket it is in: back panel, left, vertically centred, hotplug, zero
over-current events.

    ssh node 'cat /sys/bus/usb/devices/3-6/physical_location/panel'
      back

Which firmware a board carries is written nowhere on the machine. The board is asked, and it
answers with a different product ID. That is why the page checks the USB ID and not the sound
card: both firmwares present a card called `micArray`.

## The four interfaces

    ssh node 'sudo lsusb -v -d 2752:'

| Interface | Class | What it is | Driver |
|---|---|---|---|
| 0 | Audio Control | The control plane: terminals, the feature unit, the clock | `snd-usb-audio` |
| 1 | Audio Streaming | Playback, 2 channels out | `snd-usb-audio` |
| 2 | Audio Streaming | Capture, 8 channels in | `snd-usb-audio` |
| 3 | Application Specific, subclass 1 | DFU, `miniDSP DFU`. DFU 1.10, 64-byte transfers, upload and download supported, "will not detach" | none |

All three audio interfaces use `bInterfaceProtocol 0x20`, so this is USB Audio Class 2.0.

**There is no HID interface.** The speakerphone firmware reports voice activity and a direction
of arrival over HID; the raw firmware has no such interface at all, so a board running raw
reports no direction and neither does this project.

    ssh node 'ls /dev/hidraw*'
      No such file or directory

The device declares `bNumConfigurations 2`, but both configuration descriptors are byte-identical
343-byte blocks with the same `bConfigurationValue`. Nothing in the descriptor distinguishes
them and miniDSP do not explain it.

## The capture path

Input Terminal 1, type `0x0201` Microphone, 8 channels, into Feature Unit 11, out through Output
Terminal 22 as USB streaming. One alternate setting carries it:

| | |
|---|---|
| Endpoint | `0x81` IN, isochronous asynchronous, usage type implicit feedback |
| Packet | `wMaxPacketSize` 224 bytes, `bInterval` 1, so one packet every 125 us |
| Format | PCM, `bSubslotSize` 4, `bBitResolution` 24 |
| Channels | 8, and only 8 |

224 bytes holds seven frames of eight 32-bit samples. 48000 a second needs six frames per 125 us,
so the eighth is the slack an asynchronous device is allowed to drift within.

`bmChannelConfig` is `0x00000000` and `iChannelNames` points at string index 13, which is empty.
**The board names no channels and gives them no spatial locations.** The `FL FR FC LFE RL RR FLC
FRC` map that ALSA prints is ALSA's own default fill-in for eight channels, not something the
board declared, and it means nothing here.

The clock is a single internal programmable source, unit 41, `miniDSP Internal Clock`, with a
read/write frequency control and a read-only validity control, feeding clock selector 40. That
validity bit is exposed as an ALSA control and currently reads on.

## What ALSA offers

    ssh node 'cat /proc/asound/cards'
       1 [SPK  ]: USB-Audio - micArray RAW SPK
                  miniDSP micArray RAW SPK at usb-0000:00:14.0-6, high speed

Nothing pins the card to index 1. There is no `index=` option for `snd-usb-audio` in
`/etc/modprobe.d` or `/lib/modprobe.d`, no sound-related udev rule, and no `snd` parameter on the
kernel command line, so the number comes from probe order and moves if the board is plugged into
a different port. Address it by name instead, which works today:

    ssh node 'arecord -L'
      hw:CARD=SPK,DEV=0

Measured limits of `hw:1,0` capture, from `arecord --dump-hw-params`:

| | |
|---|---|
| Format | `S32_LE` and nothing else. `S16_LE`, `S24_LE`, `S24_3LE`, `FLOAT_LE`, `U8`, `S32_BE` are all refused |
| Channels | 8 and nothing else. 1, 2, 4, 6, 7, 9 and 16 are all refused |
| Rate | 11025 to 48000 |
| Period | 2 to 48000 frames, 125 us to 1 s |
| Buffer | 4 to 96000 frames, up to 2 s |

Six rates work: 11025, 12000, 16000, 32000, 44100, 48000. **Anything else is silently replaced
with the nearest, not refused.** 8000 becomes 11025, 22050 becomes 16000, 24000 becomes 32000,
and 64000, 88200, 96000, 176400 and 192000 all become 48000. `arecord` prints a warning and
writes a complete file. Anything that needs a particular rate must check the rate it was given.

The board is also a 2-channel playback device: interface 1, terminal type `0x0301` Speaker, with
a 24-bit and a 16-bit alternate setting. This project never opens it. Its sync endpoint is the
capture endpoint, in implicit feedback mode.

### The mixer

Four simple controls: `Mic` index 0 (the 8-channel capture volume and switch), `Mic` index 1 (a
joined mono view of the same feature unit), and two playback controls. Underneath, `Mic Capture
Volume` is 8 values with range 0 to 127 mapping to -127.00 dB to 0.00 dB.

    ssh node 'amixer -c 1 contents'
      numid=10 ... 'Mic Capture Volume' values=127,127,127,127,127,127,127,127

**Every control is at maximum and every switch is on.** These attenuate on the way in and can add
nothing, so maximum is where they belong; below it, a channel is quiet for a reason that has
nothing to do with the room. `/var/lib/alsa/asound.state` stores the same, so `alsa-restore`
puts it back at boot.

There is no sound server. PipeWire, PulseAudio, WirePlumber and JACK are all absent, and there is
no `/etc/asound.conf` or `~/.asoundrc`, so a program opens ALSA directly and nothing resamples or
mixes. One program holds the capture device at a time.

## What it delivers

Two seconds recorded straight off the device on 2026-09-05, in a quiet room, with nothing else
running:

    ssh node 'arecord -D hw:1,0 -c 8 -f S32_LE -r 48000 -d 2 -t wav /tmp/cap8.wav'

96000 frames per channel, 3 072 044 bytes, 2.0000 s.

| Channel | RMS | Peak |
|---|---|---|
| 1 | -85.28 dBFS | -72.27 dBFS |
| 2 | -85.40 dBFS | -72.04 dBFS |
| 3 | -85.09 dBFS | -71.45 dBFS |
| 4 | -84.98 dBFS | -71.30 dBFS |
| 5 | -84.28 dBFS | -70.49 dBFS |
| 6 | -84.36 dBFS | -71.29 dBFS |
| 7 | -85.16 dBFS | -71.97 dBFS |
| 8 | silent | silent |

The seven agree to 1.12 dB, which is what an array of matched parts should look like with
nothing to hear. Channel 8 is not quiet, it is exactly zero in all 96000 samples: the OR of every
bit on that channel is `0x00000000`. The socket has no capsule on it and the board sends zeros. A
channel that reads zero when it should read zero confirms as much as one that reads sound.

**The samples are not 24 bit as declared.** On every live channel the greatest common divisor of
the non-zero samples is 8 and the OR of all bits is `0xFFFFFFF8`: the low three bits are always
zero and 29 of the 32 vary. A 24-bit value left-justified in a 32-bit slot would leave the low
eight zero. `/proc/asound/card1/stream0` says `Bits: 24`, the data says 29, and nothing on the
machine explains the difference. Treat the sample as a 32-bit number and scale it; do not shift a
byte off the bottom.

## The geometry

The measurements below were made earlier and have not been re-taken in this repository. They are
recorded because they are properties of the board, and marked as what they are.

Seven capsules: one in the middle and six on a circle around it, at every second hour of a clock
face. Viewed from the side the capsules fire out of, with the USB socket at six o'clock, twelve
o'clock is zero degrees and bearings run clockwise.

| Microphone | Where it sits | Bearing | x mm | y mm |
|---|---|---|---|---|
| `mic0` | the middle | centre | 0 | 0 |
| `mic6` | one o'clock | 30 | 21.75 | 37.67 |
| `mic1` | three o'clock | 90 | 43.50 | 0 |
| `mic2` | five o'clock | 150 | 21.75 | -37.67 |
| `mic3` | seven o'clock | 210 | -21.75 | -37.67 |
| `mic4` | nine o'clock | 270 | -43.50 | 0 |
| `mic5` | eleven o'clock | 330 | -21.75 | 37.67 |

The ring radius is 43.5 mm. miniDSP publish only the disc's diameter; the figure was measured
with a caliper across two opposite capsules, which shows an error twice as plainly, and came to
87.0 mm.

**Which capsule arrives on which channel is not established in this repository.** It was measured
once by the earlier work, capsule by capsule, and the tool that did it is not on the machine any
more. The board itself publishes no channel names, so this cannot be looked up: it has to be
measured again before any program may assume an order.

The capsules are Knowles SPH1668LM4H: omnidirectional PDM MEMS. Knowles' datasheet gives 65.5
dB(A) signal to noise, sensitivity -29 dBFS at 94 dB SPL, and an acoustic overload point of 122
dB SPL at 10% THD. What that sensitivity becomes after the XMOS processor and the USB path is
not published by anyone, so the dBFS figures above cannot yet be turned into sound pressure.
