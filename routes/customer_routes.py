from datetime import datetime, time

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

from data import store
from models import Booking
from utils.decorators import role_required

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")

# Shop booking hours: appointments can only be booked from 8:00 AM to 8:00 PM.
# Change these two values to adjust the allowed window everywhere (server
# validation, the time picker limits, and the hint shown on the form).
BOOKING_OPEN = time(8, 0)
BOOKING_CLOSE = time(20, 0)


# Double-booking rule. False = an appointment only blocks the SAME barber's
# time. Set to True to block the time for the whole shop (one chair).
BLOCK_ACROSS_ALL_BARBERS = False


def _fmt_minutes(total):
    h, m = divmod(total, 60)
    suffix = "AM" if h < 12 else "PM"
    return f"{(h % 12) or 12}:{m:02d} {suffix}"


def _booking_hours_context():
    return {
        "booking_open": BOOKING_OPEN.strftime("%H:%M"),
        "booking_close": BOOKING_CLOSE.strftime("%H:%M"),
        "booking_open_label": BOOKING_OPEN.strftime("%I:%M %p").lstrip("0"),
        "booking_close_label": BOOKING_CLOSE.strftime("%I:%M %p").lstrip("0"),
    }


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


def _open_booking_info(customer_id):
    """Details of the client's unfinished booking (blocks booking again), or None."""
    booking = store.get_open_booking_for_customer(customer_id)
    if not booking:
        return None
    service = store.get_service_by_id(booking.service_id)
    barber = store.get_user_by_id(booking.barber_id)
    return {
        "booking": booking,
        "service_name": service.name if service else "Unknown",
        "barber_name": barber.full_name if barber else "Unknown",
    }


@customer_bp.route("/book", methods=["GET", "POST"])
@role_required("customer")
def book():
    open_booking = _open_booking_info(session["user_id"])
    if open_booking:
        if request.method == "POST":
            flash("You already have an appointment that isn't completed yet. "
                  "Please wait until it is completed (or cancel it) before booking again.", "error")
            return redirect(url_for("customer.book"))
        return render_template("customer/book.html", barbers=[], services=[], form={},
                               open_booking=open_booking, **_booking_hours_context())

    barbers = [b for b in store.get_users_by_role("barber") if b.is_active]
    services = store.get_active_services()

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
            chosen_date = None
        else:
            try:
                chosen_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if chosen_date < datetime.now().date():
                    errors.append("You cannot book a date in the past.")
            except ValueError:
                errors.append("Invalid date format.")
                chosen_date = None

        if not time_str:
            errors.append("Please choose a time.")
        elif chosen_date is not None:
            try:
                chosen_time = datetime.strptime(time_str, "%H:%M").time()
                now = datetime.now()
                if not (BOOKING_OPEN <= chosen_time <= BOOKING_CLOSE):
                    hours = _booking_hours_context()
                    errors.append(
                        f"Bookings are only available between {hours['booking_open_label']} "
                        f"and {hours['booking_close_label']}."
                    )
                elif chosen_date == now.date() and chosen_time < now.time():
                    errors.append("That time has already passed today. Please choose the current time or later.")
            except ValueError:
                errors.append("Invalid time format.")
        if len(note) > 300:
            errors.append("Suggestion/notes must be under 300 characters.")

        if not errors:
            conflict = store.find_conflict(
                int(barber_id), date_str, time_str, service.duration_minutes,
                all_barbers=BLOCK_ACROSS_ALL_BARBERS,
            )
            if conflict:
                start = store._to_minutes(conflict.time_str)
                end = start + store._booking_minutes(conflict)
                errors.append(
                    f"Sorry, that time is already booked by another client "
                    f"({_fmt_minutes(start)} - {_fmt_minutes(end)}). Please pick another time."
                )

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("customer/book.html", barbers=barbers, services=services,
                                   form=request.form, open_booking=None,
                                   **_booking_hours_context())

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
                           form={}, open_booking=None,
                           **_booking_hours_context())


@customer_bp.route("/api/booked-slots")
@role_required("customer")
def booked_slots():
    """Times already taken on a date, so the booking form can warn up front."""
    date_str = request.args.get("date", "")
    barber_id = request.args.get("barber_id") or None
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        if barber_id is not None:
            barber_id = int(barber_id)
    except ValueError:
        return jsonify({"slots": []})

    scope = None if BLOCK_ACROSS_ALL_BARBERS else barber_id
    if scope is None and not BLOCK_ACROSS_ALL_BARBERS:
        return jsonify({"slots": []})  # no barber chosen yet

    slots = [
        {"start": start, "end": end, "label": f"{_fmt_minutes(start)} - {_fmt_minutes(end)}"}
        for start, end, _ in sorted(store.get_booked_ranges(date_str, scope), key=lambda r: r[0])
    ]
    return jsonify({"slots": slots})


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
