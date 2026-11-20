"""Caption payloads reach the video reader, Chat retrieval and saved course pages intact."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import retrieval
import server
from engine import saved_pages


class VideoTranscripts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'captions.vtt'

    def texts(self, data):
        self.path.write_bytes(data)
        with patch.object(server, 'LIB', self.root):
            reader = ' '.join(cue['text'] for cue in server.vtt_cues('captions.vtt'))
        return {
            'reader': reader,
            'retrieval': ' '.join(text for _, text in retrieval.vtt_windows(self.path)),
            'saved page': saved_pages.transcript_text(data),
        }

    def test_numeric_payload_is_not_a_cue_identifier(self):
        data = (b'WEBVTT\n\n17\n00:01.000 --> 00:05.000\n'
                b'The label on this storage container reads\n12\n'
                b'litres, and the number belongs with the words.\n')
        expected = ('The label on this storage container reads 12 '
                    'litres, and the number belongs with the words.')
        for route, text in self.texts(data).items():
            with self.subTest(route=route):
                self.assertEqual(text, expected)

    def test_named_identifiers_do_not_become_spoken_text(self):
        first = 'Keep this first instruction with its own timestamp and wording.'
        second = 'Keep this next instruction with its own timestamp and wording.'
        data = ('WEBVTT\n\nchapter-one\n00:01.000 --> 00:05.000\n' + first +
                '\n\nchapter-two\n00:20.000 --> 00:24.000\n' + second).encode()
        for route, text in self.texts(data).items():
            with self.subTest(route=route):
                self.assertEqual(text, first + ' ' + second)

    def test_comments_and_settings_are_not_spoken_text(self):
        spoken = 'Only this sentence was spoken and should be used as a video source.'
        data = ('WEBVTT\nKind: captions\nLanguage: en\n\n'
                'STYLE\n::cue { color: lime; }\n\n'
                'REGION\nid:region-one\nwidth:40%\n\n'
                'NOTE editor notes\nDo not index this comment.\n'
                '00:00.000 --> 00:01.000\nThis is still inside the comment.\n\n'
                '00:02.000 --> 00:08.000 align:start position:10%\n' + spoken +
                '\n\nNOTE\nNor this trailing comment.\n').encode()
        for route, text in self.texts(data).items():
            with self.subTest(route=route):
                self.assertEqual(text, spoken)

    def test_header_words_inside_a_payload_are_kept(self):
        spoken = ('NOTE this sentence is spoken, not an editor comment. '
                  'Language: these words are also part of the caption.')
        data = ('WEBVTT\n\n00:01.000 --> 00:05.000\n'
                'NOTE this sentence is spoken, not an editor comment.\n'
                'Language: these words are also part of the caption.\n').encode()
        for route, text in self.texts(data).items():
            with self.subTest(route=route):
                self.assertEqual(text, spoken)

    def test_webvtt_identifier_after_header_keeps_its_payload(self):
        first = 'This first caption describes the label on the example container.'
        second = 'This later caption belongs to the cue whose identifier starts with WEBVTT.'
        data = ('WEBVTT\n\n00:01.000 --> 00:05.000\n' + first +
                '\n\nWEBVTT\n00:20.000 --> 00:25.000\n' + second + '\n').encode()
        for route, text in self.texts(data).items():
            with self.subTest(route=route):
                self.assertEqual(text, first + ' ' + second)
        with patch.object(server, 'LIB', self.root):
            self.assertEqual(server.vtt_cues('captions.vtt'),
                             [{'t': 1, 'text': first}, {'t': 20, 'text': second}])

    def test_whitespace_payload_lines_keep_words_and_rolling_cue_start(self):
        first = 'This first caption describes the label on the example container.'
        second = 'The next words explain how this label belongs with the rest of the example.'
        for whitespace in (' ', '\t', ' \t '):
            fixtures = {
                'inside cue': '00:20.000 --> 00:25.000\n' + first + '\n' + whitespace + '\n' + second + '\n',
                'rolling cue': ('00:02.000 --> 00:04.000 align:start position:0%\n' + whitespace + '\n' + first +
                                '\n\n00:04.000 --> 00:06.000 align:start position:0%\n' + first + '\n' + second + '\n'),
            }
            for fixture, payload in fixtures.items():
                data = ('WEBVTT\n\n' + payload).encode()
                for route, text in self.texts(data).items():
                    with self.subTest(whitespace=repr(whitespace), fixture=fixture, route=route):
                        # Consumers format whitespace differently; all spoken words must survive in order.
                        self.assertEqual(text.split(), (first + ' ' + second).split())
                expected_start = 2 if fixture == 'rolling cue' else 20
                with patch.object(server, 'LIB', self.root):
                    starts = {'reader': server.vtt_cues('captions.vtt')[0]['t'],
                              'retrieval': retrieval.vtt_windows(self.path)[0][0]}
                for route, start in starts.items():
                    with self.subTest(whitespace=repr(whitespace), fixture=fixture, route=route + ' timestamp'):
                        self.assertEqual(start, expected_start)

    def test_line_endings_bom_and_final_cue_without_blank_line(self):
        spoken = 'This final caption is complete even without a trailing blank line.'
        for newline in ('\n', '\r\n', '\r'):
            data = ('\ufeffWEBVTT\n\ncue-one\n01:02:03.000 --> 01:02:06.000\n' +
                    spoken).replace('\n', newline).encode()
            for route, text in self.texts(data).items():
                with self.subTest(newline=repr(newline), route=route):
                    self.assertEqual(text, spoken)
            with patch.object(server, 'LIB', self.root):
                self.assertEqual(server.vtt_cues('captions.vtt')[0]['t'], 3723)
            self.assertEqual(retrieval.vtt_windows(self.path)[0][0], 3723)

    def test_comma_timestamps_remain_readable(self):
        spoken = 'This caption uses the comma timestamps already accepted by Lastbook.'
        data = ('1\n00:01:02,000 --> 00:01:06,000\n' + spoken).encode()
        for route, text in self.texts(data).items():
            with self.subTest(route=route):
                self.assertEqual(text, spoken)
        with patch.object(server, 'LIB', self.root):
            self.assertEqual(server.vtt_cues('captions.vtt')[0]['t'], 62)

    def test_cue_markup_is_removed(self):
        spoken = 'This caption has spoken words inside tags and keeps the rest of the sentence.'
        data = (b'WEBVTT\n\n00:01.000 --> 00:05.000\n'
                b'<v Speaker>This caption has <b>spoken words</b> inside tags '
                b'and keeps the rest of the sentence.</v>\n')
        for route, text in self.texts(data).items():
            with self.subTest(route=route):
                self.assertEqual(text, spoken)

    def test_duplicate_cues_keep_existing_transcript_behavior(self):
        spoken = 'This complete caption appears twice in the original subtitle track.'
        data = ('WEBVTT\n\n00:01.000 --> 00:03.000\n' + spoken +
                '\n\n00:03.000 --> 00:05.000\n' + spoken + '\n').encode()
        for route, text in self.texts(data).items():
            with self.subTest(route=route):
                self.assertEqual(text, spoken)

    def test_empty_or_metadata_only_track_has_no_transcript(self):
        for data in (b'', b'WEBVTT\n\n', b'WEBVTT\n\nNOTE\nEditor notes only.\n'):
            for route, text in self.texts(data).items():
                with self.subTest(data=data, route=route):
                    self.assertEqual(text, '')

    def test_video_and_chat_entry_points_use_the_caption_payload(self):
        text = 'The storage container is marked 12 litres and this is its caption.'
        data = ('WEBVTT\n\ncaption-id\n00:20.000 --> 00:25.000\n'
                'The storage container is marked\n12\n'
                'litres and this is its caption.\n').encode()
        self.path.write_bytes(data)
        cat = {'by_id': {'video-test': {'path': 'videos/test.mp4', 'captions': ['captions.vtt']}},
               'video_tx': {}}
        with patch.object(server, 'LIB', self.root), patch.object(server, 'catalog', return_value=cat):
            self.assertEqual(server.transcript('video-test')['cues'], [{'t': 20, 'text': text}])
        with patch.object(retrieval, 'LIB', self.root):
            index = retrieval.Index.__new__(retrieval.Index)  # _texts needs neither an embedder nor an index database
            self.assertEqual(index._texts('video-test', ('vtt', 'captions.vtt')), [(None, 20, text)])

    def test_saved_course_transcript_keeps_numbers(self):
        page = b'<html><body><video><track src="captions.vtt"></video></body></html>'
        vtt = b'WEBVTT\n\n17\n00:01.000 --> 00:05.000\nThe label reads\n12\nlitres.\n'
        result = saved_pages.rewrite(page, lambda src: vtt if src == 'captions.vtt' else None)
        self.assertIn(b'<p>The label reads 12 litres.</p>', result)

    def test_trailing_whitespace_does_not_repeat_saved_course_caption(self):
        page = b'<html><body><video><track src="captions.vtt"></video></body></html>'
        expected = 'hello everyone today we compare water filters'
        for whitespace in (' ', '\t', ' \t ', '\u00a0'):
            with self.subTest(whitespace=repr(whitespace)):
                vtt = ('WEBVTT\n\n00:02.000 --> 00:04.000\nhello everyone\n' + whitespace +
                       '\n\n00:04.000 --> 00:06.000\nhello everyone\ntoday we compare water filters\n').encode()
                self.assertEqual(saved_pages.transcript_text(vtt), expected)
                result = saved_pages.rewrite(page, lambda src: vtt if src == 'captions.vtt' else None)
                self.assertIn(('<p>' + expected + '</p>').encode(), result)

    def test_empty_cue_does_not_consume_the_next_identifier(self):
        spoken = 'The next nonempty caption still belongs to its own timestamp.'
        data = ('WEBVTT\n\n00:00.000 --> 00:01.000\n\n'
                'next-cue\n00:20.000 --> 00:25.000\n' + spoken).encode()
        for route, text in self.texts(data).items():
            with self.subTest(route=route):
                self.assertEqual(text, spoken)
        with patch.object(server, 'LIB', self.root):
            self.assertEqual(server.vtt_cues('captions.vtt'), [{'t': 20, 'text': spoken}])


if __name__ == '__main__':
    unittest.main()
