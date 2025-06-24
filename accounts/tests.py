from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class SignupViewTests(TestCase):
    def test_signup_page(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign Up')

    def test_signup_creates_user(self):
        self.client.post(reverse('signup'), {
            'username': 'tester',
            'email': 'tester@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        })
        user = get_user_model().objects.filter(username='tester').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'tester@example.com')
