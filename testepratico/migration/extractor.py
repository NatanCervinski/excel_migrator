import logging
import os
import tempfile
import zipfile
from typing import Dict, List

import pandas as pd
import rarfile
from config import settings

ENCODINGS_TO_TRY = settings.MIGRATION_CONFIGS.ENCODINGS_TO_TRY


def load_csv_from_directory(
    directory_path: str,
    delimiter: str = ";",
) -> Dict[str, pd.DataFrame]:
    lst_csv_files = list_csv_in_directory(directory_path)
    return load_dataframes_from_csv(directory_path, lst_csv_files, delimiter)


def load_single_csv(
    file_path: str,
    delimiter: str = ";",
) -> pd.DataFrame:
    if not file_path.endswith(".csv"):
        raise ValueError("O arquivo fornecido não é um arquivo CSV.")

    with open(file_path, "r") as file:
        for enc in ENCODINGS_TO_TRY:
            try:
                df = pd.read_csv(file, delimiter=delimiter, encoding=enc)
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logging.error(
                    f"Erro ao carregar {file_path} com codificação {enc}: {e}"
                )
                break
    return pd.DataFrame()


def load_csv_from_compressed_file(
    input_path: str,
    delimiter: str = ";",
) -> Dict[str, pd.DataFrame]:
    if not (zipfile.is_zipfile(input_path) or rarfile.is_rarfile(input_path)):
        return {}

    with tempfile.TemporaryDirectory() as temp_dir:
        if zipfile.is_zipfile(input_path):
            with zipfile.ZipFile(input_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        elif rarfile.is_rarfile(input_path):
            with rarfile.RarFile(input_path, "r") as rar_ref:
                rar_ref.extractall(temp_dir)

        lst_csv_files = list_csv_in_directory(temp_dir)
        return load_dataframes_from_csv(temp_dir, lst_csv_files, delimiter)


def list_csv_in_directory(directory: str) -> List[str]:
    return [
        f
        for f in os.listdir(directory)
        if f.startswith(settings.MIGRATION_CONFIGS.CSV_PREFIX) and f.endswith(".csv")
    ]


def load_dataframes_from_csv(
    directory: str, csv_files: List[str], delimiter: str
) -> Dict[str, pd.DataFrame]:
    dic_dataframes = {}
    encodings_to_try = ENCODINGS_TO_TRY

    for csv_file in csv_files:
        file_path = os.path.join(directory, csv_file)
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(file_path, delimiter=delimiter, encoding=enc, header=0)
                dic_dataframes[csv_file] = df
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logging.error(f"Erro ao carregar {csv_file} com codificação {enc}: {e}")
                break
    if len(dic_dataframes) == 0:
        logging.warning(f"Não foi possível carregar nenhum arquivo CSV em {directory}")
    return dic_dataframes
