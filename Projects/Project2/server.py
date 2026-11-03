"""
COMP 7212 - Programming Project 2
RPC-Based Multi-Threaded Server

Extends the Project 1-2 multi-threaded echo server: instead of echoing,
the server unmarshals an RPC request, executes the procedure, and
marshals the result back to the client.

Protocol (newline-delimited, UTF-8 text over TCP):
    Request : <PROCEDURE>,<int a>,<int b>\n      e.g.  ADD,10,20\n
    Response: OK,<result>\n                       e.g.  OK,30\n
              ERROR,<message>\n                   e.g.  ERROR,Procedure 'DIVIDE' is not supported ...\n

Usage:
    python server.py [host] [port]        (defaults: 0.0.0.0 5000)
"""

import socket
import sys
import threading
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5000
ENCODING = "utf-8"
MAX_LINE = 1024          # reject absurdly long requests

# ---------------------------------------------------------------------------
# Remote procedures (all computation happens HERE, on the server)
# ---------------------------------------------------------------------------
def rpc_add(a, b):
    return a + b

def rpc_subtract(a, b):
    return a - b

def rpc_multiply(a, b):
    return a * b

def rpc_max(a, b):
    return a if a >= b else b

# Dispatch table: procedure name -> function
PROCEDURES = {
    "ADD": rpc_add,
    "SUBTRACT": rpc_subtract,
    "MULTIPLY": rpc_multiply,
    "MAX": rpc_max,
}


class RPCError(Exception):
    """Raised for any invalid request; its message is sent back to the client."""


# ---------------------------------------------------------------------------
# Marshaling / unmarshaling
# ---------------------------------------------------------------------------
def unmarshal_request(line):
    """Turn 'ADD,10,20' into ('ADD', 10, 20). Raises RPCError if invalid."""
    parts = [p.strip() for p in line.split(",")]

    if len(parts) != 3:
        raise RPCError(
            f"Malformed request '{line}': expected PROCEDURE,int,int "
            f"(got {len(parts)} field(s))"
        )

    proc = parts[0].upper()
    if proc not in PROCEDURES:
        raise RPCError(
            f"Procedure '{parts[0]}' is not supported "
            f"(available: {', '.join(PROCEDURES)})"
        )

    try:
        a = int(parts[1])
        b = int(parts[2])
    except ValueError:
        raise RPCError(
            f"Parameters must be integers (received a='{parts[1]}', b='{parts[2]}')"
        )

    return proc, a, b


def marshal_response(status, payload):
    """Build the wire message, e.g. ('OK', 30) -> b'OK,30\\n'."""
    # Strip newlines from the payload so it can never break message framing
    text = str(payload).replace("\n", " ").replace("\r", " ")
    return f"{status},{text}\n".encode(ENCODING)


# ---------------------------------------------------------------------------
# Logging helper (shows which thread handled what)
# ---------------------------------------------------------------------------
print_lock = threading.Lock()

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    with print_lock:
        print(f"[{ts}] [{threading.current_thread().name}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Per-client thread
# ---------------------------------------------------------------------------
def handle_client(conn, addr):
    client_id = f"{addr[0]}:{addr[1]}"
    log(f"Connected: {client_id}")
    request_count = 0

    try:
        # makefile gives us buffered line reads, so one recv() returning a
        # partial message or two merged messages is handled correctly.
        reader = conn.makefile("r", encoding=ENCODING, newline="\n")

        while True:
            line = reader.readline(MAX_LINE + 1)
            if line == "":                      # EOF -> client closed
                break

            if len(line) > MAX_LINE and not line.endswith("\n"):
                conn.sendall(marshal_response("ERROR", "Request too long"))
                # discard the rest of this oversized line
                reader.readline()
                continue

            line = line.strip()
            if not line:                        # ignore blank lines
                continue

            request_count += 1
            log(f"{client_id} -> request #{request_count}: {line}")

            try:
                proc, a, b = unmarshal_request(line)
                result = PROCEDURES[proc](a, b)
                response = marshal_response("OK", result)
                log(f"{client_id} <- {proc}({a}, {b}) = {result}")
            except RPCError as e:
                response = marshal_response("ERROR", e)
                log(f"{client_id} <- ERROR: {e}")

            conn.sendall(response)

    except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
        log(f"{client_id} disconnected unexpectedly")
    except Exception as e:                      # never let one client kill the server
        log(f"{client_id} handler error: {e!r}")
    finally:
        try:
            conn.close()
        except OSError:
            pass
        log(f"Closed: {client_id} (served {request_count} request(s)); "
            f"active clients now: {threading.active_count() - 2}")


# ---------------------------------------------------------------------------
# Main accept loop
# ---------------------------------------------------------------------------
def main():
    host = sys.argv[1] if len(sys.argv) > 1 else HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    threading.current_thread().name = "Main"
    log(f"RPC server listening on {host}:{port}  "
        f"(procedures: {', '.join(PROCEDURES)})")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                name=f"Client-{addr[1]}",
                daemon=True,
            )
            t.start()
    except KeyboardInterrupt:
        log("Shutting down server")
    finally:
        server.close()


if __name__ == "__main__":
    main()
