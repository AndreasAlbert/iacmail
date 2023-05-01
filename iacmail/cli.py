import datetime
import functools
import logging
from pathlib import Path
from iacmail.database import register_result, split_addresses_by_sent
from iacmail.util import send_message, build_message

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
session_maker = sa.orm.sessionmaker(bind=engine)
Base.metadata.create_all(engine, checkfirst=True)
logging.basicConfig(level=logging.INFO,format='[%(asctime)s] :: [%(name)s] :: [%(levelname)s] :: %(message)s')




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
    sent_addresses, unsent_addresses = split_addresses_by_sent(session_maker,addresses, message_text)
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
        register_result(session_maker, message_text, [address], failures)
        n_failures += len(failures)
    if n_failures:
        logger.warning(
            f"Failed to send {n_failures} messages out of {len(unsent_addresses)}."
        )
    else:
        logger.info("All messages sent successfully.")


if __name__ == "__main__":
    app()
