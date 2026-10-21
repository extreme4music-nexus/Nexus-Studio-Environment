"""Optional Studio entry point; headless commands never import Qt."""
import argparse
from pathlib import Path
from .composition import launch_studio


def main(argv=None):
    parser = argparse.ArgumentParser(description='Nexus Studio project browser prototype')
    parser.add_argument('--root', required=True, type=Path, help='Workspace metadata directory')
    args = parser.parse_args(argv)
    return launch_studio(args.root)


if __name__ == '__main__':
    raise SystemExit(main())
