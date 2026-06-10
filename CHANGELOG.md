# Changelog

## 0.1.9

- Fix: CSV logging silently stopped after the first 60 pings (rolling-window length was used to detect new data)
- Fix: logger only wrote the latest ping per display tick, dropping results at fast intervals; every ping now gets its own row, stamped with the ping's own timestamp
- Fix: end-of-run summary now covers the whole session instead of the last 60 samples
- Fix: subprocess ping fallback used wrong timeout units on macOS (`-W` is ms, not seconds); added Windows args too
- Chart now sizes itself to the terminal instead of fixed 80×18
- Add jitter (`jit`) to the live per-target stats line

## 0.1.8

- Fix Homebrew tap automation
- Add `.claude` to gitignore

## 0.1.7

- Fix CI: grant Homebrew tap update job access to production environment secrets

## 0.1.6

- Update CLI help text to document default log/replay paths
- Add auto-update of Homebrew tap on publish

## 0.1.5

- Default `-l` and `-r` to `logs/` when no path specified (`l8nc -l`, `l8nc -r`)
- Add GitHub Actions workflow for automated PyPI publishing on tag push

## 0.1.4

- Add `-v` / `--version` flag (version pulled from package metadata)
- Remove `-?` help shortcut (shell glob expansion makes it unusable unquoted)
- Add per-host per-session stats to `--replay` output
- Fix async test suite: add `pytest-asyncio` dependency and configure auto mode

## 0.1.3

- Add test suite for models, display, logger, CLI, discovery, and pinger
- Fix time interval display bug in logging

## 0.1.2

- Add PyPI classifiers and badges
- Change "DOWN" status label to "NO REPLY"

## 0.1.1

- Add `-h` as help shortcut
- Expand `.gitignore`
- Move to src layout, add `CLAUDE.md`
- Add MIT license

## 0.1.0

- Initial release
- Multi-target continuous ping monitor with live braille chart
- Auto-discovery of gateway, ISP hop, and public DNS
- Custom target support with `--only` mode
- Per-target CSV logging with `-l`
- Replay from saved logs with `--replay`
