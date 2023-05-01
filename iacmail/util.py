from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import hashlib
from getpass import getpass
from pathlib import Path
import smtplib
import ssl

import yaml


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


def build_message(message_text: str, address: str, subject: str, user_config: dict) -> MIMEMultipart:
    """Generates a MIMEMultiPart representation of a message"""
    message = MIMEMultipart()
    message["From"] = user_config["sender_email"]
    message["To"] = address
    message["Subject"] = subject
    message["Bcc"] = user_config["sender_email"]

    message.attach(MIMEText(message_text, "plain"))
    return message



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
    finally:
        server.quit()

    return failures