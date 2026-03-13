import transmission_rpc

from config import (
    TRANSMISSION_HOST,
    TRANSMISSION_PASSWORD,
    TRANSMISSION_PORT,
    TRANSMISSION_USERNAME,
)


def get_client():
    return transmission_rpc.Client(
        host=TRANSMISSION_HOST,
        port=TRANSMISSION_PORT,
        username=TRANSMISSION_USERNAME,
        password=TRANSMISSION_PASSWORD,
        timeout=10,
    )
