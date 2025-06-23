import configparser
import csv
import os
import sys
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import NamedTuple

import aiofiles
from aiosmtplib import SMTP
from colorama import Fore, Style
from email_validator import EmailNotValidError, validate_email


@dataclass
class SMTPCredentials:
    """SMTP credentials class."""

    hostname: str
    port: int
    username: str
    password: str


class Recipient(NamedTuple):
    """Recipient data."""

    name: str
    email: str


class ConfigLoader:
    """Class for loading configuration from `config.ini` file."""

    def __init__(self):
        self.config_path = self._get_config_path()

    def _get_config_path(self) -> str:
        base_dir = os.path.dirname(
            sys.executable if getattr(sys, "frozen", False) else __file__
        )
        return os.path.join(base_dir, "config.ini")

    async def load(self) -> tuple[SMTPCredentials, str]:
        """
        Load configuration from `config.ini` file.

        Returns:
            tuple(SMTPCredentials, str): SMTPCredentials and path to csv file with recipients data.
        """

        print(
            f"Loaded configuration from {Fore.LIGHTYELLOW_EX}{self.config_path}{Fore.RESET}"
        )

        config = configparser.ConfigParser()
        async with aiofiles.open(self.config_path, "r") as f:
            content = await f.read()

        config.read_string(content)
        smtp = config["SMTPCredentials"]
        recipients = config["Recipients"]

        credentials = SMTPCredentials(
            hostname=smtp["hostname"],
            port=int(smtp["port"]),
            username=smtp["username"],
            password=smtp["password"],
        )

        try:
            validate_email(credentials.username, check_deliverability=False)
        except EmailNotValidError:
            print(f"{Fore.RED}Invalid SMTP username email format.{Style.RESET_ALL}")
            raise

        recipients_csv_path = recipients["recipients_csv_path"]
        if not os.path.isfile(recipients_csv_path):
            print(
                f"{Fore.RED}Invalid CSV file path: {recipients_csv_path}{Style.RESET_ALL}"
            )
            raise FileNotFoundError(recipients_csv_path)

        return credentials, recipients_csv_path


class RecipientLoader:
    """Class for loading recipients from a CSV file."""

    @staticmethod
    async def load_from_csv(csv_path: str) -> list[Recipient]:
        """
        Load recipients from a CSV file.

        Returns:
            list[Recipient]: List of Recipient objects loaded from the CSV file.
        """

        print(
            f"Loading recipients list from {Fore.LIGHTYELLOW_EX}{csv_path}{Fore.RESET}"
        )
        recipients: list[Recipient] = []

        async with aiofiles.open(csv_path, "r", encoding="utf-8") as f:
            lines = await f.readlines()
            reader = csv.DictReader(lines)
            for row in reader:
                email = row.get("recipient")
                name = row.get("recipient_name", "")
                try:
                    validate_email(email, check_deliverability=False)
                    recipients.append(Recipient(name=name, email=email))
                except EmailNotValidError:
                    print(f"{Fore.RED}Invalid email skipped: {email}{Fore.RESET}")
        return recipients


class SMTPMailer:
    """Class for sending emails using SMTP."""

    def __init__(self):
        self.client: SMTP
        self.recipients: list[Recipient] = []
        self.subject = ""
        self.body = ""

    async def _setup_client(self, credentials: SMTPCredentials):
        """
        Set up the SMTP client with the provided credentials.

        Raises:
            ConnectionError: If there is an error connecting to the SMTP server.
        """

        self.client = SMTP(
            hostname=credentials.hostname,
            port=credentials.port,
            username=credentials.username,
            password=credentials.password,
            use_tls=True,
        )
        try:
            response = await self.client.connect(timeout=5)
            if response.code != 220:
                raise ConnectionError(f"SMTP connect error: {response}")
            print(f"{Fore.GREEN}Connected to SMTP server successfully.{Fore.RESET}\n")
        except Exception as e:
            print(f"{Fore.RED}Failed to connect to SMTP server: {e}{Fore.RESET}")
            raise

    def _get_multiline_input(self, prompt: str) -> str:
        """Get multiline input from the user until a specific end marker is entered."""

        end_marker = "--end"
        print(f"{prompt} (enter '--end' at the new line to complete):\n")
        lines = []
        while True:
            line = input()
            if line.strip() == end_marker:
                break
            lines.append(line)
        return "\n".join(lines)

    def _get_user_input(self):
        """Get subject and body of the email from the user."""

        self.subject = input(f"{Fore.CYAN}Enter message subject:{Fore.RESET}\n")
        self.body = self._get_multiline_input(
            f"{Fore.GREEN}Enter message body:{Fore.RESET}"
        )

    async def _dispatch_messages(self, sender_email: str):
        """Send messages to all recipients."""

        print(f"{Fore.LIGHTYELLOW_EX}Sending messages to recipients...{Fore.RESET}")

        async with self.client:
            for recipient in self.recipients:
                msg_text = self.body.format(name=recipient.name)
                message = MIMEText(msg_text, _charset="utf-8")
                message["Subject"] = self.subject
                message["From"] = sender_email
                message["To"] = recipient.email

                try:
                    await self.client.send_message(message)
                except Exception as ex:
                    print(
                        f"{Fore.RED}Failed to send to {recipient.email}: {ex}{Fore.RESET}"
                    )

        print(f"{Fore.GREEN}All messages sent successfully.{Fore.RESET}")

    async def send_emails(self):
        """
        Main method to send emails using the SMTP client.

        Loads configuration, sets up the SMTP client, gets user input
        for subject and body, sends emails to recipients.

        Raises:
            FileNotFoundError: If the recipients CSV file is not found.
            EmailNotValidError: If the SMTP username email format is invalid.
            ConnectionError: If there is an error connecting to the SMTP server.
        """

        credentials, recipients_csv_path = await ConfigLoader().load()
        await self._setup_client(credentials)

        self.recipients = await RecipientLoader.load_from_csv(recipients_csv_path)
        self._get_user_input()
        await self._dispatch_messages(credentials.username)


if __name__ == "__main__":
    import asyncio

    asyncio.run(SMTPMailer().send_emails())
