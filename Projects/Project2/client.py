"""
COMP 7212 - Programming Project 2
RPC Client (client-side stub + interactive interface)

The client NEVER computes the result. It only:
  1. marshals the procedure name and parameters,
  2. sends the request to the server,
  3. waits for the response,
  4. unmarshals the response,
  5. displays the result.

Usage:
    python client.py [host] [port]        (defaults: 127.0.0.1 5000)
Type QUIT (or press Ctrl+C) at the operation prompt to disconnect.
"""

import socket
import sys

HOST = "127.0.0.1"
PORT = 5000
ENCODING = "utf-8"


class RPCClient:
    """Client stub: hides the socket and message format behind call()."""

    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port))
        # buffered reader -> read exactly one newline-terminated response
        self.reader = self.sock.makefile("r", encoding=ENCODING, newline="\n")

    # ---------------- marshaling ----------------
    @staticmethod
    def marshal_request(procedure, a, b):
        """('ADD', '10', '20') -> b'ADD,10,20\\n'"""
        fields = [str(procedure).strip(), str(a).strip(), str(b).strip()]
        for f in fields:
            # commas/newlines inside a field would corrupt the message format
            if "," in f or "\n" in f or "\r" in f:
                raise ValueError(f"Field '{f}' may not contain commas or newlines")
        return (",".join(fields) + "\n").encode(ENCODING)

    @staticmethod
    def unmarshal_response(line):
        """'OK,30' -> ('OK', '30');  'ERROR,msg' -> ('ERROR', 'msg')"""
        status, _, payload = line.strip().partition(",")
        if status not in ("OK", "ERROR"):
            return "ERROR", f"Unexpected reply format: {line.strip()!r}"
        return status, payload

    # ---------------- remote call ----------------
    def call(self, procedure, a, b):
        request = self.marshal_request(procedure, a, b)   # 1. marshal
        self.sock.sendall(request)                        # 2. send
        line = self.reader.readline()                     # 3. wait for reply
        if line == "":
            raise ConnectionError("Connection closed by server")
        return self.unmarshal_response(line)              # 4. unmarshal

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT

    try:
        client = RPCClient(host, port)
    except OSError as e:
        print(f"Could not connect to {host}:{port} -> {e}")
        sys.exit(1)

    print(f"Connected to RPC server at {host}:{port}")
    print("Supported operations: ADD, SUBTRACT, MULTIPLY, MAX  (type QUIT to exit)\n")

    try:
        while True:
            op = input("Enter operation: ").strip()
            if not op:
                continue
            if op.upper() in ("QUIT", "EXIT"):
                break

            # Parameters are sent as typed; the SERVER validates them,
            # so invalid input demonstrates server-side error handling.
            a = input("Enter first integer: ")
            b = input("Enter second integer: ")

            try:
                status, payload = client.call(op.upper(), a, b)
            except ValueError as e:                       # marshaling problem
                print(f"Client error: {e}\n")
                continue

            if status == "OK":                            # 5. display
                print(f"Result from server: {payload}\n")
            else:
                print(f"Error from server: {payload}\n")

    except (KeyboardInterrupt, EOFError):
        print()
    except (ConnectionError, OSError) as e:
        print(f"Connection lost: {e}")
    finally:
        client.close()
        print("Disconnected from server.")


if __name__ == "__main__":
    main()
