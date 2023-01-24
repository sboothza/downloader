import argparse
import os
import shutil
import time

import yt_dlp

from classes import Target
from config import Config
from repo import Downloadable, Repository
from utils import get_fullname, get_basename, safe_get


def create_yt_dlp(config: Config, audio_only: bool) -> yt_dlp.YoutubeDL:
    ydl_opts = {'outtmpl': get_fullname(os.path.join(config.temp_path, config.output_format)),
                'restrictfilenames': True, 'nooverwrites': True, 'noplaylist': True, 'quiet': False,
                'skip_unavailable_fragments': True, 'noprogress': False, 'ignore_config': True,
                'ffmpeg_location': config.tools_path, 'verbose': False, 'no_warnings': False, 'ignoreerrors': False}

    if audio_only:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'best[ext=mp4]'

    ydl = yt_dlp.YoutubeDL(ydl_opts)
    return ydl


def task_download(config: Config, ydl: yt_dlp.YoutubeDL, item: Downloadable) -> Downloadable:
    try:
        print("Getting info for {}".format(item.url))
        info = ydl.extract_info(item.url, False)
        filename: str = ydl.prepare_filename(info, outtmpl=os.path.join(config.temp_path,
                                                                        config.output_format))
        basename: str = get_basename(filename)
        folder = config.download_path
        if not os.path.exists(folder):
            os.makedirs(folder)

        final_filename = os.path.join(folder, basename)

        item.title = safe_get(info, "title")
        item.width = safe_get(info, "width")
        item.height = safe_get(info, "height")
        item.length = safe_get(info, "duration")
        item.file_size = safe_get(info, "filesize_approx")

        if not os.path.exists(final_filename):
            print("downloading {}".format(item.id))
            ydl.download([item.url])

            temp_filename = os.path.join(config.temp_path, basename)

            print("finished downloading {}".format(item.id))
            item.filename = final_filename
            shutil.copyfile(temp_filename, final_filename)
            os.remove(temp_filename)

        st = os.stat(final_filename)
        item.file_size = st.st_size
        item.filename = final_filename
        item.status = "downloaded"
        item.errors = None
        return item
    except Exception as ex:
        print("Error: {}".format(str(ex)))
        item.retry_count = item.retry_count + 1
        if item.errors is None:
            item.errors = ''
        item.errors = item.errors + '\nERROR:{err}'.format(err=str(ex)[:100])
        if item.retry_count > 5:
            item.status = "failed"
        else:
            item.status = "queued"

        return item


def run(config: Config, repo: Repository) -> None:
    item: Downloadable = repo.get_next_queue_item()
    while item:
        try:
            print("Picked up item {}".format(item.id))

            if item.status == "queued":
                print("new item")

                ydl: yt_dlp.YoutubeDL = create_yt_dlp(config, item.audio_only)
                item.status = "in_progress"
                repo.update_item(item)

                # download item
                print("Downloading {}".format(item.id))
                item = task_download(config, ydl, item)
                item.status = "downloaded"
                repo.update_item(item)
                print("Downloaded successfully")
                print(item)

            if item.status == "downloaded":
                # execute callback
                callback = item.build_callback_info(config)
                target = Target.construct(callback)
                print("Executing callback")
                print(target)
                target.invoke(config)
                item.status = "completed"
                repo.update_item(item)

            # get next
            item = repo.get_next_queue_item()
        except Exception as e:
            print(e)
            item.in_progress = 0
            repo.update_item(item)


# def test(config: Config, repo: Repository):
#     # callback_str = "mail://stephen.booth.za@gmail.com?subject={mail_subject}&body={mail_body}"
#     # m = re.match("(\w+):\/\/(.*)", callback_str)
#     # method = m.group(1)
#     # callback = m.group(2)
#     #
#     # matches = re.findall("{([^}]+)}", callback)
#     # for match in matches:
#     #     print(match)
#     item: Downloadable = Downloadable(title="this is a test",
#                                       callback="<type:mail><address:stephen.booth.za@gmail.com><subject:<%mail_subject%>><body:<%mail_body%>>",
#                                       file_size=1024)
#     item.id = 12
#     callback = build_callback_info(item, config)
#     target = Target.construct(callback)
#     target.invoke(config)
#


def delete_expired(repo: Repository):
    items_to_delete = repo.get_expired_items()
    for item in items_to_delete:
        repo.flag_deleted(item.id)


def main():
    parser = argparse.ArgumentParser(description="Download videos and audio from streaming sources")
    parser.add_argument('--output',
                        help='Output format',
                        dest='output',
                        default='%(extractor)s_%(title)s.%(ext)s',
                        required=True)
    parser.add_argument('--database',
                        help='Database filename',
                        dest='db',
                        required=True)
    parser.add_argument('--download-path',
                        help='Download path',
                        dest='path',
                        required=True)
    parser.add_argument('--temp-path',
                        help='Temp download path',
                        dest='temp_path',
                        required=True)
    parser.add_argument('--tools-path',
                        help='Tools bin path (ffmpeg)',
                        dest='tools_path',
                        required=True)

    args = parser.parse_args()
    config = Config(args.db, args.path, args.temp_path, args.output, args.tools_path)
    print("Config set up")
    print(config)
    repo = Repository(config)
    repo.create_db_if_not_exist()
    print("Repository set up")
    print("Starting loop")

    repo.reset_in_progress()

    while True:
        run(config, repo)
        while repo.count_waiting() == 0:
            delete_expired(repo)
            print(".", end="")
            time.sleep(5)


if __name__ == '__main__':
    main()
