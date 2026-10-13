"""Stand-in interpreter used by the frotz session test. It is not a game."""

from __future__ import annotations

import sys

print("Room.", flush=True)
print(">", flush=True)
for line in sys.stdin:
    print(line.strip(), flush=True)
    print(">", flush=True)
