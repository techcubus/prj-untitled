import argparse
import importlib

EXPERIMENTS = {
    "hunger":   ("experiments.basic_hunger",        "run"),
    "fear":     ("experiments.fear_response",       "run"),
    "conflict": ("experiments.conflicting_drives",  "run"),
    "spatial":  ("experiments.spatial_navigation",  "run"),
    "longrun":  ("experiments.long_run",            "run"),
}


def main():
    parser = argparse.ArgumentParser(description="Cognitive simulation runner")
    parser.add_argument(
        "experiment",
        choices=list(EXPERIMENTS.keys()),
        default="hunger",
        nargs="?",
        help="Which experiment to run (default: hunger)",
    )
    parser.add_argument("--ticks", type=int, default=None,
                        help="Number of slow ticks to run (defaults to each experiment's own value)")
    args = parser.parse_args()

    module_path, fn_name = EXPERIMENTS[args.experiment]
    module = importlib.import_module(module_path)
    kwargs = {"slow_ticks": args.ticks} if args.ticks is not None else {}
    getattr(module, fn_name)(**kwargs)


if __name__ == "__main__":
    main()
