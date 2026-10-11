ARIS2CUTS — Barbershop Booking System

A multi-user Flask web app for managing a barbershop's bookings, built with
Object-Oriented Python. Storage is **in-memory (Python lists only)** — no
database — per the project requirements. Data resets whenever the server restarts.

 Features / Requirements Covered

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

 Project Structure

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

 Running Locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit **http://localhost:5000**

 Demo Accounts (seeded automatically)

| Role     | Username | Password  |
|----------|----------|-----------|
| Admin    | admin    | admin123  |
| Barberone| barber1  | barber123 |
| Barbertwo| barber2  | barber123 |
| Client.  | client1  | client123 |

