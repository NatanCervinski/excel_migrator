import logging
import os
import re
import tempfile
import zipfile
from typing import Dict, List

import pandas as pd
import rarfile

from testepratico.config import settings

ENCODINGS_TO_TRY = settings.MIGRATION_CONFIGS.ENCODINGS_TO_TRY


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
    required_tables: List[str],
    delimiter: str = ";",
) -> Dict[str, pd.DataFrame]:
    if not (zipfile.is_zipfile(input_path) or rarfile.is_rarfile(input_path)):
        raise ValueError("O arquivo fornecido não é um arquivo .zip ou .rar válido.")

    with tempfile.TemporaryDirectory() as temp_dir:
        if zipfile.is_zipfile(input_path):
            with zipfile.ZipFile(input_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
                compressed_files = zip_ref.namelist()
        elif rarfile.is_rarfile(input_path):
            with rarfile.RarFile(input_path, "r") as rar_ref:
                rar_ref.extractall(temp_dir)
                compressed_files = rar_ref.namelist()

        compressed_files_normalized = [os.path.basename(f) for f in compressed_files]

        table_to_file = {}
        for table_name in required_tables:
            pattern = re.compile(
                rf"{settings.MIGRATION_CONFIGS.CSV_PREFIX}{table_name}_CodEmpresa_\d+\.csv",
                re.IGNORECASE,
            )
            matching_files = list(filter(pattern.match, compressed_files_normalized))
            if matching_files:
                table_to_file[table_name] = os.path.join(temp_dir, matching_files[0])
            else:
                raise FileNotFoundError(
                    f"O arquivo para a tabela '{table_name}' está faltando no arquivo comprimido."
                )

        dataframes = {}
        for table_name, file_path in table_to_file.items():
            try:
                for enc in ENCODINGS_TO_TRY:
                    try:
                        df = pd.read_csv(
                            file_path, delimiter=delimiter, encoding=enc, header=0
                        )
                        dataframes[table_name] = df
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        logging.error(
                            f"Erro ao carregar {file_path} com codificação {enc}: {e}"
                        )
                        break
            except Exception as e:
                raise Exception(
                    f"Erro ao carregar o arquivo para a tabela '{table_name}': {e}"
                )

        return dataframes
