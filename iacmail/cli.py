import logging
from pathlib import Path
from iacmail.database import register_result, split_addresses_by_sent
from iacmail.util import send_message, build_message
import pandas as pd
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
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] :: [%(name)s] :: [%(levelname)s] :: %(message)s",
)


@app.command()
def bespoke(
    table_path: Path = typer.Option(
        ..., help="File containing one recipient email address per line."
    ),
    address_column: str = typer.Option(..., help="Column name for the email address."),
    message_file: Path = typer.Option(
        ..., help="File containing the body text for the email."
    ),
    user_config_file: Path = typer.Option(
        ..., help="File containting the user configuration."
    ),
    subject: str = typer.Option(..., help="Subject for the email."),
    html: bool = typer.Option(..., help="Whether to use html"),
    attachment: Path = typer.Option(default=None, help="A file to attach."),
    attachment_column: str = typer.Option(
        ..., help="Column name for attachment names."
    ),
):
    table_data = pd.read_excel(table_path).to_dict(orient="records")
    message_text = read_message_file(message_file)
    user_config = read_user_config_file(user_config_file)

    addresses = [row[address_column] for row in table_data]
    user_config = prompt_password_if_needed(user_config)

    logger.info(f"Message hash: {get_message_hash(message_text)}")
    logger.info(f"Found {len(addresses)} addresses in total.")

    sent_addresses, unsent_addresses = split_addresses_by_sent(
        session_maker, addresses, message_text
    )

    if unsent_addresses:
        logger.info(f"Will send to remaining {len(unsent_addresses)}")
    else:
        logger.info("No more messages to send.")
        exit(0)

    n_failures = 0

    unsent_rows = [row for row in table_data if row[address_column] in unsent_addresses]


    for row in tqdm.tqdm(unsent_rows, desc="Sending messages"):
        bespoke_text = message_text.format(**row)

        # Per-recipient attachments
        attachments = [attachment] if attachment else []
        if attachment_column:
            if attachment_column not in row:
                raise ValueError(
                    f"The attachment column '{attachment_column}' was specified but does not exist in the spreadsheet!"
                )
            attachments.append(Path(row[attachment_column]))

        # Check file existance.
        for attachment in attachments:
            if not (attachment.exists() and attachment.is_file()):
                raise FileExistsError(
                    f"Attachment file does not exist or is not a file: {attachment}"
                )

        message = build_message(
            message_text=bespoke_text,
            address=row[address_column],
            user_config=user_config,
            subject=subject,
            html=html,
            attachments=attachments,
        )
        failures = send_message(
            message=message, addresses=row[address_column], user_config=user_config
        )
        register_result(session_maker, message_text, [row[address_column]], failures)
        n_failures += len(failures)
    if n_failures:
        logger.warning(
            f"Failed to send {n_failures} messages out of {len(unsent_addresses)}."
        )
    else:
        logger.info("All messages sent successfully.")


if __name__ == "__main__":
    app()
