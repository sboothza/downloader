from os import path

from utils import dump_props


class Config:
    def __init__(self, db_file: str = "", download_path: str = "", temp_path: str = "", output_format: str = "",
                 tools_path: str = ""):
        self.db_file: str = "sqlite:///{}".format(path.expanduser(db_file))
        self.download_path: str = path.expanduser(download_path)
        self.temp_path: str = path.expanduser(temp_path)
        self.output_format: str = output_format
        self.tools_path: str = path.expanduser(tools_path)

        self.download_url = "http%3A//127.0.0.1%3A5000/file/<%id%>"
        self.mail_subject = "Download completed for '<%title%>'"
        self.mail_body = "Download completed for '<%title%>'\nDownload link: '" + self.download_url + "'"
        self.mail_sender = "stephen.booth.za@gmail.com"
        self.mail_server = "smtp.gmail.com:465"
        self.username = "stephen.booth.za@gmail.com"
        self.password = "bxvqzyavsdfscqhv"
        self.expiry_days = 2

    def __str__(self):
        return "Config:\n\t" + dump_props(self, "\n\t")
