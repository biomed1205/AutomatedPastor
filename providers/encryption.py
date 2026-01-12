"""Secure API key encryption module using Fernet symmetric encryption.

This module provides secure encryption and decryption of API keys for
multi-AI provider integration. It uses the cryptography library's Fernet
implementation which provides:
- AES-128-CBC encryption
- HMAC using SHA256 for authentication
- Timestamps for optional TTL enforcement
- URL-safe base64 encoding
"""
import os
import re
from typing import Optional

from cryptography.fernet import Fernet


class KeyEncryption:
    """Handles secure encryption and decryption of API keys.

    Uses Fernet symmetric encryption which provides authenticated encryption
    with associated data (AEAD). Each encryption operation uses a unique IV,
    ensuring the same plaintext produces different ciphertext each time.

    Attributes:
        _fernet: The Fernet cipher instance used for encryption/decryption.

    Example:
        >>> encryption = KeyEncryption()
        >>> encrypted = encryption.encrypt("sk-my-api-key")
        >>> original = encryption.decrypt(encrypted)
        >>> assert original == "sk-my-api-key"
    """

    # Environment variable name for the master encryption key
    ENV_MASTER_KEY = "PROVIDER_MASTER_KEY"

    # Minimum length for API keys to be considered valid
    MIN_KEY_LENGTH = 10

    def __init__(self, master_key: Optional[str] = None):
        """Initialize the encryption handler.

        Args:
            master_key: Optional base64-encoded Fernet key. If not provided,
                        the key is read from PROVIDER_MASTER_KEY environment
                        variable. If neither is available, a new key is
                        generated (note: this key will be lost on restart).

        Raises:
            ValueError: If the provided master_key is not a valid Fernet key.
        """
        if master_key is not None:
            # Use provided key
            key = master_key.encode() if isinstance(master_key, str) else master_key
        elif self.ENV_MASTER_KEY in os.environ:
            # Use environment variable
            key = os.environ[self.ENV_MASTER_KEY].encode()
        else:
            # Generate a new key (warning: not persistent!)
            key = Fernet.generate_key()

        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt an API key.

        Args:
            plaintext: The API key to encrypt.

        Returns:
            URL-safe base64-encoded encrypted string.

        Note:
            Each call produces different ciphertext due to unique IV,
            even for the same plaintext.
        """
        # Encode string to bytes, encrypt, and decode back to string
        ciphertext = self._fernet.encrypt(plaintext.encode())
        return ciphertext.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt an encrypted API key.

        Args:
            ciphertext: The encrypted API key (URL-safe base64).

        Returns:
            The original plaintext API key.

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails due to
                wrong key, corrupted data, or expired token.
        """
        # Encode string to bytes, decrypt, and decode back to string
        plaintext = self._fernet.decrypt(ciphertext.encode())
        return plaintext.decode()

    def mask(self, api_key: str) -> str:
        """Mask an API key for display purposes.

        Reveals only the first 4 and last 4 characters, replacing
        the middle with ellipsis for security.

        Args:
            api_key: The API key to mask.

        Returns:
            Masked version of the key, e.g., "sk-1...5678"

        Examples:
            >>> encryption.mask("sk-12345678")
            'sk-1...5678'
            >>> encryption.mask("short")
            's...ort'
            >>> encryption.mask("ab")
            '**'
            >>> encryption.mask("")
            ''
        """
        if not api_key:
            return ""

        length = len(api_key)

        if length <= 4:
            # Too short to meaningfully mask - just show asterisks
            return "*" * length

        if length <= 8:
            # Show first and last character with ellipsis
            return f"{api_key[0]}...{api_key[-3:]}"

        # Show first 4 and last 4 characters
        return f"{api_key[:4]}...{api_key[-4:]}"

    def is_valid_key_format(self, api_key: str) -> bool:
        """Validate that an API key has a reasonable format.

        This performs basic format validation to catch obvious errors
        like empty strings or whitespace-only inputs. It does NOT
        verify that the key is actually valid with the provider.

        Args:
            api_key: The API key to validate.

        Returns:
            True if the key has a valid format, False otherwise.

        Note:
            Different providers have different key formats:
            - OpenAI: sk-... (typically 51 characters)
            - Anthropic: sk-ant-... (variable length)
            - Google: AIza... (39 characters)
            - Mistral: various formats
        """
        if not api_key:
            return False

        # Check for whitespace-only
        if api_key.strip() == "":
            return False

        # Check minimum length
        if len(api_key) < self.MIN_KEY_LENGTH:
            return False

        # Key passes basic validation
        return True

    @staticmethod
    def generate_master_key() -> str:
        """Generate a new Fernet master key.

        Returns:
            A URL-safe base64-encoded key suitable for use as a master key.

        Note:
            Store this key securely! It's recommended to set it as the
            PROVIDER_MASTER_KEY environment variable.
        """
        return Fernet.generate_key().decode()
