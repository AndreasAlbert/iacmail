from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import hashlib
from getpass import getpass
from pathlib import Path
import smtplib
import socket
import ssl
import logging
import yaml

logger = logging.getLogger(__name__)


def prompt_password_if_needed(user_config: dict):
    if "password" in user_config:
        return user_config
    password = getpass("Type your password and press enter: ")
    user_config["password"] = password
    return user_config


def get_message_hash(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def read_address_file(address_file: Path) -> list[str]:
    """Read address file, assuming each line is one email address"""
    addresses = [line.strip() for line in address_file.read_text().splitlines()]
    return addresses


def read_message_file(message_file: Path) -> str:
    """Read message body from a file."""
    return message_file.read_text()


def read_user_config_file(user_config_file: Path) -> dict:
    """Read user configuration from a YAML file."""
    return yaml.load(user_config_file.read_text(), Loader=yaml.SafeLoader)


def build_message(message_text: str, address: str, subject: str, user_config: dict,html:bool = False, attachments: list[Path] | None = None) -> MIMEMultipart:
    """Generates a MIMEMultiPart representation of a message"""
    message = MIMEMultipart()
    message["From"] = formataddr((user_config["sender_name"], user_config["sender_email"]))
    message["To"] = address
    message["Subject"] = subject
    # message["Bcc"] = user_config["sender_email"]

    # Attachments
    for file in attachments or ():
        with open(file, "rb") as f:
            part = MIMEApplication(
                f.read(),
                Name=file.name
            )
    
        # After the file is closed
        part['Content-Disposition'] = f'attachment; filename="{file.name}"'
        message.attach(part)
        
    mimetype = "html" if html else "plain"
    message.attach(MIMEText(message_text, mimetype))
    return message



def send_message(
    message: MIMEMultipart, addresses: list[str], user_config: dict
) -> dict:
    context = ssl.create_default_context()
    if isinstance(addresses, str):
        addresses = [addresses]

    try:
        # Server setup        
        try:
            logger.debug(
                f"Connection to server {user_config['smtp_server']} on port {user_config['smtp_port']}."
            )
            server = smtplib.SMTP(user_config["smtp_server"], user_config["smtp_port"])
        except socket.gaierror as exc:
            raise RuntimeError(
                "Could not establish server object: Is your internet connection OK? Server details correct?"
            ) from exc

        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(user_config["sender_email"], user_config["password"])

        text = message.as_string()
        failures = server.sendmail(
            from_addr=user_config["sender_email"],
            to_addrs=addresses + [user_config["sender_email"]],
            msg=text
            )
    except smtplib.SMTPRecipientsRefused as exc:
        failures = exc.recipients
    finally:
        server.quit()

    return failures