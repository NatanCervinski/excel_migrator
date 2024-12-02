from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev",
    )

    # Importar e registrar rotas
    from . import routes

    app.register_blueprint(routes.bp)

    return app
