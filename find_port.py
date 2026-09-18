import socket
for p in range(8000, 9001):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', p))
        s.close()
    except OSError:
        print(p)
        exit(0)
print(8000)
