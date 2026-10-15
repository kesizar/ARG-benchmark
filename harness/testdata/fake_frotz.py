"""Stand-in interpreter used by the frotz session test. It is not a game."""

from __future__ import annotations

import sys

print("***MORE***", flush=True)
sys.stdin.readline()
print("Room.", flush=True)
print("   Place                                               4/1", flush=True)
print(">", flush=True)
for line in sys.stdin:
    command = line.strip()
    print(command, flush=True)
    if command == "look":
        print("Score: 2", flush=True)
    print(">", flush=True)
