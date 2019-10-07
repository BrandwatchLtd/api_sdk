# coding=utf-8
"""
credentials contains the CredentialsStore class, which responsible for persisting access tokens to disk.
"""

import logging
import os
from pathlib import Path

DEFAULT_CREDENTIALS_PATH = Path(os.path.expanduser("~")) / ".bwapi" / "credentials.txt"

logger = logging.getLogger("bwapi")


class CredentialsStore:
    """
    CredentialsStore is responsible for persisting access tokens to disk.
    """

    def __init__(self, credentials_path=None):
        """
        Create a new CredentialsStore

        :param credentials_path: Path to the credentials file
        """
        if credentials_path is None:
            credentials_path = DEFAULT_CREDENTIALS_PATH
        self._credentials_path = Path(credentials_path)

    def __getitem__(self, username):
        """ Get self[username] """
        user_tokens = self._read()
        return user_tokens[username.lower()]

    def __setitem__(self, username, token):
        """ Set self[username] to access token. """
        credentials = self._read()
        if username.lower() in credentials:
            if credentials[username.lower()] == token:
                return
            else:
                logger.info(
                    "Overwriting access token for %s in %s",
                    username,
                    self._credentials_path,
                )
        else:
            logger.info("Writing access token for user: %s", username)
        credentials[username.lower()] = token
        self._write(credentials)

    def __delitem__(self, username):
        """ Delete self[username]. """
        credentials = self._read()
        if username.lower() in credentials:
            logger.info("Deleting access token for user: %s", username)
            del credentials[username.lower()]
            self._write(credentials)

    def __iter__(self):
        """ Implement iter(self). """
        credentials = self._read()
        yield from credentials.items()

    def __len__(self):
        return len(self._read())

    def _write(self, credentials):
        self._ensure_file_exists()
        with open(str(self._credentials_path), "w") as token_file:
            contents = "\n".join(["\t".join(item) for item in credentials.items()])
            token_file.write(contents)

    def _read(self):
        self._ensure_file_exists()
        with open(str(self._credentials_path)) as token_file:
            credentials = dict()
            for line in token_file:
                try:
                    user, token = line.split()
                except ValueError:
                    logger.warning('Ignoring corrupted credentials line: "%s"', line)
                    pass
                credentials[user.lower()] = token
            return credentials

    def _ensure_file_exists(self):
        self._ensure_dir_exists()
        if not self._credentials_path.exists():
            logger.debug("Creating credentials store: %s", self._credentials_path)
            self._credentials_path.touch(mode=0o600)

    def _ensure_dir_exists(self):
        if not self._credentials_path.parent.exists():
            logger.debug(
                "Creating credentials store parent directory: %s",
                self._credentials_path.parent,
            )
            self._credentials_path.parent.mkdir(parents=True, mode=0o755)
