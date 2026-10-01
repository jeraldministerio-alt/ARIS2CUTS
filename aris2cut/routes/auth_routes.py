from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from data import store

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard_redirect"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("login.html")

        user = store.get_user_by_username(username)

        if not user or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        if not user.is_active:
            flash("This account has been deactivated.", "error")
            return render_template("login.html")

        session["user_id"] = user.user_id
        session["role"] = user.role
        session["full_name"] = user.full_name
        flash(f"Welcome back, {user.full_name}!", "success")
        return redirect(user.get_dashboard_url())  # polymorphism in action

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/dashboard")
def dashboard_redirect():
    """Send a logged-in user to the correct dashboard for their role."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = store.get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    return redirect(user.get_dashboard_url())
