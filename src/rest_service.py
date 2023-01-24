import argparse
import os
from datetime import datetime, timedelta

from flask import Flask, request, send_file, url_for, make_response

from classes import FileRequest, FileCompletedCallback
from config import Config
from repo import Repository, Downloadable
from utils import str_to_bool

app = Flask(__name__)
config = None
repo = None


@app.route("/")
def default():
    return "<p>Downloader</p>"


@app.get("/callback")
def callback_get():
    original_url = request.args.get("original_url", "")
    download_link = request.args.get("download_link", "")
    title = request.args.get("title", "")
    item = FileCompletedCallback(original_url, download_link, title)
    print("download completed")
    print(item)
    resp = "Callback ok: {} {} {}".format(original_url, download_link, title)
    return make_response(resp, 200)


@app.post("/callback")
def callback_post():
    content = request.json
    item = FileCompletedCallback.from_dict(content)
    print("download completed")
    print(item)
    resp = "Callback ok: {} {} {}".format(item.original_url, item.download_link, item.title)
    return make_response(resp, 200)


@app.post("/file")
def file_post():
    content = request.json
    file_request = FileRequest.from_dict(content)
    create = datetime.now()
    expire = create + timedelta(days=config.expiry_days)
    item = Downloadable(url=file_request.url, callback=file_request.callback,
                        audio_only=str_to_bool(file_request.audio_only),
                        create_date=create, expiry_date=expire, status="queued")
    resp = "Link queued ok: {} {} expires on {}".format(item.url, item.title, item.expiry_date)
    repo.add(item)
    return make_response(resp, 200)


@app.get("/file/<int:fileid>")
def file_get(fileid):
    # fileid = request.args.get("id", "")
    item = repo.get_by_id(int(fileid))
    if os.path.isfile(item.filename):
        return send_file(item.filename)


@app.get("/video")
def video_get():
    url = request.args.get("url", "")
    callback = request.args.get("callback", "")
    file_request = FileRequest(url, callback, False)
    create = datetime.now()
    expire = create + timedelta(days=config.expiry_days)
    item = Downloadable(url=file_request.url, callback=file_request.callback, audio_only=file_request.audio_only,
                        create_date=create, expiry_date=expire, status="queued")
    repo.add(item)
    resp = "Link queued ok: {} {} expires on {}".format(item.url, item.title, item.expiry_date)
    return make_response(resp, 200)


@app.get("/audio")
def audio_get():
    url = request.args.get("url", "")
    callback = request.args.get("callback", "")
    file_request = FileRequest(url, callback, True)
    create = datetime.now()
    expire = create + timedelta(days=config.expiry_days)
    item = Downloadable(url=file_request.url, callback=file_request.callback, audio_only=file_request.audio_only,
                        create_date=create, expiry_date=expire, status="queued")
    repo.add(item)
    resp = "Link queued ok: {} {} expires on {}".format(item.url, item.title, item.expiry_date)
    return make_response(resp, 200)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download videos and audio from streaming sources")
    parser.add_argument('--database',
                        help='Database filename',
                        dest='db',
                        required=True)
    parser.add_argument('--download-path',
                        help='Download path',
                        dest='path',
                        required=True)
    parser.add_argument('--port',
                        help='Port',
                        dest='port',
                        type=int,
                        required=True)

    args = parser.parse_args()
    config = Config(args.db, args.path, "", "", "")
    print("Config set up")
    print(config)
    repo = Repository(config)
    repo.create_db_if_not_exist()
    print("Repository set up")
    # with app.test_request_context():
    #     print(url_for("file_get", id="1"))

    app.run(host='0.0.0.0', port=args.port)
