from typing import Dict

import pandas as pd
from dynaconf import settings
from migration.loader import save_dataframes_as_excel
from migration.transformer import (
    filter_required_columns,
    format_date_column,
    handle_missing_values,
    map_fields,
    standardize_cep,
    standardize_cpf_cnpj,
    standardize_emails,
    standardize_phone,
)


def migrate_clients(dic_df: Dict[str, pd.DataFrame]) -> None:
    configs = settings.MIGRATION_CONFIGS.clientes

    clients_df = dic_df["clientes"]

    clients_df = filter_required_columns(clients_df, configs)

    clients_df = map_fields(clients_df, configs)

    clients_df = handle_missing_values(clients_df, configs)

    clients_df = standardize_cpf_cnpj(clients_df, configs)
    clients_df = standardize_phone(clients_df, configs)
    clients_df = standardize_emails(clients_df, configs)
    clients_df = standardize_cep(clients_df, configs)

    clients_df = format_date_column(clients_df, "DATA DE NASCIMENTO")

    output_directory = settings.PROCESSED_FOLDER

    save_dataframes_as_excel({"CLIENTES": clients_df}, output_directory)
