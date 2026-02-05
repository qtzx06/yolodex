from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

from .frames import extract_frames, load_frames
from .ingest import ingest_youtube
from .label_worker import run_task
from .merge import merge_to_yolo
from .rules import default_rules_path
from .tasks import create_tasks, load_classes
from .utils import ensure_dir
from .validate import validate_dataset


def default_run_dir() -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("runs") / f"run_{stamp}"


def cmd_ingest(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    ensure_dir(run_dir)
    ingest_youtube(args.youtube, run_dir)
    print(str(run_dir))
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    video_path = Path(args.video) if args.video else run_dir / "raw" / "video.mp4"
    extract_frames(video_path, run_dir, args.fps)
    print(str(run_dir / "dataset" / "images" / "train"))
    return 0


def cmd_label(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    frames = load_frames(run_dir)
    classes = load_classes(Path(args.classes) if args.classes else None)
    rules_path = Path(args.rules) if args.rules else default_rules_path()
    tasks = create_tasks(
        run_dir,
        frames,
        args.agents,
        args.model,
        classes,
        image_detail=args.image_detail,
        rules_path=rules_path,
    )

    if args.local_workers:
        for task in tasks:
            run_task(task, run_dir)
    else:
        for task in tasks:
            print(f"Task created: {task}")
        print("Run these tasks with Codex TAS agents in parallel (one task per agent/worktree).")
        print("Then run: python3 -m labeler merge --run-dir <run_dir>")
        print("And validate: python3 -m labeler validate --dataset <run_dir>/dataset")
    return 0


def cmd_label_worker(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    task_path = Path(args.task)
    run_task(task_path, run_dir)
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    classes_path = Path(args.classes) if args.classes else None
    dataset_dir = merge_to_yolo(run_dir, classes_path)
    print(str(dataset_dir))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    validate_dataset(Path(args.dataset), Path(args.rules) if args.rules else default_rules_path())
    print("OK")
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    dataset_dir = Path(args.dataset)
    if args.roboflow:
        api_key = args.roboflow_key or ""
        if api_key:
            print("Roboflow API key detected. TODO: upload/train integration.")
        else:
            print("TODO: Roboflow integration not implemented. Set ROBOFLOW_API_KEY to enable.")
        return 0
    print(f"Training stub. Dataset at {dataset_dir}")
    return 0


def cmd_run_mvp(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    ensure_dir(run_dir)
    video_path = ingest_youtube(args.youtube, run_dir)
    extract_frames(video_path, run_dir, args.fps)

    frames = load_frames(run_dir)
    classes = load_classes(Path(args.classes) if args.classes else None)
    rules_path = Path(args.rules) if args.rules else default_rules_path()
    tasks = create_tasks(
        run_dir,
        frames,
        args.agents,
        args.model,
        classes,
        image_detail=args.image_detail,
        rules_path=rules_path,
    )

    if not args.local_workers:
        for task in tasks:
            print(f"Task created: {task}")
        print("TAS manual mode: run `label-worker` for each task in parallel, then merge + validate.")
        print(f"Merge command: python3 -m labeler merge --run-dir {run_dir}")
        print(f"Validate command: python3 -m labeler validate --dataset {run_dir / 'dataset'}")
        return 0

    for task in tasks:
        run_task(task, run_dir)
    merge_to_yolo(run_dir, Path(args.classes) if args.classes else None)
    validate_dataset(run_dir / "dataset", rules_path)
    print(str(run_dir / "dataset"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Yolodex labeling CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Download a YouTube video into a run directory")
    ingest.add_argument("--youtube", required=True, help="YouTube URL")
    ingest.add_argument("--run-dir", default=str(default_run_dir()), help="Run directory")
    ingest.set_defaults(func=cmd_ingest)

    extract = sub.add_parser("extract-frames", help="Extract frames into dataset/images/train")
    extract.add_argument("--run-dir", required=True, help="Run directory")
    extract.add_argument("--video", help="Video path (defaults to run_dir/raw/video.mp4)")
    extract.add_argument("--fps", type=int, default=1, help="Frames per second")
    extract.set_defaults(func=cmd_extract)

    label = sub.add_parser("label", help="Create labeling tasks and optionally run local workers")
    label.add_argument("--run-dir", required=True, help="Run directory")
    label.add_argument("--agents", type=int, default=4, help="Number of labeling agents")
    label.add_argument("--model", default="gpt-5", help="OpenAI model")
    label.add_argument("--classes", help="Classes file (json list or newline txt)")
    label.add_argument(
        "--image-detail",
        choices=["low", "high", "auto"],
        default="high",
        help="Vision detail level for image input",
    )
    label.add_argument(
        "--rules",
        default=str(default_rules_path()),
        help="Path to LABELING_RULES.md (default: labeler/LABELING_RULES.md)",
    )
    label.add_argument("--local-workers", action="store_true", help="Run labeling workers locally")
    label.set_defaults(func=cmd_label)

    worker = sub.add_parser("label-worker", help="Run a single labeling task")
    worker.add_argument("--run-dir", required=True, help="Run directory")
    worker.add_argument("--task", required=True, help="Task json path")
    worker.set_defaults(func=cmd_label_worker)

    merge = sub.add_parser("merge", help="Merge JSON labels into YOLO dataset")
    merge.add_argument("--run-dir", required=True, help="Run directory")
    merge.add_argument("--classes", help="Classes file (json list or newline txt)")
    merge.set_defaults(func=cmd_merge)

    validate = sub.add_parser("validate", help="Validate YOLO dataset")
    validate.add_argument("--dataset", required=True, help="Dataset directory")
    validate.add_argument(
        "--rules",
        default=str(default_rules_path()),
        help="Path to LABELING_RULES.md (default: labeler/LABELING_RULES.md)",
    )
    validate.set_defaults(func=cmd_validate)

    train = sub.add_parser("train", help="Roboflow training stub")
    train.add_argument("--dataset", required=True, help="Dataset directory")
    train.add_argument("--roboflow", help="Roboflow project slug")
    train.add_argument("--roboflow-key", default=os.getenv("ROBOFLOW_API_KEY", ""))
    train.set_defaults(func=cmd_train)

    run_mvp = sub.add_parser(
        "run-mvp",
        help="MVP pipeline: ingest -> extract -> label tasks -> (optional local workers) -> merge -> validate",
    )
    run_mvp.add_argument("--youtube", required=True, help="YouTube URL")
    run_mvp.add_argument("--run-dir", default=str(default_run_dir()), help="Run directory")
    run_mvp.add_argument("--fps", type=int, default=1, help="Frames per second")
    run_mvp.add_argument("--agents", type=int, default=4, help="Number of labeling agents")
    run_mvp.add_argument("--model", default="gpt-5", help="OpenAI model")
    run_mvp.add_argument("--classes", help="Classes file (json list or newline txt)")
    run_mvp.add_argument(
        "--image-detail",
        choices=["low", "high", "auto"],
        default="high",
        help="Vision detail level for image input",
    )
    run_mvp.add_argument(
        "--rules",
        default=str(default_rules_path()),
        help="Path to LABELING_RULES.md (default: labeler/LABELING_RULES.md)",
    )
    run_mvp.add_argument(
        "--local-workers",
        action="store_true",
        help="Run workers locally to complete end-to-end in one command (without TAS fan-out)",
    )
    run_mvp.set_defaults(func=cmd_run_mvp)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
