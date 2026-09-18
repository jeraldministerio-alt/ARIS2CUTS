"""
User models demonstrating OOP concepts:
- Encapsulation: password is stored as a "private" attribute and only
  reachable through controlled methods.
- Inheritance: Admin, Barber, Customer all inherit shared behaviour
  from the base User class.
- Polymorphism: each subclass overrides get_dashboard_url() and
  get_role_label() to return role-specific behaviour, and the app
  calls these methods without caring which subclass it actually has.
"""

from werkzeug.security import generate_password_hash, check_password_hash


class User:
    """Base class for every account in the system."""

    def __init__(self, user_id, full_name, username, password, role="user"):
        self.user_id = user_id
        self.full_name = full_name
        self.username = username
        self._password_hash = generate_password_hash(password)  # encapsulated
        self.role = role
        self.is_active = True

    # ---------- Encapsulation ----------
    def check_password(self, raw_password):
        """Controlled access to the private password hash."""
        return check_password_hash(self._password_hash, raw_password)

    def set_password(self, new_password):
        if not new_password or len(new_password) < 4:
            raise ValueError("Password must be at least 4 characters long.")
        self._password_hash = generate_password_hash(new_password)

    # ---------- Polymorphism (overridden in subclasses) ----------
    def get_dashboard_url(self):
        return "/login"

    def get_role_label(self):
        return "User"

    def get_permissions(self):
        return []

    # ---------- Shared behaviour ----------
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.username}>"


class Admin(User):
    """Manages barbers, services, and all bookings."""

    def __init__(self, user_id, full_name, username, password):
        super().__init__(user_id, full_name, username, password, role="admin")

    def get_dashboard_url(self):
        return "/admin/dashboard"

    def get_role_label(self):
        return "Administrator"

    def get_permissions(self):
        return ["manage_barbers", "manage_services", "manage_bookings", "view_reports"]


class Barber(User):
    """A staff member who fulfils bookings assigned to them."""

    def __init__(self, user_id, full_name, username, password, specialty="General"):
        super().__init__(user_id, full_name, username, password, role="barber")
        self.specialty = specialty

    def get_dashboard_url(self):
        return "/barber/dashboard"

    def get_role_label(self):
        return "Barber"

    def get_permissions(self):
        return ["view_own_bookings", "update_booking_status"]

    def to_dict(self):
        data = super().to_dict()
        data["specialty"] = self.specialty
        return data


class Customer(User):
    """A client who books appointments."""

    def __init__(self, user_id, full_name, username, password, phone=""):
        super().__init__(user_id, full_name, username, password, role="customer")
        self.phone = phone

    def get_dashboard_url(self):
        return "/customer/dashboard"

    def get_role_label(self):
        return "Customer"

    def get_permissions(self):
        return ["create_booking", "view_own_bookings", "cancel_own_booking"]

    def to_dict(self):
        data = super().to_dict()
        data["phone"] = self.phone
        return data
