import re
import smtplib
import urllib
from email.mime.text import MIMEText

from pathlib import Path

import requests as requests


def str_to_bool(value: object) -> bool:
    if type(value) is bool:
        return value
    return value.lower() in ["true", "yes", "1", "y", "t"]


def dump_props(target, separator: str = "\n") -> str:
    lines = separator.join(["{}='{}'".format(key, value) for key, value in target.__dict__.items()])
    return lines


def safe_get(obj: object, prop: str, default: str = "") -> str:
    if obj is None:
        return default
    if type(obj) is not dict:
        d = obj.__dict__
    else:
        d = obj
    if prop in d:
        return d[prop]
    else:
        return default


def get_basename(path: str) -> str:
    p = Path(path)
    p.resolve()
    return p.name


def get_fullname(path: str) -> str:
    p = Path(path)
    p.resolve()
    return str(p.expanduser())


def get_property(obj, name):
    must_clean = False
    if name.startswith("clean_"):
        must_clean = True
        name = name.replace("clean_", "")

    if name in obj.__dict__:
        value = str(obj.__dict__[name])
        if must_clean:
            # value = value.replace(":", "(colon)")
            value = urllib.parse.quote(value)
        return True, value
    else:
        return False, None


def build_regex_dict(value: str, regex: str) -> dict:
    escaped_value = value.replace("\\:", "(colon)")
    new_dict = {}
    matches = re.findall(regex, escaped_value)
    for match in matches:
        new_dict[match[1]] = str(match[2]).replace("(colon)", ":")

    return new_dict


def send_email(sender: str, server: str, username: str, password: str, address: str, subject: str, body: str):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = address
    words = server.split(":")
    smtp_server = smtplib.SMTP_SSL(words[0], int(words[1]))
    smtp_server.login(username, password)
    smtp_server.sendmail(sender, address, msg.as_string())
    smtp_server.quit()


def call_http(url: str, method: str, payload: str):
    response = requests.request(method, url, data=payload)
    if response.status_code != 200:
        raise Exception("Error in http request: {}\n{}".format(response.status_code, response.text))
