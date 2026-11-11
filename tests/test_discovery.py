"""Discovery must survive junk on UDP 8900 (no network, no HA needed)."""
import struct

from pyecoplug import discovery


def _reply(name=b"amp", mac=b"38:2b:78:07:d1:88", ip=b"10.10.10.174", port=80):
    fields = [0, b"id", b"a", name, b"b", 0, 0, 0, 0, 0, 0, b"", b"", 0,
              b"", b"", b"", b"", b"", 0, 0, 0, 0, 0, b"", mac, ip, port]
    return struct.pack(discovery.DISCOVERY_FORMAT, *fields)


def test_reply_size_is_408():
    assert discovery.DISCOVERY_SIZE == 408


def test_valid_reply_parses():
    pkt = discovery.parse_packet(_reply())
    assert pkt[3] == b"amp"
    assert pkt[-2:] == (b"10.10.10.174", 80)


def test_wrong_size_datagrams_are_ignored():
    for data in (b"", b"\x00" * 128, _reply()[:-1], _reply() + b"x"):
        assert discovery.parse_packet(data) is None
