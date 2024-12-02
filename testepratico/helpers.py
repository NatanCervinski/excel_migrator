import re
from itertools import cycle
from typing import Dict

import pandas as pd
from dynaconf import settings


def clean_string(input_string: str) -> str:
    return re.sub(r"\D", "", str(input_string))


def is_valid_cpf(cpf: str) -> bool:
    if not re.match(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        return False

    numbers = [int(digit) for digit in cpf if digit.isdigit()]

    if len(numbers) != 11 or len(set(numbers)) == 1:
        return False

    sum_of_products = sum(a * b for a, b in zip(numbers[0:9], range(10, 1, -1)))
    expected_digit = (sum_of_products * 10 % 11) % 10
    if numbers[9] != expected_digit:
        return False

    sum_of_products = sum(a * b for a, b in zip(numbers[0:10], range(11, 1, -1)))
    expected_digit = (sum_of_products * 10 % 11) % 10
    if numbers[10] != expected_digit:
        return False

    return True


def is_valid_cnpj(cnpj: str) -> bool:
    if len(cnpj) != 14:
        return False

    if cnpj in (c * 14 for c in "1234567890"):
        return False

    cnpj_r = cnpj[::-1]
    for i in range(2, 0, -1):
        cnpj_enum = zip(cycle(range(2, 10)), cnpj_r[i:])
        dv = sum(map(lambda x: int(x[1]) * x[0], cnpj_enum)) * 10 % 11
        if cnpj_r[i - 1 : i] != str(dv % 10):
            return False

    return True


def is_valid_cpf_or_cnpj(cpf_cnpj: str) -> bool:
    return is_valid_cpf(cpf_cnpj) or is_valid_cnpj(cpf_cnpj)


def format_cpf_or_cnpj(cpf_cnpj: str) -> str:
    cpf_cnpj = re.sub(r"\D", "", str(cpf_cnpj))

    if len(cpf_cnpj) < 11:
        cpf = cpf_cnpj.zfill(11)
        valid_cpf = is_valid_cpf(cpf)
        if valid_cpf:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    if len(cpf_cnpj) <= 14:
        cnpj = cpf_cnpj.zfill(14)
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

    return cpf_cnpj


def validate_cpf_cnpj(df: pd.DataFrame) -> pd.DataFrame:
    cpf_cnpj_column = settings.CPF_CNPJ_COLUMN

    for index, row in df.iterrows():
        cpf_cnpj = str(row[cpf_cnpj_column])
        cpf_cnpj_cleaned = re.sub(r"\D", "", cpf_cnpj)

        if len(cpf_cnpj_cleaned) == 11 and not is_valid_cpf(cpf_cnpj_cleaned):
            df.at[index, cpf_cnpj_column] = None
        elif len(cpf_cnpj_cleaned) == 14 and not is_valid_cnpj(cpf_cnpj_cleaned):
            df.at[index, cpf_cnpj_column] = None
        else:
            df.at[index, cpf_cnpj_column] = format_cpf_or_cnpj(cpf_cnpj)

    return df


def move_value_to_column(
    df: pd.DataFrame, source_column: str, destination_column: str
) -> pd.DataFrame:
    if destination_column not in df.columns:
        df[destination_column] = ""

    for index, row in df.iterrows():
        value = str(row[source_column])
        if pd.notna(value):
            df.at[index, destination_column] += f"{value}. "
            df.at[index, source_column] = None

    return df


def handle_cpf_cnpj(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    cpf_cnpj_column = config["CPF_CNPJ_COLUMN"]
    annotations_column = config["IF_INVALID_MOVE_TO"].get(cpf_cnpj_column, "")

    if annotations_column and annotations_column not in df.columns:
        df[annotations_column] = ""

    for index, row in df.iterrows():
        cpf_cnpj = str(row[cpf_cnpj_column])
        cpf_cnpj_cleaned = re.sub(r"\D", "", cpf_cnpj)

        if len(cpf_cnpj_cleaned) == 11 and not is_valid_cpf(cpf_cnpj_cleaned):
            if annotations_column:
                df.at[index, annotations_column] += cpf_cnpj
            df.at[index, cpf_cnpj_column] = None
            return df

        if len(cpf_cnpj_cleaned) == 14 and not is_valid_cnpj(cpf_cnpj_cleaned):
            if annotations_column:
                df.at[index, annotations_column] += cpf_cnpj
            df.at[index, cpf_cnpj_column] = None
            return df

        df.at[index, cpf_cnpj_column] = format_cpf_or_cnpj(cpf_cnpj)

    return df


def remove_duplicates(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    return df.drop_duplicates(subset=[column_name])


def clean_special_characters(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    df[column_name] = df[column_name].apply(
        lambda x: re.sub(r"[^a-zA-Z\s]", "", str(x)).strip()
    )
    return df
