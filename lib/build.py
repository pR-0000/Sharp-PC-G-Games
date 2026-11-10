"""Shared Intel HEX and symbol support for game source builds."""
from pathlib import Path
import re


def intel_hex(data: bytes, origin: int) -> str:
    lines = []
    for offset in range(0, len(data), 16):
        address = origin + offset
        chunk = data[offset:offset + 16]
        record = bytes((len(chunk), address >> 8, address & 255, 0)) + chunk
        lines.append(":" + (record + bytes((-sum(record) & 255,))).hex().upper())
    return "\n".join(lines + [":00000001FF"]) + "\n"


def read_symbols(path: Path) -> dict[str, int]:
    symbols = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([^:]+): EQU 0x([0-9A-Fa-f]+)", line)
        if match:
            symbols[match[1]] = int(match[2], 16)
    return symbols
