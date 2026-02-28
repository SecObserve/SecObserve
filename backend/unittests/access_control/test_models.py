from unittest.mock import patch

from django.test import TestCase

from application.access_control.models import JWT_Secret, User


class TestUser(TestCase):
    @patch("django.contrib.auth.models.AbstractUser.save")
    def test_save_first_and_last_name(self, mock):
        user = User(first_name="first", last_name="last", username="user")
        user.save()

        self.assertEqual("first last", user.full_name)
        mock.assert_called()

    @patch("django.contrib.auth.models.AbstractUser.save")
    def test_save_first_name_only(self, mock):
        user = User(first_name="first", username="user")
        user.save()

        self.assertEqual("first", user.full_name)
        mock.assert_called()

    @patch("django.contrib.auth.models.AbstractUser.save")
    def test_save_last_name_only(self, mock):
        user = User(last_name="last", username="user")
        user.save()

        self.assertEqual("last", user.full_name)
        mock.assert_called()

    @patch("django.contrib.auth.models.AbstractUser.save")
    def test_save_no_name(self, mock):
        user = User(username="user")
        user.save()

        self.assertEqual("user", user.full_name)
        mock.assert_called()


class TestJWTSecret(TestCase):
    def setUp(self):
        # Clear any existing JWT_Secret entries
        JWT_Secret.objects.all().delete()

    @patch("application.access_control.models.JWT_Secret.create_secret")
    def test_save_method_creates_new_secret_when_none_exists(self, mock_create_secret):
        """Test that save creates a new secret when none exists"""
        jwt_secret = JWT_Secret()
        mock_create_secret.return_value = "mocked_secret"
        jwt_secret.save()

        # Verify that a new secret was created
        self.assertEqual(jwt_secret.secret, "mocked_secret")

        # Verify that only one entry exists in the database
        self.assertEqual(JWT_Secret.objects.count(), 1)

    @patch("application.access_control.models.JWT_Secret.create_secret")
    def test_save_method_removes_old_entries(self, mock_create_secret):
        """Test that save removes all other entries when saving a new one"""
        # Create initial entries
        JWT_Secret.objects.create(secret="old_secret_1")
        JWT_Secret.objects.create(secret="old_secret_2")

        # Create new entry
        new_jwt_secret = JWT_Secret()
        mock_create_secret.return_value = "new_secret"
        new_jwt_secret.save()

        # Verify only the new entry exists
        self.assertEqual(JWT_Secret.objects.count(), 1)
        self.assertEqual(JWT_Secret.objects.get().secret, "new_secret")

    def test_load_method_returns_existing_secret(self):
        """Test that load returns existing secret when it exists"""
        # Create a secret in the database
        existing_secret = JWT_Secret.objects.create(secret="existing_secret")

        # Load the secret
        loaded_secret = JWT_Secret.load()

        # Verify that the loaded secret is the same as the existing one
        self.assertEqual(loaded_secret, existing_secret)
        self.assertEqual(loaded_secret.secret, "existing_secret")

    @patch("application.access_control.models.JWT_Secret.create_secret")
    def test_load_method_creates_new_secret_when_none_exists(self, mock_create_secret):
        """Test that load creates a new secret when none exists"""
        # Ensure no secrets exist
        JWT_Secret.objects.all().delete()

        mock_create_secret.return_value = "newly_created_secret"
        loaded_secret = JWT_Secret.load()

        # Verify that a new secret was created
        self.assertEqual(loaded_secret.secret, "newly_created_secret")
        self.assertEqual(JWT_Secret.objects.count(), 1)

        # Verify that the secret was saved to the database
        saved_secret = JWT_Secret.objects.get()
        self.assertEqual(saved_secret.secret, "newly_created_secret")

    def test_create_secret(self):
        secret = JWT_Secret.create_secret()
        self.assertEqual(32, len(secret))
