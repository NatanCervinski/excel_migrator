import re

import pandas as pd


def verify_column_exists_in_dataframe(df: pd.DataFrame, column: str) -> bool:
    return column in df.columns


def clean_string(input_string: str) -> str:
    return re.sub(r"\D", "", str(input_string))


def format_cpf(cpf: str) -> str:
    cpf = clean_string(cpf)
    if not len(cpf) == 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
