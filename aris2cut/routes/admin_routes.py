from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from data import store
from models import Barber, Service
from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    total_barbers = len(store.get_users_by_role("barber"))
    total_customers = len(store.get_users_by_role("customer"))
    total_services = len(store.services)
    total_bookings = len(store.bookings)
    pending = len([b for b in store.bookings if b.status == "Pending"])

    initial_point = _current_snapshot()

    return render_template(
        "admin/dashboard.html",
        total_barbers=total_barbers,
        total_customers=total_customers,
        total_services=total_services,
        total_bookings=total_bookings,
        pending=pending,
        initial_point=initial_point,
    )


@admin_bp.route("/api/live-stats")
@role_required("admin")
def live_stats():
    """Polled by the dashboard so the haircut-demand chart and the
    revenue total stay live: as soon as a booking is made for today,
    the very next poll picks it up and the chart redraws."""
    return _current_snapshot()


def _current_snapshot():
    """Today's per-haircut booking demand + today's revenue, as of right now."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    todays_bookings = [b for b in store.bookings if b.date_str == today_str]

    counts = {s.name: 0 for s in store.services}
    revenue_today = 0.0
    for b in todays_bookings:
        service = store.get_service_by_id(b.service_id)
        if service:
            counts[service.name] = counts.get(service.name, 0) + 1
            revenue_today += service.price

    haircuts = sorted(
        ({"name": name, "count": count} for name, count in counts.items()),
        key=lambda x: (-x["count"], x["name"]),
    )

    return {
        "time": datetime.now().strftime("%I:%M:%S %p"),
        "haircuts": haircuts,
        "revenue_today": round(revenue_today, 2),
        "bookings_today": len(todays_bookings),
    }


# ---------------- BARBER MANAGEMENT (CRUD) ----------------
@admin_bp.route("/barbers", methods=["GET", "POST"])
@role_required("admin")
def barbers():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        specialty = request.form.get("specialty", "").strip()

        if not full_name or not username or len(password) < 4:
            flash("Please fill all fields; password must be 4+ characters.", "error")
        elif store.get_user_by_username(username):
            flash("That username is already taken.", "error")
        else:
            store.add_user(Barber(store.next_user_id(), full_name, username, password, specialty or "General"))
            flash("Barber added successfully.", "success")
        return redirect(url_for("admin.barbers"))

    return render_template("admin/barbers.html", barbers=store.get_users_by_role("barber"))


@admin_bp.route("/barbers/<int:user_id>/update", methods=["POST"])
@role_required("admin")
def update_barber(user_id):
    barber = store.get_user_by_id(user_id)
    if not barber or barber.role != "barber":
        flash("Barber not found.", "error")
        return redirect(url_for("admin.barbers"))

    full_name = request.form.get("full_name", "").strip()
    specialty = request.form.get("specialty", "").strip()
    is_active = request.form.get("is_active") == "on"

    if not full_name:
        flash("Full name cannot be empty.", "error")
        return redirect(url_for("admin.barbers"))

    barber.full_name = full_name
    barber.specialty = specialty or barber.specialty
    barber.is_active = is_active
    flash("Barber updated.", "success")
    return redirect(url_for("admin.barbers"))


@admin_bp.route("/barbers/<int:user_id>/delete", methods=["POST"])
@role_required("admin")
def delete_barber(user_id):
    barber = store.get_user_by_id(user_id)
    if barber and barber.role == "barber":
        store.delete_user(user_id)
        flash("Barber removed.", "success")
    else:
        flash("Barber not found.", "error")
    return redirect(url_for("admin.barbers"))


# ---------------- SERVICE MANAGEMENT (CRUD) ----------------
@admin_bp.route("/services", methods=["GET", "POST"])
@role_required("admin")
def services():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "")
        duration = request.form.get("duration", "")
        description = request.form.get("description", "").strip()

        errors = []
        if not name:
            errors.append("Service name is required.")
        try:
            price = float(price)
            if price <= 0:
                errors.append("Price must be greater than 0.")
        except ValueError:
            errors.append("Price must be a valid number.")
        try:
            duration = int(duration)
            if duration <= 0:
                errors.append("Duration must be greater than 0.")
        except ValueError:
            errors.append("Duration must be a whole number of minutes.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            store.add_service(Service(store.next_service_id(), name, price, duration, description))
            flash("Service added.", "success")
        return redirect(url_for("admin.services"))

    return render_template("admin/services.html", services=store.services)


@admin_bp.route("/services/<int:service_id>/update", methods=["POST"])
@role_required("admin")
def update_service(service_id):
    service = store.get_service_by_id(service_id)
    if not service:
        flash("Service not found.", "error")
        return redirect(url_for("admin.services"))

    try:
        name = request.form.get("name", "").strip()
        price = float(request.form.get("price"))
        duration = int(request.form.get("duration"))
        description = request.form.get("description", "").strip()
        service.update(name=name, price=price, duration_minutes=duration, description=description)
        service.is_active = request.form.get("is_active") == "on"
        flash("Service updated.", "success")
    except (ValueError, TypeError):
        flash("Invalid price or duration.", "error")

    return redirect(url_for("admin.services"))


@admin_bp.route("/services/<int:service_id>/delete", methods=["POST"])
@role_required("admin")
def delete_service(service_id):
    if store.delete_service(service_id):
        flash("Service deleted.", "success")
    else:
        flash("Service not found.", "error")
    return redirect(url_for("admin.services"))


# ---------------- BOOKING OVERSIGHT ----------------
@admin_bp.route("/bookings")
@role_required("admin")
def bookings():
    enriched = _enrich_bookings(store.bookings)
    return render_template("admin/bookings.html", bookings=enriched)


@admin_bp.route("/bookings/<int:booking_id>/update", methods=["POST"])
@role_required("admin")
def update_booking(booking_id):
    booking = store.get_booking_by_id(booking_id)
    new_status = request.form.get("status")
    if not booking:
        flash("Booking not found.", "error")
    else:
        try:
            booking.update_status(new_status)
            flash("Booking status updated.", "success")
        except ValueError as e:
            flash(str(e), "error")
    return redirect(url_for("admin.bookings"))


@admin_bp.route("/bookings/<int:booking_id>/delete", methods=["POST"])
@role_required("admin")
def delete_booking(booking_id):
    if store.delete_booking(booking_id):
        flash("Booking deleted.", "success")
    else:
        flash("Booking not found.", "error")
    return redirect(url_for("admin.bookings"))


def _enrich_bookings(bookings_list):
    """Attach readable customer/barber/service names for template display."""
    result = []
    for b in bookings_list:
        customer = store.get_user_by_id(b.customer_id)
        barber = store.get_user_by_id(b.barber_id)
        service = store.get_service_by_id(b.service_id)
        result.append({
            "booking": b,
            "customer_name": customer.full_name if customer else "Unknown",
            "barber_name": barber.full_name if barber else "Unknown",
            "service_name": service.name if service else "Unknown",
            "service_price": service.price if service else 0,
            "note": b.note,
        })
    return result
