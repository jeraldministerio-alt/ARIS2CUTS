from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from data import store
from utils.decorators import role_required

barber_bp = Blueprint("barber", __name__, url_prefix="/barber")


@barber_bp.route("/dashboard")
@role_required("barber")
def dashboard():
    barber_id = session["user_id"]
    my_bookings = store.get_bookings_for_barber(barber_id)

    enriched = []
    for b in my_bookings:
        customer = store.get_user_by_id(b.customer_id)
        service = store.get_service_by_id(b.service_id)
        enriched.append({
            "booking": b,
            "customer_name": customer.full_name if customer else "Unknown",
            "customer_phone": getattr(customer, "phone", ""),
            "service_name": service.name if service else "Unknown",
            "note": b.note,
        })

    # newest bookings first
    enriched.sort(key=lambda x: (x["booking"].date_str, x["booking"].time_str))

    pending_count = len([b for b in my_bookings if b.status == "Pending"])
    confirmed_count = len([b for b in my_bookings if b.status == "Confirmed"])
    completed_count = len([b for b in my_bookings if b.status == "Completed"])

    ratings = [b.rating for b in my_bookings if b.rating is not None]
    average_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
    rating_count = len(ratings)

    return render_template(
        "barber/dashboard.html",
        bookings=enriched,
        pending_count=pending_count,
        confirmed_count=confirmed_count,
        completed_count=completed_count,
        average_rating=average_rating,
        rating_count=rating_count,
    )


@barber_bp.route("/bookings/<int:booking_id>/update", methods=["POST"])
@role_required("barber")
def update_booking(booking_id):
    booking = store.get_booking_by_id(booking_id)
    new_status = request.form.get("status")

    if not booking:
        flash("Booking not found.", "error")
    elif booking.barber_id != session["user_id"]:
        flash("You may only update your own bookings.", "error")
    else:
        try:
            booking.update_status(new_status)
            flash("Booking status updated.", "success")
        except ValueError as e:
            flash(str(e), "error")

    return redirect(url_for("barber.dashboard"))
