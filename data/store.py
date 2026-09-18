"""
Temporary in-memory storage.

Per the project requirements, NO DATABASE is used — everything lives in
plain Python lists for the lifetime of the running process. The manager
classes below wrap those lists and expose CRUD-style methods, which keeps
the raw lists encapsulated instead of being poked at directly from routes.
"""

from itertools import count
from models import Admin, Barber, Customer, Service, Booking, HaircutStyle


class DataStore:
    """Singleton-style container holding every list used by the app."""

    def __init__(self):
        self.users = []            # list[User]  (Admin / Barber / Customer)
        self.services = []         # list[Service]
        self.bookings = []         # list[Booking]
        self.haircut_styles = []   # list[HaircutStyle] (booking-page catalog)

        self._user_ids = count(1)
        self._service_ids = count(1)
        self._booking_ids = count(1)
        self._style_ids = count(1)

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

    def get_bookings_for_barber(self, barber_id):
        return [b for b in self.bookings if b.barber_id == int(barber_id)]

    def is_slot_taken(self, barber_id, date_str, time_str, ignore_booking_id=None):
        for b in self.bookings:
            if ignore_booking_id and b.booking_id == int(ignore_booking_id):
                continue
            if b.matches_slot(int(barber_id), date_str, time_str):
                return True
        return False

    def delete_booking(self, booking_id):
        booking = self.get_booking_by_id(booking_id)
        if booking:
            self.bookings.remove(booking)
        return booking

    # ---------------- HAIRCUT STYLE CATALOG ----------------
    def next_style_id(self):
        return next(self._style_ids)

    def add_haircut_style(self, style):
        self.haircut_styles.append(style)
        return style

    def get_all_haircut_styles(self):
        return self.haircut_styles

    # ---------------- SEED DATA ----------------
    def _seed_data(self):
        # Default admin account
        self.add_user(Admin(self.next_user_id(), "Shop Owner", "admin", "admin123"))

        # A couple of barbers
        self.add_user(Barber(self.next_user_id(), "Barber one", "barber1", "barber123", "Fades & Classic Cuts"))
        self.add_user(Barber(self.next_user_id(), "Barber two", "barber2", "barber123", "Beard Grooming"))

        # A demo customer
        self.add_user(Customer(self.next_user_id(), "Client one", "client1", "client123", "0917-123-4567"))

        # Default services — bookable versions of the 8 haircut styles in
        # the catalog below (same 8 styles, now selectable when booking).
        self.add_service(Service(self.next_service_id(), "Classic Buzz Cut", 120, 20, "Short, low-maintenance clipper cut all over."))
        self.add_service(Service(self.next_service_id(), "Textured Quiff", 140, 25, "Short on the sides, slightly longer on top."))
        self.add_service(Service(self.next_service_id(), "Skin Fade", 200, 45, "Precision fade with clean blend."))
        self.add_service(Service(self.next_service_id(), "Edgar cut", 220, 40, "leveled bangs and crispier sides, styled back with tapered sides."))
        self.add_service(Service(self.next_service_id(), "Burst Fade", 190, 35, "Short shaved sides with longer hair on the back."))
        self.add_service(Service(self.next_service_id(), "Modern Mullet", 200, 35, "Short on side more volume at the back."))
        self.add_service(Service(self.next_service_id(), "Slick Back", 180, 30, "Classic slicked-back style with a polished finish."))
        self.add_service(Service(self.next_service_id(), "Textured Crop", 190, 35, "Modern crop with a textured, choppy fringe."))

        # Haircut style catalog shown on the booking page (inspiration
        # gallery). Replace the .jpg files in static/images/haircuts/
        # with real photos using the same filenames to update these.
        style_names = [
            ("Classic Buzz Cut", "buzzcut.jpg"),
            ("Textured Quiff", "texturedquiff.jpg"),
            ("Skin Fade", "skinfade.jpg"),
            ("Edgar Cut", "edgarcut.jpg"),
            ("Burst Fade", "burstfade.jpg"),
            ("Modern Mullet", "modernmullet.jpg"),
            ("Slick Back", "slickback.jpg"),
            ("Textured Crop", "texturedcrop.jpg"),
        ]
        for name, filename in style_names:
            self.add_haircut_style(HaircutStyle(self.next_style_id(), name, filename))


# A single shared instance imported across the app (still just Python
# objects in memory — reset every time the server restarts).
store = DataStore()
