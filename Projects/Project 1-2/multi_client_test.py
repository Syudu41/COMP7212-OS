import socket
import sys
import threading

HOST = "127.0.0.1"
PORT = 5000

# Usage: python test_multi_client.py [num_clients] [num_messages]
NUM_CLIENTS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
NUM_MESSAGES = int(sys.argv[2]) if len(sys.argv) > 2 else 500

start_together = threading.Barrier(NUM_CLIENTS)  # all clients start at once
lock = threading.Lock()                          # protects the counters
correct = 0
wrong = 0


def run_client(n):
    """One test client: send unique messages and check every echo."""
    global correct, wrong
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    start_together.wait()                 # wait until every client is connected

    my_correct = 0
    for i in range(1, NUM_MESSAGES + 1):
        message = f"client{n}-msg{i}"     # unique message
        client.sendall(message.encode())
        reply = client.recv(1024).decode()
        if reply == message:
            my_correct += 1
    client.close()

    with lock:
        correct += my_correct
        wrong += NUM_MESSAGES - my_correct
        print(f"Client {n}: {my_correct}/{NUM_MESSAGES} echoes correct")


threads = []
for n in range(1, NUM_CLIENTS + 1):
    t = threading.Thread(target=run_client, args=(n,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

total = NUM_CLIENTS * NUM_MESSAGES
print("\n========== RESULT ==========")
print(f"{NUM_CLIENTS} clients x {NUM_MESSAGES} messages = {total} messages")
print(f"Correct echoes: {correct} / {total}")
print("PASS" if correct == total else "FAIL")