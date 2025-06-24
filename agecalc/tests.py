from django.test import TestCase
from django.urls import reverse
from datetime import date


class AgeFormViewTests(TestCase):
    def test_age_calculation(self):
        response = self.client.post(reverse('age_form'), {
            'name': 'Test',
            'birthday': '2000-01-01'
        })
        today = date.today()
        expected_age = today.year - 2000 - ((today.month, today.day) < (1, 1))
        self.assertContains(response, str(expected_age))
