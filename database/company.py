from typing import Any


class Company:

    def __init__(self, id: str, created_time: str, fields: dict[str, Any]):
        self.id = id
        self.created_time = created_time
        self.name = fields["Name"] if "Name" in fields else None
        self.industry = fields["Industry"] if "Industry" in fields else None
        self.notes = fields["Notes"] if "Notes" in fields else None
        self.website = fields["Website"] if "Website" in fields else None
        self.instagram = fields["Instagram"] if "Instagram" in fields else None
        self.status = fields["Status"] if "Status" in fields else None
        self.fields = fields

    def __repr__(self):
        return f"{self.id} {self.created_time}: {self.name} {self.industry} {self.notes} {self.website} {self.instagram}"
