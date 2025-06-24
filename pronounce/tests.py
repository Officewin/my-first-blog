from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, ANY
from urllib.error import URLError
import requests
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import sys
from django.contrib.auth import get_user_model

class PronounceViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester", password="complexpass123"
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("pronounce"))
        login_url = reverse("login") + "?next=" + reverse("pronounce")
        self.assertRedirects(response, login_url)

    def test_get_random_word_page_logged_in(self):
        self.client.login(username="tester", password="complexpass123")
        response = self.client.get(reverse("pronounce"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Say the following word:")

    @patch('requests.post')
    def test_post_audio(self, mock_post):
        mock_post.return_value.text = 'ok'
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        self.client.login(username='tester', password='complexpass123')
        response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ok')
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('data', kwargs)
        self.assertIn('params', kwargs)
        self.assertEqual(kwargs['data']['user_text'], 'test')
        self.assertEqual(kwargs['params']['text'], 'test')

    def test_post_audio_without_requests(self):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        with patch.dict('sys.modules', {'requests': None}):
            class Dummy(io.BytesIO):
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            resp = Dummy(b'ok')
            with patch('urllib.request.urlopen', return_value=resp):
                self.client.login(username='tester', password='complexpass123')
                response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'ok')

    @patch('requests.post', side_effect=requests.exceptions.RequestException('boom'))
    def test_network_error_requests(self, mock_post):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        self.client.login(username='tester', password='complexpass123')
        response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
        self.assertEqual(response.status_code, 502)
        self.assertIn('Network error', response.content.decode())

    def test_network_error_urllib(self):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        with patch.dict('sys.modules', {'requests': None}):
            with patch('urllib.request.urlopen', side_effect=URLError('fail')):
                self.client.login(username='tester', password='complexpass123')
                response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
                self.assertEqual(response.status_code, 502)
                self.assertIn('Network error', response.content.decode())

    def test_missing_word(self):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        self.client.login(username='tester', password='complexpass123')
        response = self.client.post(reverse('pronounce'), {'audio': dummy_audio})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing parameter: word', response.content.decode())

    def test_missing_audio(self):
        self.client.login(username='tester', password='complexpass123')
        response = self.client.post(reverse('pronounce'), {'word': 'test'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing audio file', response.content.decode())

    def test_history_requires_login(self):
        response = self.client.get(reverse('pronounce_history'))
        login_url = reverse('login') + '?next=' + reverse('pronounce_history')
        self.assertRedirects(response, login_url)

    @patch('requests.post')
    def test_history_shows_saved_entry(self, mock_post):
        mock_post.return_value.text = '{"ielts_score":{"pronunciation":2}}'
        self.client.login(username='tester', password='complexpass123')
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
        resp = self.client.get(reverse('pronounce_history'))
        self.assertContains(resp, 'test')

    def test_history_handles_missing_table(self):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS pronounce_pronunciationhistory')
        self.client.login(username='tester', password='complexpass123')
        resp = self.client.get(reverse('pronounce_history'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'No history yet')
        self.assertContains(resp, 'python manage.py migrate')
