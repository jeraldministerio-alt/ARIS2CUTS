"""Reusable decorators for login and role-based access control."""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """Restrict a view to one or more roles, e.g. @role_required('admin')"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("auth.login"))
            if session.get("role") not in allowed_roles:
                flash("You do not have permission to view that page.", "error")
                return redirect(url_for("auth.dashboard_redirect"))
            return view_func(*args, **kwargs)
        return wrapper
    return decorator
