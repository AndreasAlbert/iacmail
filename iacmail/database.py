import datetime
from iacmail.model import SendingAttempt
from iacmail.util import get_message_hash


def get_n_attempts(session_maker, message_hash: str, address: str):
    with session_maker() as con:
        return (
            con.query(SendingAttempt)
            .filter_by(message_hash=message_hash, address=address)
            .count()
        )


def register_result(
    session_maker, message_text: str, addresses: set[str], failures: dict
):
    the_time = datetime.datetime.now()
    message_hash = get_message_hash(message_text)

    with session_maker() as con:
        for address in addresses:
            attempt = SendingAttempt(
                message_hash=message_hash,
                address=address,
                successful=address not in failures,
                time=the_time,
                detail=str(failures.get(address, ""))[:64],
                attempt=get_n_attempts(session_maker, message_hash, address) + 1,
            )
            con.add(attempt)
        con.commit()


def check_if_already_sent(session_maker, message_text: str, address: str) -> bool:
    """Check if the message has already been successfully sent ot the address"""
    with session_maker() as con:
        attempt = (
            con.query(SendingAttempt)
            .filter_by(
                message_hash=get_message_hash(message_text),
                address=address,
                successful=True,
            )
            .one_or_none()
        )

    return attempt is not None


def split_addresses_by_sent(session_maker, addresses: list[str], message: str):
    sent_addresses = [
        address
        for address in addresses
        if check_if_already_sent(session_maker, message, address)
    ]
    unsent_addresses = set(addresses) - set(sent_addresses)

    return sent_addresses, unsent_addresses
