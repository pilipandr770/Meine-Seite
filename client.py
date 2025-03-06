from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    message = db.Column(db.Text, nullable=True)

    def __init__(self, name, email, message):
        self.name = name
        self.email = email
        self.message = message

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "message": self.message}
