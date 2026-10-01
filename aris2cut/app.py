from flask import Flask, render_template

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.barber_routes import barber_bp
from routes.customer_routes import customer_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "dev-secret-key-change-me-in-production"  # needed for sessions/flash

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(barber_bp)
    app.register_blueprint(customer_bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    # host=0.0.0.0 so it can be reached when deployed (e.g. on Render/Railway)
    app.run(host="0.0.0.0", port=5000, debug=True)
