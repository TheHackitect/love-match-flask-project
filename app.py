import os
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, flash, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from models import Participant, Match, Setting, Admin, db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = 'static/uploads/profile_images'

db.init_app(app)  # Initialize SQLAlchemy with the Flask app instance
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'signin'
login_manager.login_message_category = 'info'


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
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('user_dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('signin.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
                flash('Invalid image format. Only jpg, jpeg, and png are allowed.')
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
            user.password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        user.dating_preference = request.form.get('dating_preference')
        user.bio = request.form.get('bio')
        user.user_entry_source = request.form.get('user_entry_source')
        user.notifications = bool(request.form.get('notifications'))
        db.session.commit()
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
    print(search_term)
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
    print(participants_data)
    return jsonify(participants_data)

@app.route('/add_match/<int:match_id>', methods=['POST'])
@login_required
def add_match(match_id):
    if current_user.id == match_id:
        return 'Cannot match with yourself', 400

    match_exists = Match.query.filter(
        (Match.user_id == current_user.id) & (Match.match_id == match_id)
    ).first()

    if match_exists:
        return 'Match already exists', 400

    new_match = Match(user_id=current_user.id, match_id=match_id)
    db.session.add(new_match)
    db.session.commit()
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
    return render_template('user_dashboard.html', current_user=current_user)

@app.route('/admin')
@login_required
def admin():
    if not current_user.admin:
        return redirect(url_for('home'))
    return render_template('admin.html')

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
    app.run(debug=True)
