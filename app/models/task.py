"""Task model definition (previously missing)."""
import os
from app.models.database import db

# Schema configuration
REQUESTS_SCHEMA = os.getenv('POSTGRES_SCHEMA_CLIENTS')
BASE_SCHEMA = os.getenv('POSTGRES_SCHEMA')  # может быть None, тогда search_path

# If the configured database isn't PostgreSQL, avoid using schema-qualified
# table names because SQLite doesn't support schemas the same way.
_db_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URI') or ''
if not ('postgres' in _db_url or 'postgresql' in _db_url):
    REQUESTS_SCHEMA = None
    BASE_SCHEMA = None


class Task(db.Model):
	__tablename__ = 'tasks'
	__table_args__ = {'extend_existing': True, 'schema': REQUESTS_SCHEMA} if REQUESTS_SCHEMA else {'extend_existing': True}
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

