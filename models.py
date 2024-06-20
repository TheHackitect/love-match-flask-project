from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()

class Participant(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    telegram_user_id = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    dating_preference = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    user_entry_source = db.Column(db.String(50), nullable=False)
    notifications = db.Column(db.Boolean, nullable=False, default=False)
    profile_image_url = db.Column(db.String(200), nullable=True, default='default.jpg')
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)    

    matches = db.relationship('Match', backref='participant', lazy=True)
    admin = db.relationship('Admin', backref='participant', uselist=False)

    # Flask-Login attributes and methods
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"Participant('{self.username}', '{self.email}', '{self.dating_preference}')"

    def has_match_with(self, match_id):
        return Match.query.filter(
            (Match.user_id == self.id) & (Match.match_id == match_id)
        ).first() is not None

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    match_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Match('{self.user_id}', '{self.match_id}')"

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_welcome_message = db.Column(db.String(500), nullable=False)
    site_title = db.Column(db.String(100), nullable=False)
    site_description = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"Setting('{self.site_title}', '{self.site_description}')"

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    admin_level = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Admin('{self.participant_id}', '{self.admin_level}')"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
