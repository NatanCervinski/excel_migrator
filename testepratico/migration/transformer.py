import pandas as pd
from config import settings
from helpers import format_cpf, verify_column_exists_in_dataframe


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna(settings.DEFAULT_VALUE_FOR_MISSING)


def standardize_dates(df: pd.DataFrame) -> pd.DataFrame:
    for column in settings.DATE_COLUMNS:
        if not verify_column_exists_in_dataframe(df, column):
            continue
        df[column] = pd.to_datetime(df[column], errors="coerce").dt.strftime("%d/%m/%Y")
    return df


def standardize_cpfs(df: pd.DataFrame) -> pd.DataFrame:
    if not verify_column_exists_in_dataframe(df, settings.CPF_CNPJ_COLUMN):
        return df

    df[settings.CPF_CNPJ_COLUMN] = df[settings.CPF_CNPJ_COLUMN].apply(format_cpf)
    return df


def map_fields(source_df: pd.DataFrame) -> pd.DataFrame:
    field_mapping = {
        k: v
        for k, v in settings.FIELD_MAPPINGS.items()
        if verify_column_exists_in_dataframe(source_df, k)
    }

    return source_df.rename(columns=field_mapping)
