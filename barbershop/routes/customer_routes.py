from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from data import store
from models import Booking
from utils.decorators import role_required

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


@customer_bp.route("/dashboard")
@role_required("customer")
def dashboard():
    customer_id = session["user_id"]
    my_bookings = store.get_bookings_for_customer(customer_id)

    enriched = []
    for b in my_bookings:
        barber = store.get_user_by_id(b.barber_id)
        service = store.get_service_by_id(b.service_id)
        enriched.append({
            "booking": b,
            "barber_name": barber.full_name if barber else "Unknown",
            "service_name": service.name if service else "Unknown",
            "service_price": service.price if service else 0,
        })

    enriched.sort(key=lambda x: (x["booking"].date_str, x["booking"].time_str), reverse=True)

    return render_template("customer/dashboard.html", bookings=enriched)


@customer_bp.route("/profile")
@role_required("customer")
def profile():
    customer_id = session["user_id"]
    customer = store.get_user_by_id(customer_id)
    my_bookings = store.get_bookings_for_customer(customer_id)

    enriched = []
    for b in my_bookings:
        barber = store.get_user_by_id(b.barber_id)
        service = store.get_service_by_id(b.service_id)
        enriched.append({
            "booking": b,
            "barber_name": barber.full_name if barber else "Unknown",
            "service_name": service.name if service else "Unknown",
            "service_price": service.price if service else 0,
        })

    enriched.sort(key=lambda x: (x["booking"].date_str, x["booking"].time_str), reverse=True)

    total_count = len(my_bookings)
    completed_count = len([b for b in my_bookings if b.status == "Completed"])
    cancelled_count = len([b for b in my_bookings if b.status == "Cancelled"])
    ratings_given = [b.rating for b in my_bookings if b.rating is not None]

    return render_template(
        "customer/profile.html",
        customer=customer,
        bookings=enriched,
        total_count=total_count,
        completed_count=completed_count,
        cancelled_count=cancelled_count,
        ratings_given_count=len(ratings_given),
    )


@customer_bp.route("/book", methods=["GET", "POST"])
@role_required("customer")
def book():
    barbers = [b for b in store.get_users_by_role("barber") if b.is_active]
    services = store.get_active_services()
    haircut_styles = store.get_all_haircut_styles()

    if request.method == "POST":
        barber_id = request.form.get("barber_id")
        service_id = request.form.get("service_id")
        date_str = request.form.get("date", "").strip()
        time_str = request.form.get("time", "").strip()
        note = request.form.get("note", "").strip()

        errors = []

        barber = store.get_user_by_id(barber_id) if barber_id else None
        service = store.get_service_by_id(service_id) if service_id else None

        if not barber or barber.role != "barber":
            errors.append("Please select a valid barber.")
        if not service:
            errors.append("Please select a valid service.")
        if not date_str:
            errors.append("Please choose a date.")
        else:
            try:
                chosen_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if chosen_date < datetime.now().date():
                    errors.append("You cannot book a date in the past.")
            except ValueError:
                errors.append("Invalid date format.")
        if not time_str:
            errors.append("Please choose a time.")
        if len(note) > 300:
            errors.append("Suggestion/notes must be under 300 characters.")

        if not errors and store.is_slot_taken(barber_id, date_str, time_str):
            errors.append("That barber is already booked at this date/time. Please pick another slot.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("customer/book.html", barbers=barbers, services=services,
                                   haircut_styles=haircut_styles, form=request.form)

        booking = Booking(
            store.next_booking_id(),
            customer_id=session["user_id"],
            barber_id=int(barber_id),
            service_id=int(service_id),
            date_str=date_str,
            time_str=time_str,
            note=note,
        )
        store.add_booking(booking)
        flash("Appointment booked successfully!", "success")
        return redirect(url_for("customer.dashboard"))

    return render_template("customer/book.html", barbers=barbers, services=services,
                           haircut_styles=haircut_styles, form={})


@customer_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@role_required("customer")
def cancel_booking(booking_id):
    booking = store.get_booking_by_id(booking_id)

    if not booking:
        flash("Booking not found.", "error")
    elif booking.customer_id != session["user_id"]:
        flash("You may only cancel your own bookings.", "error")
    else:
        try:
            booking.cancel()
            flash("Booking cancelled.", "success")
        except ValueError as e:
            flash(str(e), "error")

    return redirect(url_for("customer.dashboard"))


@customer_bp.route("/bookings/<int:booking_id>/rate", methods=["POST"])
@role_required("customer")
def rate_booking(booking_id):
    booking = store.get_booking_by_id(booking_id)
    rating = request.form.get("rating")

    if not booking:
        flash("Booking not found.", "error")
    elif booking.customer_id != session["user_id"]:
        flash("You may only rate your own bookings.", "error")
    else:
        try:
            booking.set_rating(rating)
            flash("Thanks! Your rating has been submitted.", "success")
        except ValueError as e:
            flash(str(e), "error")

    return redirect(url_for("customer.dashboard"))
