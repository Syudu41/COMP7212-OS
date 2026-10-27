import socket
import threading

HOST = "127.0.0.1"   # localhost (this computer)
PORT = 5000


def handle_client(conn, addr):
    """Runs in its own thread. Echoes everything one client sends."""
    print(f"[NEW] {addr} connected")
    try:
        while True:
            data = conn.recv(1024)          # wait for a message
            if not data:                    # empty = client disconnected
                break
            print(f"[{addr}] says: {data.decode()}")
            conn.sendall(data)              # send the same bytes back
    except ConnectionResetError:            # client closed suddenly
        pass
    conn.close()
    print(f"[CLOSED] {addr} disconnected")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server running on {HOST}:{PORT}")

    while True:                              # keep accepting clients forever
        conn, addr = server.accept()         # wait for a new client
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()                       # one thread per client
        print(f"[ACTIVE] {threading.active_count() - 1} client(s) connected")


main()