from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile

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
