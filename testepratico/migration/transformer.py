import re
from datetime import datetime
from typing import Any, Dict, Pattern

import pandas as pd

from testepratico.helpers import (
    clean_string,
    format_cpf_or_cnpj,
    is_valid_cpf_or_cnpj,
)


def handle_missing_values(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    client_field_mappings = config["FIELD_MAPPINGS"]
    columns_with_default_value = config["COLUMNS_WITH_DEFAULT_VALUE"]
    default_value_for_missing = config["DEFAULT_VALUE_FOR_MISSING"]

    mapped_columns = [
        client_field_mappings.get(col, col) for col in columns_with_default_value
    ]

    for column in mapped_columns:
        print(df.columns)
        if column in df.columns:
            df[column] = df[column].fillna(default_value_for_missing)

            print(df[column])
    return df


def standardize_dates(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    for column in config["DATE_COLUMNS"]:
        if not column in df.columns:
            continue
        df[column] = pd.to_datetime(df[column], errors="coerce").dt.strftime("%d/%m/%Y")
    return df


def standardize_cpf_cnpj(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    cpf_cnpj_column = config["CPF_CNPJ_COLUMN"]
    destination_column = config["IF_INVALID_MOVE_TO"][cpf_cnpj_column]

    if not cpf_cnpj_column in df.columns:
        return df

    if destination_column not in df.columns:
        df[destination_column] = ""

    df[cpf_cnpj_column] = df[cpf_cnpj_column].apply(clean_string)
    df[cpf_cnpj_column] = df[cpf_cnpj_column].apply(
        lambda x: x.zfill(11) if len(x) < 11 else x.zfill(14)
    )

    mask_invalid = df[cpf_cnpj_column].apply(is_valid_cpf_or_cnpj) == False

    df.loc[mask_invalid, destination_column] += df.loc[
        mask_invalid, cpf_cnpj_column
    ].apply(lambda x: f", Valor inválido (CPF/CNPJ): {x}")
    df.loc[mask_invalid, cpf_cnpj_column] = None

    df[cpf_cnpj_column] = df[cpf_cnpj_column].apply(
        lambda x: format_cpf_or_cnpj(x) if pd.notna(x) else x
    )

    return df


def standardize_phone(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    phone_columns = config.get("PHONE_COLUMNS", [])

    for phone_column in phone_columns:
        if not phone_column in df.columns:
            continue

        def format_phone(phone: str) -> str:
            phone_cleaned = clean_string(phone)

            if len(phone_cleaned) < 10:
                phone_cleaned = phone_cleaned.zfill(10)
            elif len(phone_cleaned) > 11:
                phone_cleaned = phone_cleaned[:11]

            if len(phone_cleaned) == 11:
                return f"({phone_cleaned[:2]}) {phone_cleaned[2:7]}-{phone_cleaned[7:]}"
            elif len(phone_cleaned) == 10:
                return f"({phone_cleaned[:2]}) {phone_cleaned[2:6]}-{phone_cleaned[6:]}"

            return phone_cleaned

        df[phone_column] = df[phone_column].apply(format_phone)

    return df


def standardize_emails(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    email_columns = config.get("EMAIL_COLUMNS", [])
    destination_column = config.get("IF_EMAIL_MULTIPLE_MOVE_TO", "")

    if not email_columns:
        return df

    if destination_column not in df.columns:
        df[destination_column] = ""

    for index, row in df.iterrows():
        email_data = str(row[email_columns[0]])
        if pd.notna(email_data):
            emails = email_data.split(",")

            first_email = emails[0].strip()
            df.at[index, email_columns[0]] = first_email

            if len(emails) > 1:
                additional_emails = ", ".join(email.strip() for email in emails[1:])
                current_notes = str(row.get(destination_column, "")).strip()
                updated_notes = f"{current_notes}, {additional_emails}".strip(
                    ", "
                ).replace(",,", ",")
                df.at[index, destination_column] = updated_notes

    for col in email_columns[1:]:
        df[col] = ""

    return df


def standardize_cep(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    zip_code_columns = config.get("CEP_COLUMNS", [])

    for zip_column in zip_code_columns:
        if zip_column in df.columns:
            df[zip_column] = df[zip_column].apply(
                lambda x: str(x).zfill(8) if len(str(x)) < 8 else str(x)
            )

    return df


def map_fields(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    field_mappings = config["FIELD_MAPPINGS"]

    email_columns = [
        key
        for key, value in field_mappings.items()
        if value in config.get("EMAIL_COLUMNS", [])
    ]

    if email_columns:
        combined_emails = df[email_columns].apply(
            lambda row: ",".join(filter(pd.notna, row)), axis=1
        )
        df[field_mappings[email_columns[0]]] = combined_emails

    df = df.drop(columns=email_columns)

    remaining_mappings = {
        key: value for key, value in field_mappings.items() if key not in email_columns
    }
    df = df.rename(columns=remaining_mappings)

    columns_to_keep = list(field_mappings.values())
    existing_columns = [col for col in columns_to_keep if col in df.columns]
    df = df.loc[:, existing_columns][field_mappings.values()]
    return df.loc[:, ~df.columns.duplicated()].copy()


def filter_required_columns(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    client_field_mappings = config["FIELD_MAPPINGS"]
    client_required_columns = config["REQUIRED_COLUMNS"]

    required_columns = [
        col
        for col in client_field_mappings.keys()
        if client_field_mappings[col] in client_required_columns
    ]

    filtered_df = df.dropna(subset=required_columns)

    columns_to_keep = list(client_field_mappings.keys())
    filtered_df = filtered_df.loc[:, filtered_df.columns.intersection(columns_to_keep)]

    return filtered_df


def remove_unnecessary_columns(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    columns_to_keep = list(config["FIELD_MAPPINGS"].keys())

    filtered_df = df.loc[:, df.columns.intersection(columns_to_keep)]

    return filtered_df


def merge_process_with_client(
    process_df: pd.DataFrame, client_df: pd.DataFrame, config: dict
) -> pd.DataFrame:
    process_client_code_col = config["PROCESS_CLIENT_CODE_COLUMN"]
    client_name_col = config["CLIENT_NAME_COLUMN"]
    client_code_col = config["CLIENT_CODE_COLUMN"]

    if process_client_code_col not in process_df.columns:
        raise ValueError(
            f"Coluna '{process_client_code_col}' não encontrada na tabela de processos."
        )
    if client_code_col not in client_df.columns:
        raise ValueError(
            f"Coluna '{client_code_col}' não encontrada na tabela de clientes."
        )
    if client_name_col not in client_df.columns:
        raise ValueError(
            f"Coluna '{client_name_col}' não encontrada na tabela de clientes."
        )

    merged_df = process_df.merge(
        client_df[[client_code_col, client_name_col]],
        how="left",
        left_on=process_client_code_col,
        right_on=client_code_col,
    )

    merged_df[process_client_code_col] = merged_df[client_name_col]

    merged_df = merged_df.drop(columns=[client_code_col, client_name_col])

    return merged_df


def get_action_group(
    process_number: str, group_mapping: dict, group_process_code: str
) -> str:
    process_number_cleaned = clean_string(process_number).strip()

    if not process_number_cleaned:
        return "Administrativo"

    if len(process_number_cleaned) < 20:
        return "Extrajudicial"

    group_name = group_mapping.get(group_process_code, "Sem grupo mapeado")

    return group_name


def fill_with_default(df: pd.DataFrame, config: Dict, *Args: str) -> pd.DataFrame:
    default_value = config["DEFAULT_VALUE_FOR_MISSING"]

    for arg in Args:
        if arg not in df.columns:
            raise ValueError(f"Coluna '{arg}' não encontrada no DataFrame.")
        df[arg] = df[arg].fillna(default_value)

    return df


def get_fase_processo(phase_code: str, phase_mapping: dict, config: Dict) -> str:
    phase_code_cleaned = clean_string(phase_code).strip()

    if not phase_code_cleaned or not phase_code_cleaned.isdigit():
        return "Desconhecido"

    return phase_mapping.get(
        int(phase_code_cleaned), config.get("DEFAULT_VALUE_FOR_MISSING", "Desconhecido")
    )


def get_etapa(status_code: str, status_mapping: dict, config: Dict) -> str:
    status_code_cleaned = clean_string(status_code).strip()

    if not status_code_cleaned or not status_code_cleaned.isdigit():
        return config.get("DEFAULT_VALUE_FOR_MISSING", "Desconhecido")

    return status_mapping.get(
        int(status_code_cleaned),
        config.get("DEFAULT_VALUE_FOR_MISSING", "Desconhecido"),
    )


def process_number(
    patter1: Pattern[str], patter2: Pattern[str], value: str
) -> str | None:
    if pd.isna(value):
        return None
    value = str(value)
    if patter1.match(value):
        return value
    elif patter2.match(value):
        return value.zfill(20)
    return None


def standardize_process_number(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    invalid_move_config = config.get("IF_INVALID_MOVE_TO", {})

    pattern1 = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")
    pattern2 = re.compile(r"^\d{1,19}$")

    for source_col, target_col in invalid_move_config.items():
        if source_col not in df.columns:
            continue

        if target_col not in df.columns:
            df[target_col] = ""

        processed_values = df[source_col].apply(
            lambda x: process_number(pattern1, pattern2, x)
        )

        invalid_mask = processed_values.isna()
        invalid_values = df.loc[invalid_mask, source_col].fillna("").astype(str)

        df[target_col] = df[target_col].fillna("").astype(str)
        df.loc[invalid_mask, target_col] = (
            df.loc[invalid_mask, target_col] + ", " + invalid_values
        ).str.strip(", ")

        df[source_col] = processed_values

    return df


def standardize_origin_process(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    invalid_move_config = config.get("IF_INVALID_MOVE_TO", {})
    source_col = "PROCESSO ORIGINÁRIO"
    target_col = invalid_move_config.get(source_col, "PROTOCOLO")
    phase_col = "FASE PROCESSUAL"

    cnj_pattern = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")
    numeric_pattern = re.compile(r"^\d{1,19}$")

    if source_col not in df.columns:
        return df

    if target_col not in df.columns:
        df[target_col] = ""

    processed_values = df[source_col].apply(
        lambda x: process_number(cnj_pattern, numeric_pattern, x)
    )

    invalid_values = df.loc[processed_values.isna(), source_col].fillna("").astype(str)

    df[target_col] = (
        df[target_col].astype(str).replace("nan", "").str.strip(", ")
        + ", "
        + invalid_values
    ).str.strip(", ")

    df[source_col] = processed_values

    valid_cnj_mask = df[source_col].apply(lambda x: bool(cnj_pattern.match(str(x))))

    if phase_col in df.columns:
        df.loc[valid_cnj_mask, phase_col] = "RECURSAL"

    df[source_col] = df[source_col].fillna("Sem vínculo")

    return df


def map_tribunal(
    df: pd.DataFrame, tribunal_df: pd.DataFrame, recurso_df: pd.DataFrame, config: Dict
) -> pd.DataFrame:
    tribunal_col = config.get("TRIBUNAL_COLUMN", "TRIBUNAL")
    recurso_col = config.get("RECURSO_TRIBUNAL_COLUMN", "codtribunal")

    tribunal_mapping = dict(zip(tribunal_df["codigo"], tribunal_df["descricao"]))

    if tribunal_col not in df.columns:
        df[tribunal_col] = ""

    for index, row in df.iterrows():
        tribunal_code = recurso_df.loc[
            recurso_df["codprocesso"] == row["codigo"], recurso_col
        ].values

        if len(tribunal_code) > 0:
            tribunal_name = tribunal_mapping.get(tribunal_code[0], "Desconhecido")
            df.at[index, tribunal_col] = tribunal_name
        else:
            df.at[index, tribunal_col] = "Desconhecido"

    return df


def standardize_value_columns(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    money_columns = config.get("MONEY_COLUMNS", [])

    if not money_columns:
        raise ValueError(
            "A chave 'MONEY_COLUMNS' não foi encontrada no config ou está vazia."
        )

    for column_name in money_columns:
        if column_name not in df.columns:
            print(f"Coluna '{column_name}' não encontrada no DataFrame. Será ignorada.")
            continue

        def clean_value(value) -> str:
            if pd.isna(value):
                return "Desconhecido"
            value_str = str(value).strip()

            value_str = re.sub(r"[^\d.,-]", "", value_str)

            is_negative = False
            if "-" in value_str:
                is_negative = True
                value_str = value_str.replace("-", "")

            decimal_separators = value_str.count(",") + value_str.count(".")
            if decimal_separators > 1:
                return "Desconhecido"

            if "," in value_str and "." in value_str:
                return "Desconhecido"
            elif "," in value_str:
                value_str = value_str.replace(".", "")
                value_str = value_str.replace(",", ".")
            else:
                value_str = value_str.replace(",", "")

            try:
                numeric_value = float(value_str)
                if is_negative:
                    numeric_value = -numeric_value
                if numeric_value.is_integer():
                    formatted_value = f"{int(numeric_value)}"
                else:
                    formatted_value = f"{numeric_value:.2f}".replace(".", ",")
                return formatted_value
            except ValueError:
                return "Desconhecido"

        df[column_name] = df[column_name].apply(clean_value)

    return df


def standardize_registration_date(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    registration_column = config.get("DATA_CADASTRO_COLUMN", "DATA CADASTRO")
    distribution_column = config.get("DATA_DISTRIBUICAO_COLUMN", "DATA DE DISTRIBUIÇÃO")

    if registration_column not in df.columns:
        raise ValueError(f"Coluna '{registration_column}' não encontrada no DataFrame.")

    if distribution_column not in df.columns:
        df[distribution_column] = pd.NaT

    df[registration_column] = pd.to_datetime(
        df[registration_column], errors="coerce", dayfirst=True
    )
    df[distribution_column] = pd.to_datetime(
        df[distribution_column], errors="coerce", dayfirst=True
    )

    current_date = pd.Timestamp(datetime.now().date())

    df[registration_column] = df[registration_column].fillna(df[distribution_column])

    df[registration_column] = df[registration_column].fillna(current_date)

    df[registration_column] = df[registration_column].dt.strftime("%d/%m/%Y")

    return df


def standardize_closing_date(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    closing_column = config.get("DATA_FECHAMENTO_COLUMN", "DATA FECHAMENTO")
    registration_column = config.get("DATA_CADASTRO_COLUMN", "DATA CADASTRO")

    if closing_column not in df.columns:
        df[closing_column] = pd.NaT

    if registration_column not in df.columns:
        df[registration_column] = pd.NaT

    current_date = pd.Timestamp(datetime.now().date())

    df[closing_column] = pd.to_datetime(
        df[closing_column], errors="coerce", dayfirst=True
    )

    registration_dates = pd.to_datetime(
        df[registration_column], errors="coerce", dayfirst=True
    )

    df[closing_column] = df[closing_column].fillna(registration_dates)

    df[closing_column] = df[closing_column].fillna(current_date)

    df[closing_column] = df[closing_column].dt.strftime("%d/%m/%Y")

    return df


def standardize_transit_date(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    transit_column = config.get("DATA_TRANSITO_COLUMN", "DATA TRANSITO")

    if not transit_column in df.columns:
        print(f"A coluna '{transit_column}' não foi encontrada no DataFrame.")
        return df

    df[transit_column] = pd.to_datetime(
        df[transit_column], errors="coerce", dayfirst=True
    )

    df[transit_column] = df[transit_column].dt.strftime("%d/%m/%Y")

    return df


def format_date_column(
    df: pd.DataFrame,
    column_name: str,
    date_format: str = "%d/%m/%Y",
    fill_invalid: str = "",
) -> pd.DataFrame:
    if column_name not in df.columns:
        print(f"A coluna '{column_name}' não foi encontrada no DataFrame.")
        return df

    df[column_name] = pd.to_datetime(df[column_name], errors="coerce", dayfirst=True)

    df[column_name] = df[column_name].dt.strftime(date_format)

    if fill_invalid is not None:
        df[column_name] = df[column_name].fillna(fill_invalid)

    return df


def standardize_responsible(
    df: pd.DataFrame, user_df: pd.DataFrame, config: Dict[str, Any]
) -> pd.DataFrame:
    responsible_column = config.get("RESPONSIBLE_COLUMN", "RESPONSÁVEL")
    user_code_column = config.get("USER_CODE_COLUMN", "codigo")
    user_name_column = config.get("USER_NAME_COLUMN", "nome")

    if responsible_column not in df.columns:
        raise ValueError(
            f"Coluna '{responsible_column}' não encontrada no DataFrame de processos."
        )

    if (
        user_code_column not in user_df.columns
        or user_name_column not in user_df.columns
    ):
        raise ValueError(
            "Colunas esperadas na tabela de usuários não foram encontradas."
        )

    df[responsible_column] = df[responsible_column].astype(str)
    user_df[user_code_column] = user_df[user_code_column].astype(str)

    valid_users: Dict[str, str] = user_df.set_index(user_code_column)[
        user_name_column
    ].to_dict()

    df[responsible_column] = df[responsible_column].map(
        lambda x: valid_users.get(x, "")
    )

    return df
