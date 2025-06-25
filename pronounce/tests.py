from django.test import TestCase
from django.urls import reverse
import datetime
from unittest.mock import patch, ANY
from urllib.error import URLError
import requests
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import sys
from django.contrib.auth import get_user_model
from pronounce.models import DailyPractice, DailySubmission

class PronounceViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester", password="complexpass123"
        )

    def _init_session(self, words=None, index=0):
        if words is None:
            words = ['test'] + [f"w{i}" for i in range(1,10)]
        today = datetime.date.today()
        # Ensure tests use the same timezone-aware date as the view
        try:
            from django.utils import timezone
            today = timezone.now().date()
        except Exception:
            pass
        DailyPractice.objects.update_or_create(
            user=self.user,
            date=today,
            defaults={"words": words, "index": index, "level": "beginner"},
        )
        DailySubmission.objects.update_or_create(
            user=self.user,
            date=today,
            defaults={"count": index},
        )
        return words

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("pronounce"))
        login_url = reverse("login") + "?next=" + reverse("pronounce")
        self.assertRedirects(response, login_url)

    def test_select_level_first_visit(self):
        self.client.login(username="tester", password="complexpass123")
        resp = self.client.get(reverse("pronounce"))
        self.assertContains(resp, "Select Practice Level")

    def test_choose_advanced_level(self):
        self.client.login(username="tester", password="complexpass123")
        resp = self.client.get(reverse("pronounce") + "?level=advanced")
        self.assertContains(resp, "Say the following word:")
        from django.utils import timezone
        record = DailyPractice.objects.get(user=self.user, date=timezone.now().date())
        self.assertEqual(record.level, "advanced")

    def test_get_random_word_page_logged_in(self):
        self.client.login(username="tester", password="complexpass123")
        self._init_session()
        response = self.client.get(reverse("pronounce"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Say the following word:")

    @patch('requests.post')
    def test_post_audio(self, mock_post):
        mock_post.return_value.text = 'ok'
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        self.client.login(username='tester', password='complexpass123')
        words = self._init_session()
        response = self.client.post(reverse('pronounce'), {'word': words[0], 'audio': dummy_audio})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ok')
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('data', kwargs)
        self.assertIn('params', kwargs)
        self.assertEqual(kwargs['data']['user_text'], words[0])
        self.assertEqual(kwargs['params']['text'], words[0])

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
                words = self._init_session()
                response = self.client.post(reverse('pronounce'), {'word': words[0], 'audio': dummy_audio})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'ok')

    @patch('requests.post', side_effect=requests.exceptions.RequestException('boom'))
    def test_network_error_requests(self, mock_post):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        self.client.login(username='tester', password='complexpass123')
        words = self._init_session()
        response = self.client.post(reverse('pronounce'), {'word': words[0], 'audio': dummy_audio})
        self.assertEqual(response.status_code, 502)
        self.assertIn('Network error', response.content.decode())

    def test_network_error_urllib(self):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        with patch.dict('sys.modules', {'requests': None}):
            with patch('urllib.request.urlopen', side_effect=URLError('fail')):
                self.client.login(username='tester', password='complexpass123')
                words = self._init_session()
                response = self.client.post(reverse('pronounce'), {'word': words[0], 'audio': dummy_audio})
                self.assertEqual(response.status_code, 502)
                self.assertIn('Network error', response.content.decode())

    def test_missing_word(self):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        self.client.login(username='tester', password='complexpass123')
        self._init_session()
        response = self.client.post(reverse('pronounce'), {'audio': dummy_audio})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing parameter: word', response.content.decode())

    def test_missing_audio(self):
        self.client.login(username='tester', password='complexpass123')
        words = self._init_session()
        response = self.client.post(reverse('pronounce'), {'word': words[0]})
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
        words = self._init_session()
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        self.client.post(reverse('pronounce'), {'word': words[0], 'audio': dummy_audio})
        resp = self.client.get(reverse('pronounce_history'))
        self.assertContains(resp, 'test')
        self.assertContains(resp, '2')

    def test_history_handles_missing_table(self):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS pronounce_pronunciationhistory')
        self.client.login(username='tester', password='complexpass123')
        resp = self.client.get(reverse('pronounce_history'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'No history yet')
        self.assertContains(resp, 'python manage.py migrate')

    def test_history_parses_string_payload(self):
        from pronounce.models import PronunciationHistory
        self.client.login(username='tester', password='complexpass123')
        PronunciationHistory.objects.create(
            user=self.user,
            text='foo',
            response='{"ielts_score":{"pronunciation":7.0}}'
        )
        resp = self.client.get(reverse('pronounce_history'))
        self.assertContains(resp, 'foo')
        self.assertContains(resp, '7.0')

    @patch('requests.post')
    def test_daily_limit(self, mock_post):
        mock_post.return_value.text = '{}'
        self.client.login(username='tester', password='complexpass123')
        words = self._init_session([f'w{i}' for i in range(10)])
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        for i in range(10):
            resp = self.client.post(reverse('pronounce'), {'word': words[i], 'audio': dummy_audio})
            self.assertEqual(resp.status_code, 200)
        resp = self.client.post(reverse('pronounce'), {'word': 'extra', 'audio': dummy_audio})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Daily submission limit reached', resp.content.decode())

    @patch('requests.post')
    def test_progress_persists_across_sessions(self, mock_post):
        mock_post.return_value.text = '{}'
        self.client.login(username='tester', password='complexpass123')
        words = self._init_session(['a', 'b', 'c'])
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        self.client.post(reverse('pronounce'), {'word': words[0], 'audio': dummy_audio})
        self.client.logout()
        from django.test import Client
        self.client = Client()
        self.client.login(username='tester', password='complexpass123')
        resp = self.client.get(reverse('pronounce'))
        self.assertContains(resp, 'Practice 1 / 3')

    @patch("requests.post")
    def test_daily_limit_persists_across_sessions(self, mock_post):
        mock_post.return_value.text = "{}"
        self.client.login(username="tester", password="complexpass123")
        words = self._init_session([f"w{i}" for i in range(10)])
        dummy_audio = SimpleUploadedFile("test.wav", b"\x00\x00", content_type="audio/wav")
        for i in range(5):
            resp = self.client.post(reverse("pronounce"), {"word": words[i], "audio": dummy_audio})
            self.assertEqual(resp.status_code, 200)
        self.client.logout()
        from django.test import Client
        self.client = Client()
        self.client.login(username="tester", password="complexpass123")
        for i in range(5, 10):
            resp = self.client.post(reverse("pronounce"), {"word": words[i], "audio": dummy_audio})
            self.assertEqual(resp.status_code, 200)
        resp = self.client.post(reverse("pronounce"), {"word": "extra", "audio": dummy_audio})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Daily submission limit reached", resp.content.decode())

    def test_unexpected_word(self):
        self.client.login(username='tester', password='complexpass123')
        words = self._init_session(['a', 'b', 'c'])
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        resp = self.client.post(reverse('pronounce'), {'word': 'wrong', 'audio': dummy_audio})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Unexpected word', resp.content.decode())
