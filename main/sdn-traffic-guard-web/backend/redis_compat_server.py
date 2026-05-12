import argparse
import fnmatch
import socketserver
import sys
import threading
import time


class RedisStore:
    def __init__(self):
        self._data = {}
        self._expiry = {}
        self._lock = threading.Lock()

    def _purge_if_needed(self, key):
        expires_at = self._expiry.get(key)
        if expires_at is not None and expires_at <= time.time():
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    def get(self, key):
        with self._lock:
            self._purge_if_needed(key)
            return self._data.get(key)

    def set(self, key, value):
        with self._lock:
            self._data[key] = value
            self._expiry.pop(key, None)

    def setex(self, key, seconds, value):
        with self._lock:
            self._data[key] = value
            self._expiry[key] = time.time() + seconds

    def expire(self, key, seconds):
        with self._lock:
            self._purge_if_needed(key)
            if key not in self._data:
                return 0
            self._expiry[key] = time.time() + seconds
            return 1

    def ttl(self, key):
        with self._lock:
            self._purge_if_needed(key)
            if key not in self._data:
                return -2
            expires_at = self._expiry.get(key)
            if expires_at is None:
                return -1
            return max(0, int(expires_at - time.time()))

    def delete(self, *keys):
        removed = 0
        with self._lock:
            for key in keys:
                self._purge_if_needed(key)
                existed = key in self._data
                self._data.pop(key, None)
                self._expiry.pop(key, None)
                removed += int(existed)
        return removed

    def exists(self, *keys):
        count = 0
        with self._lock:
            for key in keys:
                self._purge_if_needed(key)
                count += int(key in self._data)
        return count

    def keys(self, pattern="*"):
        with self._lock:
            for key in list(self._data.keys()):
                self._purge_if_needed(key)
            return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]


STORE = RedisStore()


def encode_simple_string(value):
    return f"+{value}\r\n".encode()


def encode_error(value):
    return f"-ERR {value}\r\n".encode()


def encode_bulk_string(value):
    if value is None:
        return b"$-1\r\n"
    payload = value.encode()
    return f"${len(payload)}\r\n".encode() + payload + b"\r\n"


def encode_integer(value):
    return f":{int(value)}\r\n".encode()


def encode_array(values):
    encoded = [f"*{len(values)}\r\n".encode()]
    for value in values:
        encoded.append(encode_bulk_string(value))
    return b"".join(encoded)


class RedisCompatHandler(socketserver.StreamRequestHandler):
    def _read_line(self):
        line = self.rfile.readline()
        if not line:
            raise ConnectionResetError("client disconnected")
        if not line.endswith(b"\r\n"):
            raise ValueError("protocol error")
        return line[:-2]

    def _read_command(self):
        first = self._read_line()
        if not first.startswith(b"*"):
            raise ValueError("expected array")
        count = int(first[1:])
        parts = []
        for _ in range(count):
            header = self._read_line()
            if not header.startswith(b"$"):
                raise ValueError("expected bulk string")
            length = int(header[1:])
            payload = self.rfile.read(length)
            trailer = self.rfile.read(2)
            if trailer != b"\r\n":
                raise ValueError("invalid line ending")
            parts.append(payload.decode())
        return parts

    def handle(self):
        while True:
            try:
                parts = self._read_command()
            except ConnectionResetError:
                return
            except Exception as exc:
                self.wfile.write(encode_error(str(exc)))
                return

            if not parts:
                self.wfile.write(encode_error("empty command"))
                continue

            command = parts[0].upper()
            args = parts[1:]

            try:
                if command == "PING":
                    response = encode_bulk_string(args[0]) if args else encode_simple_string("PONG")
                elif command == "ECHO" and len(args) == 1:
                    response = encode_bulk_string(args[0])
                elif command == "GET" and len(args) == 1:
                    response = encode_bulk_string(STORE.get(args[0]))
                elif command == "SET" and len(args) >= 2:
                    key, value = args[0], args[1]
                    if len(args) == 2:
                        STORE.set(key, value)
                    elif len(args) == 4 and args[2].upper() == "EX":
                        STORE.setex(key, int(args[3]), value)
                    else:
                        raise ValueError("unsupported SET options")
                    response = encode_simple_string("OK")
                elif command == "SETEX" and len(args) == 3:
                    STORE.setex(args[0], int(args[1]), args[2])
                    response = encode_simple_string("OK")
                elif command == "DEL" and args:
                    response = encode_integer(STORE.delete(*args))
                elif command == "EXISTS" and args:
                    response = encode_integer(STORE.exists(*args))
                elif command == "EXPIRE" and len(args) == 2:
                    response = encode_integer(STORE.expire(args[0], int(args[1])))
                elif command == "TTL" and len(args) == 1:
                    response = encode_integer(STORE.ttl(args[0]))
                elif command == "KEYS" and len(args) == 1:
                    response = encode_array(STORE.keys(args[0]))
                elif command == "FLUSHDB":
                    STORE.delete(*STORE.keys("*"))
                    response = encode_simple_string("OK")
                elif command == "QUIT":
                    self.wfile.write(encode_simple_string("OK"))
                    return
                else:
                    response = encode_error(f"unsupported command '{command}'")
            except Exception as exc:
                response = encode_error(str(exc))

            self.wfile.write(response)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description="Lightweight Redis-compatible server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=6379)
    args = parser.parse_args()

    with ThreadedTCPServer((args.host, args.port), RedisCompatHandler) as server:
        if sys.stdout is not None:
            print(f"Redis-compatible server listening on {args.host}:{args.port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
