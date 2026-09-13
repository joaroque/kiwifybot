import os
from urllib.parse import urlparse

import requests
import yt_dlp
from pathvalidate import sanitize_filename
from requests import Session

KIWIBOT_ERRORS = (
    requests.RequestException,
    yt_dlp.utils.DownloadError,
    OSError,
    RuntimeError,
    ValueError,
    KeyError,
)


class Kiwibot:
    LOGIN_URL = (
        "https://www.googleapis.com/identitytoolkit/v3/relyingparty/"
        "verifyPassword?key=AIzaSyDmOO1YAGt0X35zykOMTlolvsoBkefLKFU"
    )
    COURSES_URL = "https://api.kiwify.com.br/v1/viewer/courses"
    REQUEST_TIMEOUT = (15, 120)

    def __init__(self, output_dir="Cursos"):
        self.output_dir = output_dir
        self._s = self._new_session()
        self._is_logged = False

    @staticmethod
    def _new_session():
        session = Session()
        session.headers["user-agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
        return session

    @property
    def is_logged(self):
        return self._is_logged

    @staticmethod
    def sanitize(value, fallback="arquivo"):
        cleaned = sanitize_filename((value or fallback).strip()).strip()
        return cleaned or fallback

    # Backward-compatible alias for users of the original class.
    sanatize = sanitize

    def login(self, email, password):
        response = self._s.post(
            self.LOGIN_URL,
            data={
                "email": email,
                "password": password,
                "returnSecureToken": True,
            },
            timeout=self.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        token = response.json().get("idToken")
        if not token:
            raise RuntimeError("A autenticação não retornou um token")
        self._s.headers["authorization"] = f"Bearer {token}"
        self._is_logged = True
        return True

    def logout(self):
        self._s.close()
        self._s = self._new_session()
        self._is_logged = False

    def _get_json(self, url):
        response = self._s.get(url, timeout=self.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_courses(self):
        courses = []
        page = 1
        total = None
        while total is None or len(courses) < total:
            payload = self._get_json(f"{self.COURSES_URL}?page={page}")
            page_courses = payload.get("courses", [])
            total = payload.get("count", len(page_courses))
            if not page_courses:
                break
            courses.extend(page_courses)
            page += 1
        return courses

    def get_modules(self, course_id):
        return self._get_json(f"{self.COURSES_URL}/{course_id}")

    # Preserved for compatibility with callers of the original project.
    get_lessons = get_modules

    @staticmethod
    def _video_url(video):
        url = (
            video.get("stream_link_full_url")
            or video.get("download_link_full_url")
            or video.get("stream_link")
            or video.get("download_link")
            or video.get("url")
        )
        if url and url.startswith("/"):
            return "https://d3pjuhbfoxhm7c.cloudfront.net" + url
        return url

    @staticmethod
    def _is_kiwify_host(url):
        host = (urlparse(url).hostname or "").lower()
        return host == "kiwify.com.br" or host.endswith(".kiwify.com.br")

    def extract_info(
        self,
        course_id,
        module_id,
        lesson_id,
        file_type,
        file_id=None,
        course_payload=None,
    ):
        payload = course_payload or self.get_modules(course_id)
        course = payload.get("course", {})
        for module in course.get("modules", []):
            if module.get("id") != module_id:
                continue
            for lesson in module.get("lessons", []):
                if lesson.get("id") != lesson_id:
                    continue
                common = {
                    "course_name": self.sanitize(course.get("name"), "Curso"),
                    "module_name": self.sanitize(module.get("name"), "Modulo"),
                }
                if file_type == "video" and lesson.get("video"):
                    url = self._video_url(lesson["video"])
                    if not url:
                        return None
                    filename = self.sanitize(
                        lesson.get("title") or lesson["video"].get("name"), "video"
                    )
                    if not filename.lower().endswith(
                        (".mp4", ".mkv", ".mov", ".webm", ".avi")
                    ):
                        filename += ".mp4"
                    return {
                        **common,
                        "kind": "video",
                        "filename": filename,
                        "url": url,
                    }
                if file_type in ("file", "pdf"):
                    attachment = next(
                        (
                            item
                            for item in lesson.get("files") or []
                            if file_id is None or item.get("id") == file_id
                        ),
                        None,
                    )
                    if not attachment:
                        return None
                    extension = (attachment.get("extension") or "").lower()
                    if extension == "pdf":
                        url = (
                            f"{self.COURSES_URL}/{course_id}/files/"
                            f"{attachment['id']}?forceDownload=true"
                        )
                    else:
                        url = attachment.get("url")
                    if not url:
                        return None
                    return {
                        **common,
                        "kind": "file",
                        "filename": self.sanitize(
                            attachment.get("name"), f"anexo.{extension or 'bin'}"
                        ),
                        "url": url,
                    }
        return None

    def _destination(self, info):
        category = "Videos" if info["kind"] == "video" else "Anexos"
        directory = os.path.join(
            self.output_dir, info["course_name"], category, info["module_name"]
        )
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, info["filename"])

    def _download_file(self, url, destination):
        if os.path.isfile(destination) and os.path.getsize(destination) > 0:
            return "skipped"
        getter = self._s.get if self._is_kiwify_host(url) else requests.get
        response = getter(url, stream=True, timeout=self.REQUEST_TIMEOUT)
        response.raise_for_status()
        if "application/json" in response.headers.get("Content-Type", ""):
            payload = response.json()
            redirected_url = payload.get("url") or payload.get("download_url")
            response.close()
            if not redirected_url:
                raise RuntimeError("A API não retornou uma URL para o anexo")
            # Never forward Kiwify's bearer token to the storage provider.
            response = requests.get(
                redirected_url, stream=True, timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
        partial = destination + ".part"
        try:
            with open(partial, "wb") as output:
                for chunk in response.iter_content(chunk_size=256 * 1024):
                    if chunk:
                        output.write(chunk)
            os.replace(partial, destination)
        finally:
            response.close()
        return "downloaded"

    @staticmethod
    def _download_video(url, destination):
        if os.path.isfile(destination) and os.path.getsize(destination) > 0:
            return "skipped"
        options = {
            "outtmpl": destination,
            "windowsfilenames": True,
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "noplaylist": True,
            "quiet": True,
            "noprogress": True,
        }
        with yt_dlp.YoutubeDL(options) as downloader:
            downloader.download([url])
        return "downloaded"

    def download(self, info):
        destination = self._destination(info)
        if info["kind"] == "video":
            result = self._download_video(info["url"].strip(), destination)
        else:
            result = self._download_file(info["url"].strip(), destination)
        return result, destination

    def downloader(self, course_id, module_id, lesson_id, file_type, file_id=None):
        info = self.extract_info(
            course_id, module_id, lesson_id, file_type, file_id=file_id
        )
        return self.download(info) if info else None

    def download_all(self):
        totals = {"downloaded": 0, "skipped": 0, "failed": 0}
        for course in self.get_courses():
            data = self.get_modules(course["id"]).get("course", {})
            for module in data.get("modules", []):
                for lesson in module.get("lessons", []):
                    tasks = []
                    if lesson.get("video"):
                        tasks.append(("video", None))
                    tasks.extend(
                        ("file", item.get("id")) for item in lesson.get("files") or []
                    )
                    for file_type, file_id in tasks:
                        try:
                            info = self.extract_info(
                                course["id"],
                                module["id"],
                                lesson["id"],
                                file_type,
                                file_id,
                                course_payload={"course": data},
                            )
                            result = self.download(info) if info else None
                            if result:
                                status, destination = result
                                totals[status] += 1
                                print(f"[{status.upper()}] {destination}", flush=True)
                        except KIWIBOT_ERRORS as error:
                            totals["failed"] += 1
                            print(f"[FAILED] {error}", flush=True)
        return totals
