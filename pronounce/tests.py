from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, ANY
from urllib.error import URLError
import requests
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
        mock_post.return_value.json.return_value = {
            'status': 'ok',
            'text_score': {
                'score': 90,
                'score_ielts': 8,
                'word_score_list': [
                    {'phone_score_list': [{'phone': 't', 'score': 80}]}
                ],
            },
        }
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['score'], 90)
        self.assertEqual(data['ielts'], 8)
        self.assertEqual(data['phonemes'][0]['phone'], 't')
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('data', kwargs)
        self.assertIn('params', kwargs)
        self.assertEqual(kwargs['data']['user_text'], 'test')
        self.assertEqual(kwargs['params']['text'], 'test')

    @patch('requests.post')
    def test_api_error_message(self, mock_post):
        mock_post.return_value.json.return_value = {
            'status': 'error',
            'short_message': 'error_missing_parameters',
        }
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'error_missing_parameters')

    def test_post_audio_without_requests(self):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        with patch.dict('sys.modules', {'requests': None}):
            class Dummy(io.BytesIO):
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            resp = Dummy(b'{"status":"ok","text_score":{"score":80,"word_score_list":[]}}')
            with patch('urllib.request.urlopen', return_value=resp):
                response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['score'], 80)

    @patch('requests.post', side_effect=requests.exceptions.RequestException('boom'))
    def test_network_error_requests(self, mock_post):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
        self.assertEqual(response.status_code, 502)
        self.assertIn('Network error', response.json()['error'])

    def test_network_error_urllib(self):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        with patch.dict('sys.modules', {'requests': None}):
            with patch('urllib.request.urlopen', side_effect=URLError('fail')):
                response = self.client.post(reverse('pronounce'), {'word': 'test', 'audio': dummy_audio})
                self.assertEqual(response.status_code, 502)
                self.assertIn('Network error', response.json()['error'])

    def test_missing_word(self):
        dummy_audio = SimpleUploadedFile('test.wav', b'\x00\x00', content_type='audio/wav')
        response = self.client.post(reverse('pronounce'), {'audio': dummy_audio})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Missing parameter: word')

    def test_missing_audio(self):
        response = self.client.post(reverse('pronounce'), {'word': 'test'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Missing audio file')
