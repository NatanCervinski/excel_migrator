import os
import shutil
import subprocess
import zipfile
from typing import Dict

import pandas as pd


def save_dataframes_as_csv(
    dataframes: Dict[str, pd.DataFrame], output_directory: str
) -> None:
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for file_name, df in dataframes.items():
        output_file_path = os.path.join(output_directory, f"{file_name}.csv")
        df.to_csv(output_file_path, index=False, encoding="utf-8")


def create_zip_from_directory(directory_path: str, zip_file_path: str) -> None:
    with zipfile.ZipFile(zip_file_path, "w") as zipf:
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, directory_path))


def create_rar_from_directory(directory_path: str, rar_file_path: str) -> None:
    rar_command = shutil.which("rar")
    if not rar_command:
        raise EnvironmentError(
            "O comando 'rar' não foi encontrado. Instale o WinRAR ou RAR no sistema."
        )

    subprocess.run(
        [rar_command, "a", rar_file_path, os.path.join(directory_path, "*")], check=True
    )


def copy_files_without_compression(
    source_directory: str, destination_directory: str
) -> None:
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    for root, _, files in os.walk(source_directory):
        for file in files:
            source_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(source_file_path, source_directory)
            destination_file_path = os.path.join(destination_directory, relative_path)

            destination_file_dir = os.path.dirname(destination_file_path)
            if not os.path.exists(destination_file_dir):
                os.makedirs(destination_file_dir)

            shutil.copy2(source_file_path, destination_file_path)
