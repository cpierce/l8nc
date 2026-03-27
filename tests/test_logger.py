"""Tests for the logger module."""

from __future__ import annotations

import csv
import os
import tempfile

from l8nc.logger import LogManager, _safe_filename
from l8nc.models import TargetStats


def test_safe_filename_basic():
    assert _safe_filename("google-dns") == "google-dns"


def test_safe_filename_special_chars():
    assert _safe_filename("test@host!") == "test_host"


def test_safe_filename_spaces():
    assert _safe_filename("my target") == "my_target"


def test_safe_filename_empty():
    assert _safe_filename("!!!") == "unknown"


def test_logger_creates_csv():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = LogManager(log_dir=tmpdir)
        t = TargetStats(address="1.1.1.1", label="test-target")
        t.record(15.0)
        logger.write([t])

        path = os.path.join(tmpdir, "test-target.csv")
        assert os.path.exists(path)

        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert rows[0] == ["timestamp", "latency_ms", "loss_pct", "min_ms", "avg_ms", "max_ms", "status"]
        assert len(rows) == 2
        assert rows[1][1] == "15.0"
        assert rows[1][6] == "ok"


def test_logger_timeout_row():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = LogManager(log_dir=tmpdir)
        t = TargetStats(address="1.1.1.1", label="test")
        t.record(None)
        logger.write([t])

        path = os.path.join(tmpdir, "test.csv")
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert rows[1][1] == ""
        assert rows[1][6] == "timeout"


def test_logger_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = LogManager(log_dir=tmpdir)
        t = TargetStats(address="1.1.1.1", label="test")
        t.record(10.0)
        logger.write([t])

        summary = logger.summary()
        assert "1.1.1.1" in summary


def test_logger_skips_empty_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = LogManager(log_dir=tmpdir)
        t = TargetStats(address="1.1.1.1", label="test")
        logger.write([t])

        path = os.path.join(tmpdir, "test.csv")
        assert not os.path.exists(path)


def test_logger_appends_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = LogManager(log_dir=tmpdir)
        t = TargetStats(address="1.1.1.1", label="test")
        t.record(10.0)
        logger.write([t])
        t.record(20.0)
        logger.write([t])

        path = os.path.join(tmpdir, "test.csv")
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        # header + 2 data rows
        assert len(rows) == 3
