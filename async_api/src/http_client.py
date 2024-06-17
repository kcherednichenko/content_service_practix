from aiohttp import ClientSession

session: ClientSession | None = None


def get_session() -> ClientSession:
    return session
