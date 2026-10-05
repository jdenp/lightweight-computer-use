import sys

from .server import main

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] != "serve":
        sys.exit(f"unknown command: {args[0]!r}; usage: python -m lightweight_computer_use serve")
    main()
