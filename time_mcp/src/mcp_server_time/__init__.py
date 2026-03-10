from .server import serve, serve_sse


def main():
    """MCP Time Server - Time and timezone conversion functionality for MCP"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="give a model the ability to handle time queries and timezone conversions"
    )
    parser.add_argument("--local-timezone", type=str, help="Override local timezone")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transport protocol to use (stdio or sse)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host IP to bind to when using sse transport")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to when using sse transport")

    args = parser.parse_args()
    
    if args.transport == "sse":
        asyncio.run(serve_sse(host=args.host, port=args.port, local_timezone=args.local_timezone))
    else:
        asyncio.run(serve(args.local_timezone))


if __name__ == "__main__":
    main()
