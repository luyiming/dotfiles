#!/usr/bin/env python3

import argparse
import os
import re
from pathlib import Path

ZSH_HISTORY = Path(os.path.expanduser("~/.zsh_history"))
FISH_HISTORY = Path(os.path.expanduser("~/.local/share/fish/fish_history"))

ZSH_EXT_RE = re.compile(r"^:\s*(\d+):(\d+);(.*)$")

IGNORE_COMMANDS = {
    "l",
    "ls",
    "ll",
    "la",
    "pwd",
    "clear",
    "proxy",
    "proxyon",
    "proxyoff",
}

IGNORE_COMMAND_PREFIXES = {
    "bindkey",
    "alias",
}


def iter_zsh_history_entries(path: Path):
    timestamp = None
    duration = None
    command_lines = []

    with path.open(errors="replace") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            m = ZSH_EXT_RE.match(line)

            if m:
                if timestamp is not None:
                    yield timestamp, duration, "\n".join(command_lines)

                timestamp, duration, first_command_line = m.groups()
                command_lines = [first_command_line]
            else:
                if timestamp is not None:
                    command_lines.append(line)
                else:
                    print(f"SKIP leading non-history line: {line}")

    if timestamp is not None:
        yield timestamp, duration, "\n".join(command_lines)


def parse_zsh_history_line(line: str):
    """
    Parse zsh EXTENDED_HISTORY line:
      : 1780193626:0;brew update

    Return (timestamp, duration, command) or None.
    """
    m = ZSH_EXT_RE.match(line.rstrip("\n"))
    if not m:
        return None

    timestamp, duration, command = m.groups()
    return timestamp, duration, command


def is_suspicious(cmd: str) -> tuple[bool, str]:
    """
    Conservative filter: skip commands likely to be invalid or risky in fish history.
    """
    if not cmd.strip():
        return True, "empty command"

    if not cmd.isascii():
        return True, "non-ascii command"

    if "\n" in cmd or "\r" in cmd:
        return True, "multiline command"

    if cmd.endswith("\\"):
        return True, "line continuation"

    if "`" in cmd:
        return True, "backtick command substitution"

    if re.search(r"(^|[;&|]\s*)\[ ", cmd):
        return True, "test command using [ ... ]"

    if "<< " in cmd or "<<" in cmd:
        return True, "heredoc"

    if cmd in IGNORE_COMMANDS:
        return True, "ignored command"

    for prefix in IGNORE_COMMAND_PREFIXES:
        if cmd.startswith(prefix + " "):
            return True, "ignored command prefix"

    return False, ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite fish history instead of appending",
    )
    args = parser.parse_args()

    imported = 0
    skipped_consecutive_duplicate = 0
    suspicious = 0

    FISH_HISTORY.parent.mkdir(parents=True, exist_ok=True)

    mode = "w" if args.overwrite else "a"

    previous_zsh_command = None
    with FISH_HISTORY.open(mode) as dst:
        for timestamp, duration, command in iter_zsh_history_entries(ZSH_HISTORY):
            # Remove consecutive duplicates in zsh history.
            if command == previous_zsh_command:
                skipped_consecutive_duplicate += 1
                print(f"SKIP consecutive duplicate: {command}")
                continue

            previous_zsh_command = command

            bad, reason = is_suspicious(command)
            if bad:
                suspicious += 1
                print(f"SUSPICIOUS [{reason}]:")
                print(command)
                print()
                continue

            dst.write(f"- cmd: {command}\n")
            dst.write(f"  when: {timestamp}\n")

            imported += 1
            print(f"ADD: {command}")

    print()
    print(f"Imported: {imported}")
    print(f"Suspicious: {suspicious}")
    print(f"Skipped consecutive zsh duplicates: {skipped_consecutive_duplicate}")


if __name__ == "__main__":
    main()
