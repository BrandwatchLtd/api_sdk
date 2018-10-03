# coding=utf-8
"""
credentials contains the CredentialsStore class, which responsible for persisting access tokens to disk.
"""

import logging
from pathlib import Path
from typing import Mapping

DEFAULT_CREDENTIALS_PATH = Path.home() / '.bwapi' / "credentials.txt"

logger = logging.getLogger("bwapi")


class CredentialsStore:
    """
    CredentialsStore is responsible for persisting access tokens to disk.
    """

    _credentials_path: Path

    def __init__(self, credentials_path=DEFAULT_CREDENTIALS_PATH):
        """
        Create a new CredentialsStore

        :param credentials_path: Path to the credentials file
        """
        self._credentials_path = credentials_path

    def __getitem__(self, username: str) -> str:
        """ Get self[username] """
        user_tokens = self._read()
        return user_tokens[username.lower()]

    def __setitem__(self, username: str, token: str):
        """ Set self[username] to access token. """
        credentials = self._read()
        if username.lower() in credentials:
            if credentials[username.lower()] == token:
                return
            else:
                logger.debug("Overwriting access token for user: {}", username)
        else:
            logger.debug("Writing access token for user: {}", username)
        credentials[username.lower()] = token
        self._write(credentials)

    def __delitem__(self, username):
        """ Delete self[username]. """
        credentials = self._read()
        if username.lower() in credentials:
            logger.debug("Deleting access token for user: {}", username)
            del credentials[username.lower()]
            self._write(credentials)

    def __iter__(self):
        """ Implement iter(self). """
        credentials = self._read()
        yield from credentials.items()

    def __len__(self):
        return len(self._read())

    def _write(self, credentials: Mapping[str, str]):
        self._ensure_file_exists()
        with open(self._credentials_path, 'w') as token_file:
            contents = "\n".join(["\t".join(item) for item in credentials.items()])
            token_file.write(contents)

    def _read(self) -> Mapping[str, str]:
        self._ensure_file_exists()
        with open(self._credentials_path) as token_file:
            credentials = dict()
            for line in token_file:
                try:
                    user, token = line.split()
                except ValueError:
                    logger.warning("Ignoring corrupted credentials line: \"{}\"", line)
                    pass
                credentials[user.lower()] = token
            return credentials

    def _ensure_file_exists(self):
        self._ensure_dir_exists()
        if not self._credentials_path.exists():
            logger.debug("Creating credentials store: {}", self._credentials_path)
            self._credentials_path.touch(mode=0o600)

    def _ensure_dir_exists(self):
        if not self._credentials_path.parent.exists():
            logger.debug("Creating credentials store parent directory: {}", self._credentials_path.parent)
            self._credentials_path.parent.mkdir(parents=True, mode=0o755)
