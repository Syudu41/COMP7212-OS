import socket

HOST = "127.0.0.1"   # must match the server
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
print(f"Connected to server at {HOST}:{PORT}. Type 'quit' to exit.")

while True:
    message = input("You: ")
    if message == "quit":
        break
    if message == "":                        # skip empty lines
        continue
    client.sendall(message.encode())         # send to server
    reply = client.recv(1024).decode()       # wait for the echo
    print(f"Echo: {reply}")

client.close()
print("Disconnected.")