from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from data import store
from models import Customer

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


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Only customers may self-register. Admin/Barber accounts are
    created by the Admin from the admin dashboard."""
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        phone = request.form.get("phone", "").strip()

        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not username:
            errors.append("Username is required.")
        elif store.get_user_by_username(username):
            errors.append("That username is already taken.")
        if len(password) < 4:
            errors.append("Password must be at least 4 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", form=request.form)

        new_customer = Customer(store.next_user_id(), full_name, username, password, phone)
        store.add_user(new_customer)
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form={})


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
