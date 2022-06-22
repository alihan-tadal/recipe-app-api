"""Tests for the user API."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """The public features of the API."""
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = {
            'email': 'example@example.com',
            'password': 'afasdfasfd21',
            'name': 'name31',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        user = get_user_model().objects.get(email=payload['email'])
        # Assertions.
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            'email': 'example@example.com',
            'password': 'afasdfasfd21',
            'name': 'name31',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        # Assertions.
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test error returned if password is shorter than 5 chars."""
        payload = {
            'email': 'example@example.com',
            'password': '123',
            'name': 'name31',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        # Make sure that the user not created.
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        # Assertions.
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generate tokens for valid credentials."""
        user_details = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'test-user-password3',
        }
        create_user(**user_details)
        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)
        # Assertions.
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_for_bad_credentials(self):
        """Test returns error if credentials invalid."""
        # create_user(email='main@main.com', password='goodpass')
        payload = {'email': '', 'password': 'badpass'}
        res = self.client.post(TOKEN_URL, payload)
        # Assertions.
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {'email': 'test@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)
        # Assertions.
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        res = self.client.get(ME_URL)
        # Assertions.
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name='testname',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)
        # Assertions.
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name,
        })

    def test_post_me_not_allowed(self):
        """Test POST not allowed for the me endpoint."""
        res = self.client.post(ME_URL, {})
        # Assertion.
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {
            'name': 'updated name',
            'password': 'new_password',
        }
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        # Assertions.
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
