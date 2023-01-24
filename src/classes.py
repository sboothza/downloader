import urllib

from config import Config
from utils import send_email, call_http, dump_props, str_to_bool, safe_get


class FileRequest:
    def __init__(self, url: str = "", callback: str = "", audio_only: bool = False):
        self.url = url
        self.callback = callback
        self.audio_only = audio_only

    @classmethod
    def from_dict(cls, data: dict):
        value = FileRequest(urllib.parse.unquote(safe_get(data, "url")),
                            urllib.parse.unquote(safe_get(data, "callback")),
                            str_to_bool(safe_get(data, "audio_only", "False")))
        return value


class FileCompletedCallback:
    def __init__(self, original_url: str = "", download_link: str = "", title: str = ""):
        self.original_url = original_url
        self.download_link = download_link
        self.title = title

    @classmethod
    def from_dict(cls, data: dict):
        value = FileCompletedCallback(safe_get(data, "original_url"), safe_get(data, "download_link"),
                                      safe_get(data, "title"))
        return value

    def __str__(self):
        return "FileCompletedCallback:\n\t" + dump_props(self, "\n\t")


class Target:
    pass


class MailTarget(Target):
    def __init__(self, address: str = "", subject: str = "", body: str = ""):
        self.address = address
        self.subject = subject
        self.body = body

    def invoke(self, config: Config):
        send_email(config.mail_sender, config.mail_server, config.username, config.password, self.address, self.subject,
                   self.body)

    @classmethod
    def build_from_dict(cls, values: dict):
        item = MailTarget(safe_get(values, "address"), safe_get(values, "subject"), safe_get(values, "body"))
        return item

    def __str__(self):
        return "MailTarget:\n\t" + dump_props(self, "\n\t")


class HttpTarget(Target):
    def __init__(self, url: str = "", method: str = "", payload: str = ""):
        self.url = url
        self.method = method
        self.payload = payload

    def invoke(self, config: Config):
        call_http(self.url, self.method, self.payload)

    @classmethod
    def build_from_dict(cls, values: dict):
        item = HttpTarget(safe_get(values, "url"), safe_get(values, "method"), safe_get(values, "payload"))
        return item

    def __str__(self):
        return "HttpTarget:\n\t" + dump_props(self, "\n\t")


class Target:
    def __init__(self):
        pass

    def invoke(self, config: Config):
        pass

    @staticmethod
    def construct(values: dict) -> Target:
        if values["type"] == "http":
            return HttpTarget.build_from_dict(values)
        elif values["type"] == "mail":
            return MailTarget.build_from_dict(values)
        else:
            raise Exception("target not found")
