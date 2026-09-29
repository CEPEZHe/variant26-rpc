"""Command-line entry point for the TCP RPC server."""

from rpc import RPCServer, configure_logging


def main() -> None:
    """Run the server on 127.0.0.1:9000."""
    configure_logging()
    with RPCServer(("127.0.0.1", 9000)) as server:
        print("RPC server listening on 127.0.0.1:9000")
        server.serve_forever()


if __name__ == "__main__":
    main()
