"""Task model definition (previously missing)."""
from app.models.database import db


class Task(db.Model):
	__tablename__ = 'tasks'
	id = db.Column(db.Integer, primary_key=True)
	client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
	title = db.Column(db.String(200), nullable=False)
	description = db.Column(db.Text, nullable=True)
	status = db.Column(db.String(20), nullable=True)
	priority = db.Column(db.String(20), nullable=True)
	due_date = db.Column(db.Date, nullable=True)
	created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
	updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

	def to_dict(self):
		return {
			'id': self.id,
			'client_id': self.client_id,
			'title': self.title,
			'description': self.description,
			'status': self.status,
			'priority': self.priority,
			'due_date': self.due_date.isoformat() if self.due_date else None,
			'created_at': self.created_at.isoformat() if self.created_at else None,
			'updated_at': self.updated_at.isoformat() if self.updated_at else None,
		}

