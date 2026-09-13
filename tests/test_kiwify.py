import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from kiwify import Kiwibot


class KiwibotTests(unittest.TestCase):
    def test_login_sets_bearer_token_and_timeout(self):
        bot = Kiwibot()
        response = Mock()
        response.json.return_value = {"idToken": "test-token"}
        bot._s.post = Mock(return_value=response)
        bot.login("user@example.com", "secret")
        self.assertTrue(bot.is_logged)
        self.assertEqual(bot._s.headers["authorization"], "Bearer test-token")
        self.assertEqual(bot._s.post.call_args.kwargs["timeout"], bot.REQUEST_TIMEOUT)

    def test_extract_info_uses_viewer_endpoint_for_pdf(self):
        bot = Kiwibot()
        bot.get_modules = Mock(return_value=self._course_payload("pdf"))
        info = bot.extract_info("course", "module", "lesson", "file", "file")
        self.assertEqual(info["kind"], "file")
        self.assertEqual(
            info["url"],
            f"{bot.COURSES_URL}/course/files/file?forceDownload=true",
        )

    def test_extract_info_uses_lesson_url_for_non_pdf(self):
        bot = Kiwibot()
        bot.get_modules = Mock(return_value=self._course_payload("xlsx"))
        info = bot.extract_info("course", "module", "lesson", "file", "file")
        self.assertEqual(info["url"], "https://admin-api.kiwify.com.br/file")

    def test_external_redirect_does_not_receive_bearer_session(self):
        bot = Kiwibot()
        first = Mock()
        first.headers = {"Content-Type": "application/json"}
        first.json.return_value = {"url": "https://storage.example/file.pdf"}
        second = Mock()
        second.headers = {"Content-Type": "application/pdf"}
        second.iter_content.return_value = [b"pdf"]
        bot._s.get = Mock(return_value=first)
        with tempfile.TemporaryDirectory() as directory:
            destination = os.path.join(directory, "file.pdf")
            with patch("kiwify.requests.get", return_value=second) as clean_get:
                bot._download_file("https://api.kiwify.com.br/file", destination)
            clean_get.assert_called_once()
            with open(destination, "rb") as downloaded:
                self.assertEqual(downloaded.read(), b"pdf")

    @staticmethod
    def _course_payload(extension):
        return {
            "course": {
                "name": "Course",
                "modules": [
                    {
                        "id": "module",
                        "name": "Module",
                        "lessons": [
                            {
                                "id": "lesson",
                                "title": "Lesson",
                                "files": [
                                    {
                                        "id": "file",
                                        "name": f"file.{extension}",
                                        "extension": extension,
                                        "url": "https://admin-api.kiwify.com.br/file",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        }


if __name__ == "__main__":
    unittest.main()
