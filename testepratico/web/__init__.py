from flask import Flask


def create_app():
    app = Flask(__name__)

    # Configurações adicionais podem ser adicionadas aqui
    app.config["SECRET_KEY"] = "sua_chave_secreta_aqui"
    app.config["UPLOAD_FOLDER"] = "uploads"  # Diretório para uploads

    # Registrar as rotas
    from .routes import main

    app.register_blueprint(main)

    return app
