from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date


class AgeFormViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester',
            password='complexpass123'
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('age_form'))
        login_url = reverse('login') + '?next=' + reverse('age_form')
        self.assertRedirects(response, login_url)

    def test_age_calculation_logged_in(self):
        self.client.login(username='tester', password='complexpass123')
        response = self.client.post(reverse('age_form'), {
            'name': 'Test',
            'birthday': '2000-01-01'
        })
        today = date.today()
        expected_age = today.year - 2000 - ((today.month, today.day) < (1, 1))
        self.assertContains(response, str(expected_age))
