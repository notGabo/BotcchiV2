import asyncio
import unittest

import yt_dlp

from src.services.yt_handler import YTDLSource


class FakeYTDL:
    def __init__(self):
        self.calls = []

    def extract_info(self, query, download=False):
        self.calls.append(query)
        if len(self.calls) == 1 and "topic" not in query:
            raise yt_dlp.utils.DownloadError(
                "Sign in to confirm your age. This video may be inappropriate for some users."
            )
        return {
            "title": "Test title",
            "webpage_url": "https://example.com/watch?v=123",
            "thumbnail": "https://example.com/thumb.jpg",
            "duration": 123,
            "uploader": "Test uploader",
            "url": "https://example.com/audio.mp3",
        }


class YTDLSourceTests(unittest.TestCase):
    def test_extract_info_retries_with_topic_on_age_restriction(self):
        original = YTDLSource.ytdl
        YTDLSource.ytdl = FakeYTDL()
        try:
            result = asyncio.run(YTDLSource.extract_info("Song Name"))
            self.assertEqual(YTDLSource.ytdl.calls, ["Song Name", "Song Name topic"])
            self.assertEqual(result["title"], "Test title")
            self.assertEqual(result["duration_str"], "2:03")
        finally:
            YTDLSource.ytdl = original

    def test_extract_info_raises_for_other_errors(self):
        original = YTDLSource.ytdl
        YTDLSource.ytdl = FakeYTDL()

        def failing_extract_info(query, download=False):
            raise yt_dlp.utils.DownloadError("No internet connection")

        YTDLSource.ytdl.extract_info = failing_extract_info
        try:
            with self.assertRaises(RuntimeError):
                asyncio.run(YTDLSource.extract_info("Song Name"))
        finally:
            YTDLSource.ytdl = original


if __name__ == "__main__":
    unittest.main()
