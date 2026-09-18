from __future__ import annotations

import ipaddress
import re
import secrets
import socket
import struct
from collections.abc import Callable
from pathlib import Path

from django.conf import settings


class DNSVerificationError(RuntimeError):
    pass


def _dkim_record(domain: str) -> tuple[str, bool]:
    key_file = Path(f"/etc/opendkim/keys/{domain}/mail.txt")
    try:
        content = key_file.read_text(encoding="ascii")
    except (OSError, UnicodeError):
        return "DKIM signing key is not configured for this domain.", False
    fragments = re.findall(r'"([^"]*)"', content)
    public_key = "".join(fragments).split("p=", 1)
    if len(public_key) != 2 or not public_key[1].split(";", 1)[0].strip():
        return "DKIM signing key is not configured for this domain.", False
    value = public_key[1].split(";", 1)[0].strip()
    return f"v=DKIM1; k=rsa; p={value}", True


def build_dns_records(domain: str) -> list[dict[str, str | bool]]:
    dkim_value, dkim_copyable = _dkim_record(domain)
    address_type = "AAAA" if ipaddress.ip_address(settings.SERVER_IP).version == 6 else "A"
    return [
        {
            "type": "MX", "host": domain, "cf_host": "@", "value": settings.MAIL_HOSTNAME,
            "priority": "10", "copyable": True,
        },
        {
            "type": address_type, "host": settings.MAIL_HOSTNAME, "cf_host": "mail",
            "value": settings.SERVER_IP, "priority": "-", "copyable": True,
        },
        {
            "type": "TXT", "host": domain, "cf_host": "@",
            "value": f"v=spf1 a:{settings.MAIL_HOSTNAME} -all",
            "priority": "-", "copyable": True,
        },
        {
            "type": "TXT", "host": f"mail._domainkey.{domain}", "cf_host": "mail._domainkey",
            "value": dkim_value, "priority": "-", "copyable": dkim_copyable,
        },
        {
            "type": "TXT", "host": f"_dmarc.{domain}", "cf_host": "_dmarc",
            "value": f"v=DMARC1; p=none; rua=mailto:postmaster@{domain}",
            "priority": "-", "copyable": True,
        },
    ]


def _query(name: str, record_type: int, *, timeout: float = 2.0) -> list[str]:
    nameserver = "127.0.0.53"
    try:
        with open("/etc/resolv.conf", encoding="ascii") as handle:
            nameserver = next(
                (line.split()[1] for line in handle if line.startswith("nameserver ")), nameserver
            )
    except (OSError, StopIteration):
        pass
    labels = name.rstrip(".").split(".")
    question = b"".join(bytes([len(label)]) + label.encode("idna") for label in labels) + b"\0"
    packet = struct.pack("!HHHHHH", secrets.randbelow(65534) + 1, 0x0100, 1, 0, 0, 0)
    packet += question + struct.pack("!HH", record_type, 1)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.settimeout(timeout)
            client.sendto(packet, (nameserver, 53))
            response = client.recv(4096)
    except OSError as exc:
        raise DNSVerificationError("DNS lookup timed out or was unavailable") from exc
    if len(response) < 12:
        raise DNSVerificationError("DNS response was malformed")
    _transaction, flags, questions, answers, authority, additional = struct.unpack("!HHHHHH", response[:12])
    if flags & 0x000F or questions != 1:
        return []
    offset = 12

    def skip_name(position: int) -> int:
        while position < len(response):
            length = response[position]
            if length == 0:
                return position + 1
            if length & 0xC0 == 0xC0:
                if position + 1 >= len(response):
                    raise DNSVerificationError("DNS response was malformed")
                return position + 2
            if length & 0xC0:
                raise DNSVerificationError("DNS response was malformed")
            position += 1 + length
        raise DNSVerificationError("DNS response was malformed")

    offset = skip_name(offset) + 4
    records: list[str] = []
    for _ in range(answers + authority + additional):
        if offset + 10 > len(response):
            raise DNSVerificationError("DNS response was malformed")
        offset = skip_name(offset)
        _rtype, _class, _ttl, length = struct.unpack("!HHIH", response[offset : offset + 10])
        offset += 10
        data = response[offset : offset + length]
        offset += length
        if _rtype != record_type:
            continue
        if record_type == 15 and len(data) >= 3:
            records.append(_decode_name(response, offset - length + 2).lower())
        elif record_type == 1 and length == 4:
            records.append(socket.inet_ntoa(data))
        elif record_type == 16:
            position = 0
            fragments: list[str] = []
            while position < len(data):
                chunk_length = data[position]
                position += 1
                if position + chunk_length > len(data):
                    raise DNSVerificationError("DNS response was malformed")
                fragments.append(data[position : position + chunk_length].decode("utf-8"))
                position += chunk_length
            records.append("".join(fragments))
        elif record_type == 28 and length == 16:
            records.append(socket.inet_ntop(socket.AF_INET6, data))
    return records


def _decode_name(packet: bytes, offset: int) -> str:
    labels: list[str] = []
    visited: set[int] = set()
    while offset < len(packet):
        if offset in visited:
            raise DNSVerificationError("DNS response was malformed")
        visited.add(offset)
        length = packet[offset]
        if length == 0:
            break
        if length & 0xC0 == 0xC0:
            if offset + 1 >= len(packet):
                raise DNSVerificationError("DNS response was malformed")
            pointer = ((length & 0x3F) << 8) | packet[offset + 1]
            if pointer >= len(packet):
                raise DNSVerificationError("DNS response was malformed")
            offset = pointer
            continue
        if length & 0xC0 or offset + 1 + length > len(packet):
            raise DNSVerificationError("DNS response was malformed")
        offset += 1
        labels.append(packet[offset : offset + length].decode("idna"))
        offset += length
    if offset >= len(packet):
        raise DNSVerificationError("DNS response was malformed")
    return ".".join(labels) + "."


def verify_domain(
    domain: str,
    *,
    mail_hostname: str | None = None,
    resolver: Callable[[str, int], list[str]] | None = None,
) -> dict[str, object]:
    lookup = resolver or _query
    target = (mail_hostname or settings.MAIL_HOSTNAME).strip().lower().rstrip(".")
    try:
        mx_records = {record.rstrip(".").lower() for record in lookup(domain, 15)}
        target_addresses = set(lookup(target, 1) + lookup(target, 28))
        expected_mx = target.rstrip(".")
        mx_ok = expected_mx in mx_records
        target_ok = bool(target_addresses)
        return {
            "verified": mx_ok and target_ok,
            "mx": sorted(mx_records),
            "target": target,
            "target_addresses": sorted(target_addresses),
            "mx_ok": mx_ok,
            "target_ok": target_ok,
            "message": (
                "Required MX and mail-host records match."
                if mx_ok and target_ok
                else "Required MX or mail-host records are missing or incorrect."
            ),
        }
    except (DNSVerificationError, UnicodeError, ValueError) as exc:
        return {
            "verified": False,
            "message": "DNS verification could not complete safely.",
            "error": type(exc).__name__,
        }


def verify_dns_records(
    domain: str,
    *,
    resolver: Callable[[str, int], list[str]] | None = None,
) -> dict[str, object]:
    lookup = resolver or _query
    records = build_dns_records(domain)
    results: list[dict[str, object]] = []
    for record in records:
        expected = str(record["value"])
        record_type = str(record["type"])
        if not bool(record.get("copyable", True)):
            status = "missing"
        else:
            query_type = {"MX": 15, "A": 1, "AAAA": 28, "TXT": 16}[record_type]
            answers = lookup(str(record["host"]), query_type)
            if record_type == "MX":
                status = "verified" if expected.rstrip(".").lower() in {
                    answer.rstrip(".").lower() for answer in answers
                } else "missing"
            else:
                status = "verified" if expected in answers else "missing"
        results.append({**record, "status": status})
    verified = bool(results) and all(record["status"] == "verified" for record in results)
    return {
        "verified": verified,
        "records": results,
        "message": (
            "All DNS records match."
            if verified
            else "One or more DNS records are missing or incorrect."
        ),
    }
