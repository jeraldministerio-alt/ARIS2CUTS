"""Haircut style shown in the customer-facing catalog on the booking page.

This is a display/inspiration catalog (photo + name), separate from the
bookable Service list. Swap the placeholder .jpg files in
static/images/haircuts/ with real photos using the same filenames and
they will show up automatically — no code changes needed.
"""


class HaircutStyle:
    def __init__(self, style_id, name, image_filename):
        self.style_id = style_id
        self.name = name
        self.image_filename = image_filename

    def to_dict(self):
        return {
            "style_id": self.style_id,
            "name": self.name,
            "image_filename": self.image_filename,
        }

    def __repr__(self):
        return f"<HaircutStyle {self.name}>"
