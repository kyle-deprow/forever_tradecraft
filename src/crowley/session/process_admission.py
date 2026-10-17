"""Positive admission gates for subprocesses owned by the session guardian.

The wrapper is intentionally tiny and self contained because it is executed
with ``python -c`` before the allowlisted target.  A closed pipe is an abort;
only the exact positive token permits ``execv``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ADMISSION_TOKEN = b"CROWLEY_ADMIT\n"
ADMISSION_ABORT_EXIT = 125

# Keep this source independent of package imports: it runs in a fresh Python
# interpreter before the target executable has been resolved into place.
ADMISSION_WRAPPER = "\n".join(
    (
        "import os,sys",
        "fd=int(sys.argv[1])",
        "target=sys.argv[2:]",
        "token=b'CROWLEY_ADMIT\\n'",
        "data=b''",
        "while b'\\n' not in data:",
        "    chunk=os.read(fd,4096)",
        "    if not chunk: os._exit(125)",
        "    data += chunk",
        "    if len(data)>len(token): os._exit(125)",
        "if data != token or not target: os._exit(125)",
        "os.close(fd)",
        "os.execv(target[0],target)",
    )
)


def admit(write_fd: int) -> None:
    """Send the one positive admission token and close the gate."""

    try:
        written = os.write(write_fd, ADMISSION_TOKEN)
        if written != len(ADMISSION_TOKEN):
            raise OSError("short admission token write")
    finally:
        os.close(write_fd)


def abort(write_fd: int) -> None:
    """Close an unopened gate without ever admitting its child."""

    try:
        os.close(write_fd)
    except OSError:
        pass


@dataclass
class AdmissionGate:
    """Single-use owner-side positive admission capability."""

    write_fd: int
    _closed: bool = False

    def release(self) -> None:
        if self._closed:
            return
        self._closed = True
        admit(self.write_fd)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        abort(self.write_fd)


__all__ = ["ADMISSION_ABORT_EXIT", "ADMISSION_TOKEN", "ADMISSION_WRAPPER", "AdmissionGate", "abort", "admit"]
