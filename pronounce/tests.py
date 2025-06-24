from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import sys

class PronounceViewTests(TestCase):
    def test_get_random_word_page(self):
        response = self.client.get(reverse('pronounce'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Say the following word:')

    @patch('requests.post')
    def test_post_audio(self, mock_post):
        mock_post.return_value.text = 'ok'
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ok')

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
                response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'ok')
