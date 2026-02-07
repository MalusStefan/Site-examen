from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

#User database
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(1000))
    event_date = db.Column(db.Date, nullable=False)  # Date only (YYYY-MM-DD)
    start_time = db.Column(db.Time, nullable=True)  # Optional time
    end_time = db.Column(db.Time, nullable=True)  # Optional time
    color = db.Column(db.String(20), default='#007bff')  # Event color
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Note relationship
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=True)
    note = db.relationship('Note', backref='calendar_events')



class RoadmapGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(1000))
    position = db.Column(db.Integer, default=0)  # For ordering
    deadline = db.Column(db.Date, nullable=True)  # Optional deadline
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')
    calendar_events = db.relationship('CalendarEvent', cascade="all, delete")
    roadmap_goals = db.relationship('RoadmapGoal', cascade="all, delete", order_by='RoadmapGoal.position')


