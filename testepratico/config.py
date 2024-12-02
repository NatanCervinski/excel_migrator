import os

from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["settings.json", ".secrets.toml"],
    environments=True,
    defaults={
        "UPLOAD_FOLDER": os.path.join(os.getcwd(), "uploads"),
        "PROCESSED_FOLDER": os.path.join(os.getcwd(), "processed_files"),
    },
)
