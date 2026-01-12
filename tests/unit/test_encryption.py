"""Tests for API key encryption module.

TDD: These tests are written FIRST before implementation.
"""
import os
import pytest


class TestKeyEncryption:
    """Test the KeyEncryption class."""

    def test_should_create_encryption_instance(self):
        """Test creating an encryption instance."""
        from providers.encryption import KeyEncryption

        encryption = KeyEncryption()
        assert encryption is not None

    def test_should_encrypt_api_key(self):
        """Test encrypting an API key."""
        from providers.encryption import KeyEncryption

        encryption = KeyEncryption()
        api_key = "sk-test-key-12345"

        encrypted = encryption.encrypt(api_key)

        assert encrypted is not None
        assert encrypted != api_key
        assert len(encrypted) > 0

    def test_should_decrypt_api_key(self):
        """Test decrypting an encrypted API key."""
        from providers.encryption import KeyEncryption

        encryption = KeyEncryption()
        original_key = "sk-test-key-12345"

        encrypted = encryption.encrypt(original_key)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original_key

    def test_should_produce_different_ciphertext_each_time(self):
        """Test that encryption produces different ciphertext (due to IV)."""
        from providers.encryption import KeyEncryption

        encryption = KeyEncryption()
        api_key = "sk-test-key"

        encrypted1 = encryption.encrypt(api_key)
        encrypted2 = encryption.encrypt(api_key)

        # Fernet uses random IV, so same plaintext produces different ciphertext
        assert encrypted1 != encrypted2

        # But both should decrypt to same value
        assert encryption.decrypt(encrypted1) == api_key
        assert encryption.decrypt(encrypted2) == api_key

    def test_should_use_provided_master_key(self):
        """Test using a provided master key."""
        from providers.encryption import KeyEncryption
        from cryptography.fernet import Fernet

        # Generate a valid Fernet key
        master_key = Fernet.generate_key().decode()

        encryption = KeyEncryption(master_key=master_key)
        api_key = "test-api-key"

        encrypted = encryption.encrypt(api_key)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == api_key

    def test_should_use_environment_variable_for_master_key(self, monkeypatch):
        """Test using PROVIDER_MASTER_KEY environment variable."""
        from providers.encryption import KeyEncryption
        from cryptography.fernet import Fernet

        # Set env var
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("PROVIDER_MASTER_KEY", test_key)

        encryption = KeyEncryption()
        api_key = "env-test-key"

        encrypted = encryption.encrypt(api_key)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == api_key

    def test_should_generate_master_key_if_not_provided(self):
        """Test that a master key is generated if not provided."""
        from providers.encryption import KeyEncryption

        # Clear any env var
        if "PROVIDER_MASTER_KEY" in os.environ:
            del os.environ["PROVIDER_MASTER_KEY"]

        encryption = KeyEncryption()

        # Should still work
        encrypted = encryption.encrypt("test")
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == "test"

    def test_should_fail_to_decrypt_with_wrong_key(self):
        """Test that decryption fails with wrong key."""
        from providers.encryption import KeyEncryption
        from cryptography.fernet import Fernet, InvalidToken

        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        encryption1 = KeyEncryption(master_key=key1)
        encryption2 = KeyEncryption(master_key=key2)

        encrypted = encryption1.encrypt("secret-key")

        with pytest.raises(InvalidToken):
            encryption2.decrypt(encrypted)

    def test_should_handle_empty_string(self):
        """Test encrypting and decrypting empty string."""
        from providers.encryption import KeyEncryption

        encryption = KeyEncryption()

        encrypted = encryption.encrypt("")
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == ""

    def test_should_handle_long_api_keys(self):
        """Test handling very long API keys."""
        from providers.encryption import KeyEncryption

        encryption = KeyEncryption()
        long_key = "sk-" + "x" * 1000

        encrypted = encryption.encrypt(long_key)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == long_key

    def test_should_mask_api_key(self):
        """Test masking API key for display."""
        from providers.encryption import KeyEncryption

        encryption = KeyEncryption()

        assert encryption.mask("sk-12345678") == "sk-1...5678"
        assert encryption.mask("short") == "s...ort"
        assert encryption.mask("ab") == "**"
        assert encryption.mask("") == ""

    def test_should_validate_api_key_format(self):
        """Test validating API key formats."""
        from providers.encryption import KeyEncryption

        encryption = KeyEncryption()

        # Valid formats
        assert encryption.is_valid_key_format("sk-12345678901234567890") is True
        assert encryption.is_valid_key_format("AIza" + "x" * 35) is True  # Google format

        # Invalid formats
        assert encryption.is_valid_key_format("") is False
        assert encryption.is_valid_key_format("   ") is False
        assert encryption.is_valid_key_format("short") is False
