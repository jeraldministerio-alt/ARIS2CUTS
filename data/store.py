"""
Temporary in-memory storage.

Per the project requirements, NO DATABASE is used — everything lives in
plain Python lists for the lifetime of the running process. The manager
classes below wrap those lists and expose CRUD-style methods, which keeps
the raw lists encapsulated instead of being poked at directly from routes.
"""

from itertools import count
from models import Admin, Barber, Customer, Service, Booking


class DataStore:
    """Singleton-style container holding every list used by the app."""

    def __init__(self):
        self.users = []            # list[User]  (Admin / Barber / Customer)
        self.services = []         # list[Service]
        self.bookings = []         # list[Booking]

        self._user_ids = count(1)
        self._service_ids = count(1)
        self._booking_ids = count(1)

        self._seed_data()

    # ---------------- USERS ----------------
    def add_user(self, user):
        self.users.append(user)
        return user

    def next_user_id(self):
        return next(self._user_ids)

    def get_user_by_username(self, username):
        return next((u for u in self.users if u.username.lower() == username.lower()), None)

    def get_user_by_id(self, user_id):
        return next((u for u in self.users if u.user_id == int(user_id)), None)

    def get_users_by_role(self, role):
        return [u for u in self.users if u.role == role]

    def delete_user(self, user_id):
        user = self.get_user_by_id(user_id)
        if user:
            self.users.remove(user)
        return user

    # ---------------- SERVICES ----------------
    def next_service_id(self):
        return next(self._service_ids)

    def add_service(self, service):
        self.services.append(service)
        return service

    def get_service_by_id(self, service_id):
        return next((s for s in self.services if s.service_id == int(service_id)), None)

    def get_active_services(self):
        return [s for s in self.services if s.is_active]

    def delete_service(self, service_id):
        service = self.get_service_by_id(service_id)
        if service:
            self.services.remove(service)
        return service

    # ---------------- BOOKINGS ----------------
    def next_booking_id(self):
        return next(self._booking_ids)

    def add_booking(self, booking):
        self.bookings.append(booking)
        return booking

    def get_booking_by_id(self, booking_id):
        return next((b for b in self.bookings if b.booking_id == int(booking_id)), None)

    def get_bookings_for_customer(self, customer_id):
        return [b for b in self.bookings if b.customer_id == int(customer_id)]

    def get_open_booking_for_customer(self, customer_id):
        """The customer's earliest booking that is not finished yet
        (Pending or Confirmed). Completed and Cancelled ones don't count."""
        open_bookings = [b for b in self.bookings
                         if b.customer_id == int(customer_id) and b.status in ("Pending", "Confirmed")]
        open_bookings.sort(key=lambda b: (b.date_str, b.time_str))
        return open_bookings[0] if open_bookings else None

    def get_bookings_for_barber(self, barber_id):
        return [b for b in self.bookings if b.barber_id == int(barber_id)]

    def is_slot_taken(self, barber_id, date_str, time_str, ignore_booking_id=None):
        for b in self.bookings:
            if ignore_booking_id and b.booking_id == int(ignore_booking_id):
                continue
            if b.matches_slot(int(barber_id), date_str, time_str):
                return True
        return False

    def _booking_minutes(self, booking):
        service = self.get_service_by_id(booking.service_id)
        return service.duration_minutes if service else 30

    @staticmethod
    def _to_minutes(time_str):
        h, m = time_str.split(":")
        return int(h) * 60 + int(m)

    def get_booked_ranges(self, date_str, barber_id=None, ignore_booking_id=None):
        """Active (non-cancelled) appointments on a date as (start, end, booking)
        in minutes-from-midnight. barber_id=None means every barber."""
        ranges = []
        for b in self.bookings:
            if b.status == "Cancelled" or b.date_str != date_str:
                continue
            if barber_id is not None and b.barber_id != int(barber_id):
                continue
            if ignore_booking_id and b.booking_id == int(ignore_booking_id):
                continue
            start = self._to_minutes(b.time_str)
            ranges.append((start, start + self._booking_minutes(b), b))
        return ranges

    def find_conflict(self, barber_id, date_str, time_str, duration_minutes,
                      all_barbers=False, ignore_booking_id=None):
        """Return the existing booking that overlaps the requested time, or None.
        Two appointments overlap if one starts before the other has finished."""
        new_start = self._to_minutes(time_str)
        new_end = new_start + int(duration_minutes)
        scope = None if all_barbers else barber_id
        for start, end, booking in self.get_booked_ranges(date_str, scope, ignore_booking_id):
            if new_start < end and start < new_end:
                return booking
        return None

    def delete_bookings_for_customer(self, customer_id):
        self.bookings = [b for b in self.bookings if b.customer_id != int(customer_id)]

    def delete_booking(self, booking_id):
        booking = self.get_booking_by_id(booking_id)
        if booking:
            self.bookings.remove(booking)
        return booking

    # ---------------- SEED DATA ----------------
    def _seed_data(self):
        # Default admin account
        self.add_user(Admin(self.next_user_id(), "Shop Owner", "admin", "admin123"))

        # A couple of barbers
        self.add_user(Barber(self.next_user_id(), "Barber one", "barber1", "barber123", "Fades & Classic Cuts"))
        self.add_user(Barber(self.next_user_id(), "Barber two", "barber2", "barber123", "Beard Grooming"))

        # A demo customer
        self.add_user(Customer(self.next_user_id(), "Client one", "client1", "client123", "0917-123-4567"))
        self.add_user(Customer(self.next_user_id(), "Client two", "client2", "client123", "0927-321-7654"))
            

        # Default services. Each service has its own photo (shown in the
        # booking page catalog) plus price, duration and description.
        self.add_service(Service(self.next_service_id(), "Classic Buzz Cut", 120, 20, "Short, low-maintenance clipper cut all over.", "buzzcut.jpg"))
        self.add_service(Service(self.next_service_id(), "Textured Quiff", 130, 25, "Short on the sides, slightly longer on top.", "texturedquiff.jpg"))
        self.add_service(Service(self.next_service_id(), "Skin Fade", 120, 35, "Precision fade with clean blend.", "skinfade.jpg"))
        self.add_service(Service(self.next_service_id(), "Edgar cut", 120, 30, "leveled bangs and crispier sides, styled back with tapered sides.", "edgarcut.jpg"))
        self.add_service(Service(self.next_service_id(), "Burst Fade", 130, 35, "Short shaved sides with longer hair on the back.", "burstfade.jpg"))
        self.add_service(Service(self.next_service_id(), "Modern Mullet", 115, 35, "Short on side more volume at the back.", "modernmullet.jpg"))
        self.add_service(Service(self.next_service_id(), "Slick Back", 130, 30, "Classic slicked-back style with a polished finish.", "slickback.jpg"))
        self.add_service(Service(self.next_service_id(), "Textured Crop", 120, 35, "Modern crop with a textured, choppy fringe.", "texturedcrop.jpg"))



# A single shared instance imported across the app (still just Python
# objects in memory — reset every time the server restarts).
store = DataStore()
