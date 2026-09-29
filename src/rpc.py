"""TCP RPC server and client for practical assignment variant 26."""

from __future__ import annotations

import json
import logging
import socket
import socketserver
from collections.abc import Callable
from typing import Any

from model import DataModel

PROTOCOL_VERSION = 1
REQUEST_HEADER_SIZE = 6
RESPONSE_HEADER_SIZE = 8

OPERATIONS = {
    "create_profile": 1,
    "get_profiles": 2,
    "get_profile": 3,
    "edit_profile": 4,
    "create_query": 5,
    "get_queries": 6,
    "get_query": 7,
    "edit_query": 8,
    "create_feedback": 9,
    "get_feedback": 10,
    "get_feedback_item": 11,
    "edit_feedback": 12,
    "recent_feedback_projection": 13,
}
OPERATION_NAMES = {value: key for key, value in OPERATIONS.items()}

LOGGER = logging.getLogger("variant26.rpc")


def configure_logging() -> None:
    """Configure required request/response logging to journal.log."""
    if LOGGER.handlers:
        return
    LOGGER.setLevel(logging.INFO)
    handler = logging.FileHandler("journal.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    LOGGER.addHandler(handler)


def _read_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("connection closed before message completed")
        data.extend(chunk)
    return bytes(data)


def encode_request(operation: int, body: dict[str, Any]) -> bytes:
    """Encode: operation(2) + body size(4) + JSON, little-endian."""
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    return (
        operation.to_bytes(2, "little") + len(raw).to_bytes(4, "little") + raw
    )


def decode_request(sock: socket.socket) -> tuple[int, dict[str, Any]]:
    """Read one request from a connected socket."""
    header = _read_exact(sock, REQUEST_HEADER_SIZE)
    operation = int.from_bytes(header[:2], "little")
    size = int.from_bytes(header[2:6], "little")
    body = json.loads(_read_exact(sock, size).decode("utf-8"))
    return operation, body


def encode_response(operation: int, body: dict[str, Any]) -> bytes:
    """Encode: version(1) + operation(2) + body size(5) + JSON."""
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    return (
        PROTOCOL_VERSION.to_bytes(1, "little")
        + operation.to_bytes(2, "little")
        + len(raw).to_bytes(5, "little")
        + raw
    )


def decode_response(sock: socket.socket) -> tuple[int, dict[str, Any]]:
    """Read one response from a connected socket."""
    header = _read_exact(sock, RESPONSE_HEADER_SIZE)
    version = header[0]
    if version != PROTOCOL_VERSION:
        raise ValueError(f"unsupported protocol version: {version}")
    operation = int.from_bytes(header[1:3], "little")
    size = int.from_bytes(header[3:8], "little")
    body = json.loads(_read_exact(sock, size).decode("utf-8"))
    return operation, body


class RPCDispatcher:
    """Map operation codes to DataModel methods."""

    def __init__(self, model: DataModel | None = None) -> None:
        self.model = model or DataModel()

    def dispatch(self, operation: int, body: dict[str, Any]) -> dict[str, Any]:
        """Execute an RPC call and return a JSON-serializable envelope."""
        name = OPERATION_NAMES.get(operation)
        if name is None:
            return {"ok": False, "error": f"unknown operation: {operation}"}
        method: Callable[..., Any] = getattr(self.model, name)
        try:
            result = method(**body)
        except (KeyError, ValueError, TypeError) as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "result": result}


class RPCRequestHandler(socketserver.BaseRequestHandler):
    """Handle one or more RPC requests on a TCP connection."""

    def handle(self) -> None:
        configure_logging()
        while True:
            try:
                operation, body = decode_request(self.request)
            except ConnectionError:
                return
            LOGGER.info("request op=%s body=%r", operation, body)
            response = self.server.dispatcher.dispatch(operation, body)
            LOGGER.info("response op=%s body=%r", operation, response)
            self.request.sendall(encode_response(operation, response))


class RPCServer(socketserver.ThreadingTCPServer):
    """Threaded TCP server carrying an RPCDispatcher."""

    allow_reuse_address = True

    def __init__(
        self, address: tuple[str, int], model: DataModel | None = None
    ):
        super().__init__(address, RPCRequestHandler)
        self.dispatcher = RPCDispatcher(model)


class RPCClient:
    """Client whose methods match the DataModel function names."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9000) -> None:
        self.host = host
        self.port = port

    def _call(self, name: str, **kwargs: Any) -> Any:
        operation = OPERATIONS[name]
        with socket.create_connection(
            (self.host, self.port), timeout=5
        ) as sock:
            sock.sendall(encode_request(operation, kwargs))
            response_op, body = decode_response(sock)
        if response_op != operation:
            raise RuntimeError("response operation does not match request")
        if not body.get("ok"):
            raise RuntimeError(body.get("error", "RPC error"))
        return body.get("result")

    def create_profile(self, **values: Any) -> Any:
        return self._call("create_profile", **values)

    def get_profiles(self) -> Any:
        return self._call("get_profiles")

    def get_profile(self, key: int) -> Any:
        return self._call("get_profile", key=key)

    def edit_profile(self, key: int, **changes: Any) -> Any:
        return self._call("edit_profile", key=key, **changes)

    def create_query(self, **values: Any) -> Any:
        return self._call("create_query", **values)

    def get_queries(self) -> Any:
        return self._call("get_queries")

    def get_query(self, key: int) -> Any:
        return self._call("get_query", key=key)

    def edit_query(self, key: int, **changes: Any) -> Any:
        return self._call("edit_query", key=key, **changes)

    def create_feedback(self, **values: Any) -> Any:
        return self._call("create_feedback", **values)

    def get_feedback(self) -> Any:
        return self._call("get_feedback")

    def get_feedback_item(self, key: int) -> Any:
        return self._call("get_feedback_item", key=key)

    def edit_feedback(self, key: int, **changes: Any) -> Any:
        return self._call("edit_feedback", key=key, **changes)

    def recent_feedback_projection(self, now: int | None = None) -> Any:
        kwargs = {} if now is None else {"now": now}
        return self._call("recent_feedback_projection", **kwargs)
