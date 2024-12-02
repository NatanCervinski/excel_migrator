# testepratico/web/routes.py

import io
import os
import zipfile

from dynaconf import settings
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
)
from werkzeug.utils import secure_filename

from testepratico.migration import clientes, extractor, processos

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "rar_file" not in request.files or request.files["rar_file"].filename == "":
            flash("Nenhum arquivo selecionado.")
            return redirect(request.url)

        file = request.files["rar_file"]

        if file.filename is None:
            flash("Nenhum arquivo selecionado.")
            return redirect(request.url)

        filename = secure_filename(file.filename)

        if not filename.lower().endswith((".zip", ".rar")):
            flash(
                "Tipo de arquivo não permitido. Por favor, envie um arquivo .zip ou .rar."
            )
            return redirect(request.url)

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        required_files = (
            settings.MIGRATION_CONFIGS.clientes.REQUIRED_FILES
            + settings.MIGRATION_CONFIGS.processos.REQUIRED_FILES
        )
        try:
            dic_df = extractor.load_csv_from_compressed_file(
                file_path, required_files, delimiter=";"
            )
            clientes.migrate_clients(dic_df)
            processos.migrate_processes(dic_df)
            processed_files = ["CLIENTES.xlsx", "PROCESSOS.xlsx"]

            return render_template("download.html", files=processed_files)

        except ValueError as ve:
            flash(f"Erro: {ve}")
            return redirect(request.url)
        except FileNotFoundError as fnfe:
            flash(f"Erro: {fnfe}")
            return redirect(request.url)
        except Exception as e:
            flash(f"Ocorreu um erro inesperado: {e}")
            return redirect(request.url)
    return render_template("index.html")


@main.route("/download/<filename>")
def download_file(filename):
    print(filename)
    filename = secure_filename(filename)
    allowed_files = ["CLIENTES.xlsx", "PROCESSOS.xlsx"]
    if filename not in allowed_files:
        abort(404)

    processed_folder = os.path.abspath(settings.PROCESSED_FOLDER)
    print(processed_folder)
    print(filename)
    return send_from_directory(processed_folder, filename, as_attachment=True)


@main.route("/download_all")
def download_all():
    processed_folder = os.path.abspath(settings.PROCESSED_FOLDER)
    processed_files = ["CLIENTES.xlsx", "PROCESSOS.xlsx"]
    data = io.BytesIO()
    with zipfile.ZipFile(data, mode="w") as z:
        for file_name in processed_files:
            file_path = os.path.join(processed_folder, file_name)
            z.write(file_path, arcname=file_name)
    data.seek(0)

    return send_file(
        data,
        mimetype="application/zip",
        as_attachment=True,
        download_name="arquivos_processados.zip",
    )
