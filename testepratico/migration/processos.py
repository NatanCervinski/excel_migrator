from typing import Dict

import pandas as pd
from dynaconf import settings

from testepratico.migration.loader import save_dataframes_as_excel
from testepratico.migration.transformer import (
    fill_with_default,
    filter_required_columns,
    format_date_column,
    get_action_group,
    get_etapa,
    get_fase_processo,
    map_fields,
    map_tribunal,
    merge_process_with_client,
    standardize_closing_date,
    standardize_origin_process,
    standardize_process_number,
    standardize_registration_date,
    standardize_responsible,
    standardize_value_columns,
)


def migrate_processes(dic_df: Dict[str, pd.DataFrame]) -> None:
    configs = settings.MIGRATION_CONFIGS.processos

    for file in configs["REQUIRED_FILES"]:
        if file not in dic_df:
            raise ValueError(f"Arquivo {file} não encontrado.")

    process_df = dic_df["processos"]
    clientes_df = dic_df["clientes"]
    usuarios_df = dic_df["usuario"]
    tribunal_df = dic_df["tribunal"]
    recurso_df = dic_df["recurso"]
    status_processual_df = dic_df["statusprocessual"]
    fase_df = dic_df["fase"]
    grupo_processo_df = dic_df["grupo_processo"]

    statusprocessual_dict = status_processual_df.set_index("codigo")[
        "descricao"
    ].to_dict()
    fase_dict = fase_df.set_index("codigo")["fase"].to_dict()
    codigo_descricao_dict = grupo_processo_df.set_index("codigo")["descricao"].to_dict()

    process_df = fill_with_default(
        process_df, configs, "tipo_acao", "cod_parte_adversa"
    )

    process_df = map_tribunal(process_df, tribunal_df, recurso_df, configs)

    process_df = filter_required_columns(process_df, configs)

    merged_df = merge_process_with_client(process_df, clientes_df, configs)

    process_df = map_fields(merged_df, configs)

    process_df["GRUPO DE AÇÃO"] = process_df.apply(
        lambda row: get_action_group(
            process_number=row["NÚMERO DO PROCESSO"],
            group_mapping=codigo_descricao_dict,
            group_process_code=row["GRUPO DE AÇÃO"],
        ),
        axis=1,
    )

    process_df["FASE PROCESSUAL"] = process_df["FASE PROCESSUAL"].apply(
        lambda code: get_fase_processo(
            phase_code=code,
            phase_mapping=fase_dict,
            config=configs,
        )
    )

    process_df["ETAPA"] = process_df["ETAPA"].apply(
        lambda code: get_etapa(
            status_code=code,
            status_mapping=statusprocessual_dict,
            config=configs,
        )
    )

    process_df = standardize_process_number(process_df, configs)
    process_df = standardize_origin_process(process_df, configs)
    process_df = standardize_value_columns(process_df, configs)
    process_df = standardize_registration_date(process_df, configs)
    process_df = standardize_closing_date(process_df, configs)

    for col in configs["DATE_COLUMNS"]:
        process_df = format_date_column(process_df, col)

    process_df = standardize_responsible(process_df, usuarios_df, configs)

    output_directory = settings.PROCESSED_FOLDER
    save_dataframes_as_excel({"PROCESSOS": process_df}, output_directory)
