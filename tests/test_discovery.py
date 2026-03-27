"""Tests for the discovery module."""

from __future__ import annotations

import socket
from unittest.mock import patch

from l8nc.discovery import check_dns, resolve_hostname, reverse_dns


def test_check_dns_success():
    with patch("socket.getaddrinfo", return_value=[("AF_INET", None, None, None, ("1.2.3.4", 0))]):
        assert check_dns() is True


def test_check_dns_failure():
    with patch("socket.getaddrinfo", side_effect=socket.gaierror):
        assert check_dns() is False


def test_resolve_hostname_success():
    with patch("socket.getaddrinfo", return_value=[("AF_INET", None, None, None, ("93.184.216.34", 0))]):
        result = resolve_hostname("example.com")
        assert result == "93.184.216.34"


def test_resolve_hostname_failure():
    with patch("socket.getaddrinfo", side_effect=socket.gaierror):
        result = resolve_hostname("nonexistent.invalid")
        assert result is None


def test_reverse_dns_success():
    with patch("socket.gethostbyaddr", return_value=("dns.google", [], ["8.8.8.8"])):
        result = reverse_dns("8.8.8.8")
        assert result == "dns.google"


def test_reverse_dns_failure():
    with patch("socket.gethostbyaddr", side_effect=socket.herror):
        result = reverse_dns("1.2.3.4")
        assert result is None


def test_reverse_dns_too_long():
    long_name = "a" * 61
    with patch("socket.gethostbyaddr", return_value=(long_name, [], ["1.2.3.4"])):
        result = reverse_dns("1.2.3.4")
        assert result is None


def test_reverse_dns_returns_ip():
    with patch("socket.gethostbyaddr", return_value=("1.2.3.4", [], ["1.2.3.4"])):
        result = reverse_dns("1.2.3.4")
        assert result is None
