import os

from flask import Flask

from . import db
from .routes.allocations import allocations_bp
from .routes.dashboard import dashboard_bp
from .routes.expenses import expenses_bp
from .routes.rents import rents_bp
from .routes.rooms import rooms_bp
from .routes.students import students_bp


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    db.init_app(app)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(allocations_bp)
    app.register_blueprint(rents_bp)

    return app
