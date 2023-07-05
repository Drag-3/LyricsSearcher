import json
import logging

from lyrics_searcher import CONFIG_DIR

logging.getLogger(__name__)


def save_auth(service, token):
    try:
        file = CONFIG_DIR / "auth.json"
        with open(file, 'r', encoding="utf-8") as f:
            auths = json.load(f)

        auths[service] = token

        with open(file, 'w', encoding="utf-8") as f:
            json.dump(auths, f)

    except Exception as e:
        logging.exception(e)
        return None


def create_auth():
    file = CONFIG_DIR / "auth.json"
    file.touch()
    data = {"spotify": "", "genius": ""}
    with open(file, 'w', encoding="utf-8") as f:
        json.dump(data, f)


def get_auth(service):
    try:
        file = CONFIG_DIR / "auth.json"
        with open(file, 'r', encoding="utf-8") as f:
            auths = json.load(f)
        return auths.get(service)
    except Exception as e:
        logging.exception(e)
        return None
