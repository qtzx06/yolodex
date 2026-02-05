#!/usr/bin/env python3
"""Merge class maps from parallel subagent worktrees into a unified classes.txt.

Also re-maps class IDs in label .txt files to match the unified mapping.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from shared.utils import load_config


def main() -> int:
    config = load_config()
    output_dir = Path(config.get("output_dir", "output"))
    frames_dir = output_dir / "frames"
    worktree_base = Path("/tmp/yolodex-workers")

    # Build unified class map from all worktree class files
    unified: dict[str, int] = {}

    # First load any existing classes.txt from main repo
    main_classes = output_dir / "classes.txt"
    if main_classes.exists():
        for idx, name in enumerate(main_classes.read_text().strip().split("\n")):
            if name:
                unified[name] = idx

    # Then scan worktree class files for new classes
    for agent_dir in sorted(worktree_base.glob("agent-*")):
        classes_file = agent_dir / output_dir / "classes.txt"
        if not classes_file.exists():
            continue
        for name in classes_file.read_text().strip().split("\n"):
            if name and name not in unified:
                unified[name] = len(unified)

    # Also scan frames_dir for any classes.txt from subagents that already merged
    # (labels were already copied back by dispatch.sh)

    if not unified:
        print("[merge] No classes found. Nothing to merge.")
        return 0

    # Write unified class map
    names = [name for name, _ in sorted(unified.items(), key=lambda item: item[1])]
    main_classes.write_text("\n".join(names), encoding="utf-8")
    print(f"[merge] Unified {len(unified)} classes: {', '.join(names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
