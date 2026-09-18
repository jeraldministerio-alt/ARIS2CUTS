# Fade & Blade — Barbershop Booking System

A multi-user Flask web app for managing a barbershop's bookings, built with
Object-Oriented Python. Storage is **in-memory (Python lists only)** — no
database — per the project requirements. Data resets whenever the server restarts.

## Features / Requirements Covered

- **3 User Roles**: Admin, Barber, Customer — each with their own dashboard and permissions.
- **Login & Role-Based Access**: Session-based auth; `role_required()` decorator guards routes.
- **CRUD Operations**:
  - Admin: Add / View / Update / Delete barbers, services, and bookings.
  - Barber: View assigned bookings, update booking status.
  - Customer: Create bookings, view own bookings, cancel bookings.
- **OOP concepts**:
  - *Inheritance*: `Admin`, `Barber`, `Customer` all inherit from `User`.
  - *Encapsulation*: password stored as a hashed, "private" attribute accessed only via `check_password()`/`set_password()`; the in-memory lists are wrapped by a `DataStore` class instead of being touched directly.
  - *Polymorphism*: `get_dashboard_url()`, `get_role_label()`, and `get_permissions()` are overridden per subclass and called generically (e.g. after login, `user.get_dashboard_url()` sends each role to the correct page without an if/else chain).
  - *Functions*: business logic (slot-conflict checking, status transitions, validation) lives in model/manager methods, not templates.
- **Temporary Storage**: everything lives in Python lists inside `data/store.py` (`DataStore`).
- **Flask Web App**: Blueprints for `auth`, `admin`, `barber`, `customer`; Jinja2 templates + plain CSS.
- **Validation & Error Handling**: required-field checks, price/duration type checks, duplicate-username checks, double-booking prevention, custom 404/500 pages, flash messages.

## Project Structure

```
barbershop/
├── app.py                     # App factory + entry point
├── requirements.txt
├── models/
│   ├── user.py                 # User, Admin, Barber, Customer
│   ├── service.py               # Service
│   └── booking.py               # Booking
├── data/
│   └── store.py                 # DataStore (Python-list "database" + seed data)
├── routes/
│   ├── auth_routes.py           # /login /register /logout
│   ├── admin_routes.py          # /admin/*
│   ├── barber_routes.py         # /barber/*
│   └── customer_routes.py       # /customer/*
├── utils/
│   └── decorators.py            # login_required, role_required
├── templates/
│   ├── base.html, login.html, register.html
│   ├── admin/ (dashboard, barbers, services, bookings)
│   ├── barber/ (dashboard)
│   ├── customer/ (dashboard, book)
│   └── errors/ (404, 500)
└── static/css/style.css
```

## Running Locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit **http://localhost:5000**

## Demo Accounts (seeded automatically)

| Role     | Username | Password  |
|----------|----------|-----------|
| Admin    | admin    | admin123  |
| Barber   | miguel   | barber123 |
| Barber   | carlo    | barber123 |
| Customer | juan     | cust123   |

New customers can also self-register from the login page.

## Deployment Notes

For online deployment (e.g. Render, Railway, PythonAnywhere):
1. Push this project to a GitHub repository.
2. Set the start command to: `gunicorn app:app` (add `gunicorn` to `requirements.txt`).
3. Because storage is in-memory, data resets on every redeploy/restart — this is expected given the "Python Lists only, no database" requirement.
4. Change `app.secret_key` in `app.py` to a real secret (e.g. via an environment variable) before going live.

## Notes on Design Decisions

- Passwords are hashed with `werkzeug.security` even though the project only requires basic validation — this keeps the "encapsulation" of `User._password_hash` meaningful and safe to demo publicly.
- Double-booking is prevented: a barber cannot be booked for the same date & time twice while a booking is active (not cancelled).
- Admin cannot directly edit/delete a Customer account in this version (only Admin/Barber management screens are provided) — this can be extended if needed.
