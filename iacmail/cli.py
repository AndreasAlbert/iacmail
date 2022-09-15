import datetime
import functools
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from getpass import getpass
from pathlib import Path
from tabnanny import check

import sqlalchemy as sa
import tqdm
import typer
from typer import Typer

from iacmail.model import Base, SendingAttempt
from iacmail.util import (
    get_message_hash,
    prompt_password_if_needed,
    read_address_file,
    read_message_file,
    read_user_config_file,
)

logger = logging.getLogger(__name__)

app = Typer()

DB_PATH = "sqlite:///db.sqlite"

engine = sa.create_engine(DB_PATH)
Session = sa.orm.sessionmaker(bind=engine)
Base.metadata.create_all(engine, checkfirst=True)
logging.basicConfig(level=logging.INFO)


def build_message(message_text: str, address: str, subject: str, user_config: dict):
    message = MIMEMultipart()
    message["From"] = user_config["sender_email"]
    message["To"] = address
    message["Subject"] = subject
    message["Bcc"] = user_config["sender_email"]

    message.attach(MIMEText(message_text, "plain"))
    return message


def get_n_attempts(message_hash: str, address: str):
    with Session() as con:
        return (
            con.query(SendingAttempt)
            .filter_by(message_hash=message_hash, address=address)
            .count()
        )


def register_result(message_text: str, addresses: set[str], failures: dict):
    the_time = datetime.datetime.now()
    message_hash = get_message_hash(message_text)

    with Session() as con:
        for address in addresses:
            attempt = SendingAttempt(
                message_hash=message_hash,
                address=address,
                successful=address not in failures,
                time=the_time,
                detail=str(failures.get(address, ""))[:64],
                attempt=get_n_attempts(message_hash, address) + 1,
            )
            con.add(attempt)
        con.commit()


def check_if_already_sent(message_text: str, address: str) -> bool:
    """Check if the message has already been successfully sent ot the address"""
    with Session() as con:
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


def send_message(
    message: MIMEMultipart, addresses: list[str], user_config: dict
) -> dict:
    context = ssl.create_default_context()
    if isinstance(addresses, str):
        addresses = [addresses]

    try:
        # Server setup
        server = smtplib.SMTP(user_config["smtp_server"], user_config["smtp_port"])
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(user_config["sender_email"], user_config["password"])

        text = message.as_string()
        failures = server.sendmail(user_config["sender_email"], addresses, text)
    except smtplib.SMTPRecipientsRefused as exc:
        failures = exc.recipients
    # except Exception as exc:
    #     failures = {address : str(exc) for address in addresses}
    finally:
        server.quit()

    return failures


def split_addresses_by_sent(addresses: list[str], message: str):

    sent_addresses = [
        address for address in addresses if check_if_already_sent(message, address)
    ]
    unsent_addresses = set(addresses) - set(sent_addresses)

    return sent_addresses, unsent_addresses


@app.command()
def send(
    address_file: Path = typer.Option(..., help="File containing one recipient email address per line."),
    message_file: Path = typer.Option(..., help="File containing the body text for the email."),
    user_config_file: Path = typer.Option(..., help="File containting the user configuration."),
    subject: str = typer.Option(..., help="Subject for the email."),
):
    addresses = read_address_file(address_file)
    message_text = read_message_file(message_file)
    user_config = read_user_config_file(user_config_file)

    user_config = prompt_password_if_needed(user_config)

    logger.info(f"Message hash: {get_message_hash(message_text)}")
    logger.info(f"Found {len(addresses)} addresses in total.")
    sent_addresses, unsent_addresses = split_addresses_by_sent(addresses, message_text)
    logger.info(
        f"Of {len(addresses)} total addresses, {len(sent_addresses)} have already been sent to."
    )

    if unsent_addresses:
        logger.info(f"Will send to remaining {len(unsent_addresses)}")
    else:
        logger.info("No more messages to send.")
        exit(0)
    n_failures = 0
    for address in tqdm.tqdm(unsent_addresses, desc="Sending messages"):
        message = build_message(
            message_text=message_text,
            address=address,
            user_config=user_config,
            subject=subject,
        )
        failures = send_message(
            message=message, addresses=address, user_config=user_config
        )
        register_result(message_text, [address], failures)
        n_failures += len(failures)
    if n_failures:
        logger.info(
            f"Failed to send {n_failures} messages out of {len(unsent_addresses)}."
        )
    else:
        logger.info("All messages sent successfully.")


if __name__ == "__main__":
    app()
