import argparse
import re

from config import Config
from repo import Repository, Downloadable


def import_list(repo: Repository, filename: str) -> None:
    lines: list[str]
    with open(filename, "r", encoding='utf-8') as f:
        lines = f.readlines()
        f.close()

    total: int = 0
    ok: int = 0
    bad: int = 0
    for line in lines:
        words = [w for w in line.split("  ", ) if w.strip() != ""]
        url = words[0].strip()
        clip_type = words[1].strip().lower()
        audio_only = clip_type == "audio"
        callback = words[2].strip()

        item = Downloadable(url=url, audio_only=audio_only, callback=callback, status="queued")

        if repo.add(item):
            print('added url {url}'.format(url=url))
            ok = ok + 1
            total = total + 1
        else:
            print('already added {url} -- skipping'.format(url=url))
            bad = bad + 1
            total = total + 1

    print('FINISHED IMPORTING')
    print('Successfully imported {ok} of {total} - {bad} already imported'.format(ok=ok, total=total, bad=bad))


def main():
    DESCRIPTION = "Download videos and audio from streaming sources - import file list\n" \
                  "Format as follows: \n" \
                  "<type:http><method:post><url:mynameisearl.co.za/done_post><payload:{url=\"<%url%>\"," \
                  "download=\"<%download_url%>\",title=\"<%title%>\"}>\n" \
                  "<type:mail><address:stephen.booth.za@gmail.com><subject:<%mail_subject%>><body:<%mail_body%>>"

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--database',
                        help='Database filename',
                        dest='db',
                        required=True)
    parser.add_argument('--import-file',
                        help='list of urls',
                        dest='import_file',
                        default='not_set',
                        required=True)

    args = parser.parse_args()
    config = Config(args.db)
    repo = Repository(config)
    repo.create_db_if_not_exist()
    import_list(repo, args.import_file)


if __name__ == '__main__':
    main()
