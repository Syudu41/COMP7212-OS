"""
COMP 7212 - Programming Project 2
Automated demo of the four required test scenarios.
Start server.py first, then run:  python test_rpc.py [host] [port]
"""

import socket
import struct
import sys
import time

from client import RPCClient

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000


def show(label, client, proc, a, b):
    status, payload = client.call(proc, a, b)
    print(f"  [{label}] {proc}({a}, {b}) -> {status}: {payload}")
    return status, payload


def banner(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def scenario_1():
    banner("Scenario 1: Single client - all four procedures")
    c = RPCClient(HOST, PORT)
    expected = {("ADD", 10, 20): "30", ("SUBTRACT", 10, 20): "-10",
                ("MULTIPLY", 10, 20): "200", ("MAX", 10, 20): "20"}
    for (proc, a, b), want in expected.items():
        status, got = show("C1", c, proc, a, b)
        assert status == "OK" and got == want, f"{proc} expected {want}, got {got}"
    c.close()
    print("  PASS")


def scenario_2():
    banner("Scenario 2: Multiple requests on ONE connection (no reconnect)")
    c = RPCClient(HOST, PORT)
    local_port = c.sock.getsockname()[1]
    print(f"  Client local port: {local_port} (same socket for every call)")
    for proc, a, b in [("ADD", 5, 7), ("MULTIPLY", -3, 9), ("MAX", 42, 17),
                       ("SUBTRACT", 100, 1), ("ADD", 123456789, 987654321)]:
        show("C2", c, proc, a, b)
    assert c.sock.getsockname()[1] == local_port
    c.close()
    print("  PASS")


def scenario_3():
    banner("Scenario 3: Invalid procedure / invalid parameters")
    c = RPCClient(HOST, PORT)
    status, _ = show("C3", c, "DIVIDE", 10, 2)
    assert status == "ERROR"
    status, _ = show("C3", c, "ADD", "ten", 2)
    assert status == "ERROR"
    # raw malformed message (wrong field count), bypassing the stub
    c.sock.sendall(b"ADD,1\n")
    print(f"  [C3] raw 'ADD,1' -> {c.reader.readline().strip()}")
    # connection still usable after errors
    status, got = show("C3", c, "ADD", 1, 1)
    assert status == "OK" and got == "2"
    c.close()
    print("  PASS (server returned errors and kept the connection alive)")


def scenario_4():
    banner("Scenario 4: One client disconnects, others keep working")
    a = RPCClient(HOST, PORT)
    b = RPCClient(HOST, PORT)
    show("A", a, "ADD", 1, 2)
    show("B", b, "MULTIPLY", 3, 4)

    print("  [A] disconnecting abruptly (RST, no clean shutdown)...")
    # SO_LINGER with timeout 0 forces a TCP reset = unexpected disconnect
    for linger in (struct.pack("ii", 1, 0), struct.pack("HH", 1, 0)):  # POSIX / Windows
        try:
            a.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger)
            break
        except OSError:
            continue
    a.sock.close()
    time.sleep(0.5)

    show("B", b, "MAX", 8, 99)
    show("B", b, "SUBTRACT", 50, 8)
    c = RPCClient(HOST, PORT)
    show("C (new)", c, "ADD", 20, 22)
    b.close()
    c.close()
    print("  PASS (server still serving B and accepting new clients)")


if __name__ == "__main__":
    scenario_1()
    scenario_2()
    scenario_3()
    scenario_4()
    print("\nAll scenarios completed.")
