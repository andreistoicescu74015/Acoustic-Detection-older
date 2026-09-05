#!/usr/bin/env python3
"""One page. It says whether the microphone board is on the USB bus."""

import http.server
import pathlib
import socket

VENDOR = "2752"   # miniDSP
PRODUCT = "001d"  # UMA-8 v2 running the raw firmware

USB = pathlib.Path("/sys/bus/usb/devices")
PORT = 80

CONNECTED = "The board is connected."
DISCONNECTED = "The board is not connected."

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="5">
<title>Board</title>
<style>
body { margin: 0; height: 100vh; display: flex; align-items: center;
       justify-content: center; background: #101014; color: #e8e8ea;
       font: 1.5rem/1.4 system-ui, sans-serif; }
</style>
</head>
<body>MESSAGE</body>
</html>
"""


def board_is_connected():
    """True when a device with the board's vendor and product ID is on the bus.

    The USB ID is asked rather than the sound card, because the board answers
    0x001C on the speakerphone firmware and 0x001D on the raw one, and only the
    second is this board.
    """
    for vendor in USB.glob("*/idVendor"):
        product = vendor.with_name("idProduct")
        if not product.exists():
            continue
        if vendor.read_text().strip() == VENDOR and product.read_text().strip() == PRODUCT:
            return True
    return False


class Handler(http.server.BaseHTTPRequestHandler):
    def version_string(self):
        """Overridden whole, because the default joins two names with a space and
        leaves a trailing one when the second is empty."""
        return "board"

    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        message = CONNECTED if board_is_connected() else DISCONNECTED
        body = PAGE.replace("MESSAGE", message).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        """The page reloads itself every five seconds. Logging that fills the journal."""


class Server(http.server.ThreadingHTTPServer):
    """One socket for both address families.

    The machine publishes an A record and an AAAA record under the same name, so
    a browser is free to try either. An IPv6 socket with V6ONLY off answers both.
    """

    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


if __name__ == "__main__":
    Server(("", PORT), Handler).serve_forever()
