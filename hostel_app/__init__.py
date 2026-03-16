from flask import Flask

from .routes.allocations import allocations_bp
from .routes.auth import auth_bp
from .routes.dashboard import dashboard_bp
from .routes.expenses import expenses_bp
from .routes.rents import rents_bp
from .routes.rooms import rooms_bp
from .routes.students import students_bp


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = "your_secure_secret_key_here_change_this"

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(allocations_bp)
    app.register_blueprint(rents_bp)

    return app
