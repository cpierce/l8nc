# Changelog

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
