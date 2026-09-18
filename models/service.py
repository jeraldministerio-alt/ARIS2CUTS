"""Service offered by the barbershop (e.g. Haircut, Shave, Hair Color)."""


class Service:
    def __init__(self, service_id, name, price, duration_minutes, description=""):
        self.service_id = service_id
        self.name = name
        self.price = float(price)
        self.duration_minutes = int(duration_minutes)
        self.description = description
        self.is_active = True

    def update(self, name=None, price=None, duration_minutes=None, description=None):
        if name:
            self.name = name
        if price is not None:
            self.price = float(price)
        if duration_minutes is not None:
            self.duration_minutes = int(duration_minutes)
        if description is not None:
            self.description = description

    def to_dict(self):
        return {
            "service_id": self.service_id,
            "name": self.name,
            "price": self.price,
            "duration_minutes": self.duration_minutes,
            "description": self.description,
            "is_active": self.is_active,
        }

    def __repr__(self):
        return f"<Service {self.name} (${self.price})>"
