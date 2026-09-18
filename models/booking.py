"""Booking model representing a customer's appointment."""

from datetime import datetime

VALID_STATUSES = ("Pending", "Confirmed", "Completed", "Cancelled")


class Booking:
    def __init__(self, booking_id, customer_id, barber_id, service_id, date_str, time_str, note=""):
        self.booking_id = booking_id
        self.customer_id = customer_id
        self.barber_id = barber_id
        self.service_id = service_id
        self.date_str = date_str      # "YYYY-MM-DD"
        self.time_str = time_str      # "HH:MM"
        self.note = note              # optional customer suggestion/special request
        self.status = "Pending"
        self.created_at = datetime.now()
        self.rating = None            # customer's 1-10 rating of the barber, set after completion

    def update_status(self, new_status):
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'.")
        self.status = new_status

    def cancel(self):
        if self.status == "Completed":
            raise ValueError("A completed booking cannot be cancelled.")
        self.status = "Cancelled"

    def set_rating(self, rating):
        """Customer rates the barber 1-10 once the service is Completed."""
        if self.status != "Completed":
            raise ValueError("You can only rate a completed appointment.")
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            raise ValueError("Rating must be a whole number between 1 and 10.")
        if rating < 1 or rating > 10:
            raise ValueError("Rating must be between 1 and 10.")
        self.rating = rating

    def matches_slot(self, barber_id, date_str, time_str):
        """Used to detect double-booking for the same barber."""
        return (
            self.barber_id == barber_id
            and self.date_str == date_str
            and self.time_str == time_str
            and self.status not in ("Cancelled",)
        )

    def to_dict(self):
        return {
            "booking_id": self.booking_id,
            "customer_id": self.customer_id,
            "barber_id": self.barber_id,
            "service_id": self.service_id,
            "date": self.date_str,
            "time": self.time_str,
            "note": self.note,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "rating": self.rating,
        }

    def __repr__(self):
        return f"<Booking #{self.booking_id} {self.status}>"
