import os
import uuid
import ezgmail
import asyncio
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, flash, send_from_directory,abort, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from models import Participant, Match, Setting, Admin, db
from werkzeug.security import generate_password_hash, check_password_hash

from telegram import Bot
from telegram.error import TelegramError


executor = ThreadPoolExecutor()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = 'static/uploads/profile_images'

# Replace with your actual Telegram bot token
TELEGRAM_BOT_TOKEN = '7478636127:AAH628CWYez8rfiJ1S26bqpLhvAvikPf3jw'

db.init_app(app)  # Initialize SQLAlchemy with the Flask app instance
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'signin'
login_manager.login_message_category = 'info'


# # Replace with your actual Gmail credentials
# GMAIL_EMAIL = 'your_email@gmail.com'
# GMAIL_PASSWORD = 'your_password'

async def send_async_email(recipient_email, subject, message_html):
    ezgmail.send(recipient_email, subject, message_html, mimeSubtype="html")


async def send_async_telegram(chat_id, message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    # try:
    await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
    # except TelegramError as e:
    #     app.logger.error(f'Telegram notification failed: {str(e)}')

@login_manager.user_loader
def load_user(user_id):
    # with app.app_context():
    return Participant.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Participant.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login Successful!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('signin.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('logout Successful!', 'success')
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        phone_number = request.form.get('phone')
        email = request.form.get('email')
        telegram_user_id = request.form.get('telegramId')
        password = request.form.get('password')
        dating_preference = ','.join(request.form.getlist('preferences'))
        bio = request.form.get('bio')
        user_entry_source = request.form.get('heardAboutUs')
        notifications = request.form.get('hearEvents') == 'Yes'

        # Handle profile image upload
        profile_image = request.files['profileImage']
        if profile_image and profile_image.filename != '':
            filename = secure_filename(profile_image.filename)
            file_ext = os.path.splitext(filename)[1]
            if file_ext.lower() in ['.jpg', '.jpeg', '.png']:
                unique_filename = str(uuid.uuid4()) + file_ext
                profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                profile_image_url = os.path.join('uploads/profile_images', unique_filename).replace('\\', '/')  # Updated profile image URL creation
            else:
                flash('Invalid image format. Only jpg, jpeg, and png are allowed.', 'danger')
                return redirect(request.url)
        else:
            profile_image_url = 'uploads/profile_images/default.jpg'  # Default image path

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = Participant(name=name, username=email.split('@')[0], phone_number=phone_number, email=email,
                               telegram_user_id=telegram_user_id, password=hashed_password, 
                               dating_preference=dating_preference, bio=bio, user_entry_source=user_entry_source,
                               notifications=notifications, profile_image_url=profile_image_url)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Registration Successful!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('signup.html')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.username = request.form.get('username')
        user.phone_number = request.form.get('phone_number')
        user.email = request.form.get('email')
        user.telegram_user_id = request.form.get('telegram_user_id')
        if request.form.get('password'):
            user.password = generate_password_hash(request.form.get('password'))
        user.dating_preference = request.form.get('dating_preference')
        user.bio = request.form.get('bio')
        user.user_entry_source = request.form.get('user_entry_source')
        user.notifications = bool(request.form.get('notifications'))
        db.session.commit()
        flash('Profile Updated!', 'success')
        return redirect(url_for('user_dashboard'))
    return render_template('edit_profile.html', user=user)

@app.route('/match_search')
@login_required
def match_search():
    # Implement search logic here
    return render_template('match_search.html')


@app.route('/search_participants', methods=['POST'])
@login_required
def search_participants():
    search_term = request.json.get('search_term', '')
    participants = Participant.query.filter(
        (Participant.name.contains(search_term)) |
        (Participant.username.contains(search_term)) |
        (Participant.email.contains(search_term)) |
        (Participant.telegram_user_id.contains(search_term))
    ).all()

    participants_data = []
    for participant in participants:
        participants_data.append({
            'id': participant.id,
            'name': participant.name,
            'profile_image_url': participant.profile_image_url,
            'bio': participant.bio,
            'is_matched': current_user.has_match_with(participant.id)
        })
    return jsonify(participants_data)

@app.route('/add_match/<int:match_id>', methods=['POST'])
@login_required
async def add_match(match_id):
    if current_user.id == match_id:
        return 'Cannot match with yourself', 400

    match_exists = Match.query.filter(
        (Match.user_id == current_user.id) & (Match.match_id == match_id)
    ).first()

    if match_exists:
        return 'Match already exists', 400

    match_user = Participant.query.get_or_404(match_id)

    new_match = Match(user_id=current_user.id, match_id=match_id)
    db.session.add(new_match)
    db.session.commit()

    # Send notifications
    participant = current_user
    match = match_user

    # Email notifications
    participant_email_subject = 'New Match Notification'
    participant_email_template = render_template('match_email_template.html',
                                                participant_name=participant.name,
                                                participant_email=participant.email,
                                                participant_phone=participant.phone_number,
                                                participant_telegram=participant.telegram_user_id,
                                                participant_image=participant.profile_image_url)
    await send_async_email(match.email, participant_email_subject, participant_email_template)

    match_email_subject = 'New Match Notification'
    match_email_template = render_template('match_email_template.html',
                                           participant_name=match.name,
                                           participant_email=match.email,
                                           participant_phone=match.phone_number,
                                           participant_telegram=match.telegram_user_id,
                                           participant_image=match.profile_image_url)
    await send_async_email(participant.email, match_email_subject, match_email_template)

    # Telegram notifications
    participant_telegram_message = f"You have been added as a match by {match.name}."
    await send_async_telegram(participant.telegram_user_id, participant_telegram_message)

    match_telegram_message = f"You have been matched with {participant.name}."
    await send_async_telegram(match.telegram_user_id, match_telegram_message)

    flash('Match added successfully.', 'success')
    return 'Match added successfully'

@app.route('/remove_match/<int:match_id>', methods=['POST'])
@login_required
def remove_match(match_id):
    match_to_remove = Match.query.filter(
        (Match.user_id == current_user.id) & (Match.match_id == match_id)
    ).first()

    if not match_to_remove:
        return 'Match not found', 404

    db.session.delete(match_to_remove)
    db.session.commit()
    return 'Match removed successfully'


@app.route('/view_profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = Participant.query.get_or_404(user_id)
    return render_template('view_profile.html', user=user)

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    matches = current_user.matched_users.all()
    return render_template('user_dashboard.html', current_user=current_user, matches=matches)


@app.route('/admin')
@login_required
def admin():
    if not current_user.admin:
        flash('You Probably Visited a wrong link!', 'danger')
        return redirect(url_for('home'))
    
    participants = Participant.query.all()
    total_users = len(participants)
    active_users = sum(1 for user in participants if user.is_active)
    reports_count = sum(1 for user in participants if user.has_reports)

    return render_template('admin_dashboard.html', participants=participants, total_users=total_users, active_users=active_users, reports_count=reports_count)


@app.route('/admin/create_participant', methods=['POST'])
@login_required
def create_participant():
    if not current_user.admin:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')
    telegram_user_id = request.form.get('telegram_user_id')
    date_joined = datetime.now()  # Or use a datepicker from the form

    participant = Participant(name=name, email=email, phone_number=phone_number, 
                              telegram_user_id=telegram_user_id)
    
    try:
        db.session.add(participant)
        db.session.commit()
        flash('Participant created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error creating participant: ' + str(e), 'danger')

    return redirect(url_for('admin'))


@app.route('/admin/edit_participant/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_participant(id):
    if not current_user.admin:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin'))
    
    participant = Participant.query.get_or_404(id)
    
    if request.method == 'POST':
        participant.name = request.form.get('name')
        participant.email = request.form.get('email')
        participant.phone_number = request.form.get('phone_number')
        participant.telegram_user_id = request.form.get('telegram_user_id')
        
        try:
            db.session.commit()
            flash('Participant updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating participant: ' + str(e), 'danger')
        
        return redirect(url_for('admin'))

    return render_template('edit_participant.html', participant=participant)


@app.route('/delete_participant/<int:id>', methods=['POST'])
def delete_participant(id):
    participant = Participant.query.get_or_404(id)

    try:
        # Delete related matches first
        Match.query.filter_by(user_id=id).delete()

        # Then delete the participant
        db.session.delete(participant)
        db.session.commit()

        flash('Participant deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting participant: ' + str(e), 'danger')
        abort(500)

    return redirect(url_for('admin'))

@app.route('/export_database')
@login_required
def export_database():
    if not current_user.admin:
        return redirect(url_for('home'))
    # Implement database export logic here
    return 'Database exported successfully'

# Static file serving
@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory("static", path)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0",port=30000)
