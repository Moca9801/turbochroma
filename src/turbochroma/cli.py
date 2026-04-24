import argparse
import sys

from turbochroma._version import __version__


def main() -> None:
    parser = argparse.ArgumentParser(prog="turbochroma", description="TurboChroma CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # In the future, we could add commands like 'bench' or 'backfill'
    parser.parse_args()
    if not sys.argv[1:]:
        parser.print_help()


if __name__ == "__main__":
    main()
