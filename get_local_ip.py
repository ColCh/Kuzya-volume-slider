import typing


def get_local_ip(
    mode: typing.Union[typing.Literal['v4'], typing.Literal['v6']] = 'v4'
) -> typing.Union[str, None]:
    """Try to determine the local IP address of the machine.
    Returns None on fail."""
    import socket
    try:
        sock = socket.socket(
            socket.AF_INET if mode == 'v4' else socket.AF_INET6,
            socket.SOCK_DGRAM,
        )

        # Use Google Public DNS server to determine own IP
        sock.connect(('8.8.8.8' if mode == 'v4' else '2001:db8::', 80))

        return sock.getsockname()[0]
    except socket.error:
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return None
    finally:
        sock.close()
