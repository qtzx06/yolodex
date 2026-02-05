#!/usr/bin/env python3
"""Play skill entrypoint: deterministic real-time gameplay bot."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from shared.game_bot.runtime import main


if __name__ == "__main__":
    raise SystemExit(main())

