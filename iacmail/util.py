import hashlib
from getpass import getpass
from pathlib import Path

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
