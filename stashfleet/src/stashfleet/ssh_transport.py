"""Translate rclone's SFTP subsystem request to a configured server command."""

import os
import sys


def main():
    if len(sys.argv) < 5 or sys.argv[-2:] != ["-s", "sftp"]:
        raise SystemExit("custom SFTP transport accepts only the SFTP subsystem")
    command = sys.argv[1]
    args = [*sys.argv[2:-2], command]
    # Replace this process, preserving rclone's pipes, signals, and process group.
    os.execvp(args[0], args)


if __name__ == "__main__":
    main()
