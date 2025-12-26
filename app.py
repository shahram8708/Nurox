from flask import Flask, render_template, redirect, url_for, request, flash, session, send_from_directory, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import random
from datetime import datetime
import secrets 
import re
import os
import bcrypt
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask_mail import Mail, Message
from flask_session import Session
from datetime import timedelta
import google.generativeai as genai

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = db
app.config['SESSION_PERMANENT'] = True 
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365) 

Session(app)
app.config['SECRET_KEY'] = secrets.token_hex(16) 
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = ''  
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = ''  
from flask_migrate import Migrate
migrate = Migrate(app, db)

mail = Mail(app)

@app.route('/our_team')
def our_team():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = []  
        
    return render_template('our_team.html', unread_count=unread_count, notifications=notifications)

@app.route('/contact', methods=['GET'])
def contact():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 

    return render_template('contact.html', unread_count=unread_count, notifications=notifications)

@app.route('/terms_conditions')
def terms_conditions():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = []  

    return render_template('terms_conditions.html', unread_count=unread_count, notifications=notifications)

@app.route('/privacy_policy')
def privacy_policy():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:                   
        unread_count = 0
        notifications = []  
    
    return render_template('privacy_policy.html', unread_count=unread_count, notifications=notifications)

@app.route('/chatbot')
@login_required
def chatbot():
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('chatbot.html', unread_count=unread_count, notifications=notifications)

@app.route('/send_message', methods=['POST'])
def send_message():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    message = request.form['message']

    msg = Message(
        subject='Nurox Contact Form Submission',
        sender='factorysoch@gmail.com',
        recipients=['factorysoch@gmail.com']
    )
    msg.body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"

    try:
        mail.send(msg)
        flash('Your message has been sent!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('contact'))

user_followers = db.Table('user_followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_number = db.Column(db.String(100), nullable=False)
    subscription_type = db.Column(db.String(50), nullable=False)
    subscription_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref='subscriptions', lazy=True)

class ProfileView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    viewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_sent = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', foreign_keys=[user_id])
    viewer = db.relationship('User', foreign_keys=[viewer_id])

@app.route('/user_profile/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    groups = Group.query.filter_by(created_by=user.id).all()
    users = User.query.all() 

    if current_user.id != user_id:
        existing_view = ProfileView.query.filter(
            ProfileView.user_id == user_id,
            ProfileView.viewer_id == current_user.id,
            db.func.date(ProfileView.viewed_at) == datetime.utcnow().date()
        ).first()

        if not existing_view or not existing_view.email_sent:
            send_profile_view_notification(
                to_email=user.email,
                viewer_username=current_user.username,
                viewer_user_id=current_user.id
            )

            profile_view = ProfileView(
                user_id=user_id,
                viewer_id=current_user.id,
                email_sent=True
            )
            db.session.add(profile_view)

            notification = Notification(
                user_id=user_id,
                sender_id=current_user.id,
                notification_type="profile_view",
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()
        else:
            existing_view.viewed_at = datetime.utcnow()
            db.session.commit()

    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    stories = Story.query.filter_by(user_id=user.id).order_by(Story.created_at.desc()).all()

    problems_uploaded = Problem.query.filter_by(user_id=user.id).all()
    return render_template('user_profile.html', user=user, unread_count=unread_count, notifications=notifications, groups=groups, users=users, problems_uploaded=problems_uploaded, stories=stories)

def send_profile_view_notification(to_email, viewer_username, viewer_user_id):
    viewer_profile_link = url_for('user_profile', user_id=viewer_user_id, _external=True)
    chat_link = url_for('chat', user_id=viewer_user_id, _external=True) 

    msg = Message(
        subject="Someone viewed your profile on Nurox!",
        recipients=[to_email],
        body=(f"Hello,\n\n"
              f"{viewer_username} just visited your profile on Nurox! 🎉\n\n"
              f"Check out their profile here: {viewer_profile_link}\n"
              f"Start a chat here: {chat_link}\n\n"
              "Don't miss out on connecting with them!\n\n"
              "Thank you for being a part of Nurox.\n\n"
              "Best Regards,\n"
              "The Nurox Team 🛠️")
    )
    mail.send(msg)

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    if current_user.is_authenticated:
        user = current_user  
        groups = Group.query.filter_by(created_by=user.id).all()
        groupss = Group.query.join(GroupMembership).filter(
            GroupMembership.user_id == current_user.id 
        ).filter(
            GroupMembership.is_admin == False  
        ).all()
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
        users = User.query.all() 
        stories = Story.query.filter_by(user_id=current_user.id).order_by(Story.created_at.desc()).all()
        problems_uploaded = Problem.query.filter_by(user_id=user.id).all()
        return render_template('profile.html', user=user, unread_count=unread_count, notifications=notifications, groups=groups, users=users, groupss=groupss, problems_uploaded=problems_uploaded, stories=stories)
    else:
        flash('Please log in to access your profile.')
        return redirect(url_for('login'))

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    subscription_type = request.form['subscription_type']
    transaction_number = request.form['transaction_number']

    expiry_date = calculate_expiry(subscription_type)

    subscription = Subscription(
        user_id=current_user.id,
        transaction_number=transaction_number,
        subscription_type=subscription_type,
        subscription_date=datetime.utcnow(),
        expiry_date=expiry_date
    )
    db.session.add(subscription)
    db.session.commit()

    admin_email = 'factorysoch@gmail.com' 
    msg = Message('New Subscription Alert',
                  recipients=[admin_email])
    msg.body = f"""
A new subscription has been created:

User Details:
- User ID: {current_user.id}
- Name: {current_user.username}
- Email: {current_user.email}

Subscription Details:
- Subscription Type: {subscription_type}
- Transaction Number: {transaction_number}
- Expiry Date: {expiry_date if expiry_date else 'Lifetime'}

Best regards,
The Nurox Team 🛠️
    """
    mail.send(msg)

    current_user.subscription_status = "Pending Confirmation"
    current_user.subscription_type = subscription_type
    current_user.subscription_expiry = expiry_date if expiry_date else None
    db.session.commit()

    return redirect(url_for('subscription_status'))

from datetime import datetime, timedelta

def calculate_expiry(subscription_type):
    if subscription_type == '1 Month':
        return datetime.utcnow() + timedelta(days=30)
    elif subscription_type == '3 Months':
        return datetime.utcnow() + timedelta(days=90)
    elif subscription_type == '6 Months':
        return datetime.utcnow() + timedelta(days=180)
    elif subscription_type == '1 Year':
        return datetime.utcnow() + timedelta(days=365)
    elif subscription_type == 'Lifetime':
        return datetime.utcnow() + timedelta(days=365 * 100)
    return None 

@app.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    if current_user.subscription_status in ['Active', 'Pending Confirmation', 'Expired']:
        return redirect(url_for('subscription_status'))
    
    if request.method == 'POST':
        subscription_type = request.form.get('subscription_type')
        transaction_number = request.form.get('transaction_number')

        if subscription_type == '1 Month':
            expiry_date = datetime.utcnow() + timedelta(days=30)
        elif subscription_type == '3 Months':
            expiry_date = datetime.utcnow() + timedelta(days=90)
        elif subscription_type == '6 Months':
            expiry_date = datetime.utcnow() + timedelta(days=180)
        elif subscription_type == '1 Year':
            expiry_date = datetime.utcnow() + timedelta(days=365)
        elif subscription_type == 'Lifetime':
            expiry_date = None 

        subscription = Subscription(
            user_id=current_user.id,
            transaction_number=transaction_number,
            subscription_type=subscription_type,
            expiry_date=expiry_date
        )
        db.session.add(subscription)
        db.session.commit()

        current_user.subscription_status = "Pending Confirmation"
        current_user.subscription_type = subscription_type
        db.session.commit()

        return redirect(url_for('subscription_status'))  
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('subscription.html', unread_count=unread_count, notifications=notifications) 

@app.route('/admin/subscriptions')
def admin_subscriptions():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    subscriptions = Subscription.query.join(User).filter(User.subscription_status.in_(['Pending Confirmation', 'Active'])).all()

    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template('admin_dashboard.html', 
                           subscriptions=subscriptions, 
                           unread_count=unread_count, 
                           notifications=notifications)

@app.route('/admin/approve_subscription/<int:subscription_id>', methods=['POST'])
def approve_subscription(subscription_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    subscription = Subscription.query.get(subscription_id)
    user = subscription.user

    subscription.status = 'Approved'
    user.subscription_status = 'Active'
    user.subscription_expiry = subscription.expiry_date
    db.session.commit()

    msg = Message('Your Subscription is Approved',
                  recipients=[user.email])
    msg.body = f"""
Congratulations, your subscription has been approved!

Subscription Details:
- Subscription Type: {subscription.subscription_type}
- Transaction Number: {subscription.transaction_number}
- Expiry Date: {subscription.expiry_date if subscription.expiry_date else 'Lifetime'}

Thank you for subscribing!

Best regards,
The Nurox Team 🛠️
    """
    mail.send(msg)

    return redirect(url_for('admin_dashboard'))

@app.route('/subscription/status')
@login_required
def subscription_status():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('subscription_status.html', user=current_user, unread_count=unread_count, notifications=notifications)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    active_session = db.Column(db.String(150), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    branch = db.Column(db.String(50), nullable=True)
    college = db.Column(db.String(150), nullable=False, default="")
    bio = db.Column(db.Text, nullable=True)
    points = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    groups = db.relationship('GroupMembership', backref='user', lazy=True)
    group_messages = db.relationship('GroupMessage', backref='user', lazy=True)
    subscription_status = db.Column(db.String(50), nullable=True)
    subscription_type = db.Column(db.String(50), nullable=True)
    subscription_expiry = db.Column(db.DateTime, nullable=True)
    sectors = db.Column(db.String(500), nullable=True)
    user_type = db.Column(db.String(50), nullable=False)
    selected_sectors = db.Column(db.String(500), nullable=True)
    def get_enrollment_number(self):
        return self.email 
    
    followed = db.relationship(
        'User', secondary=user_followers,
        primaryjoin=(user_followers.c.follower_id == id),
        secondaryjoin=(user_followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(user_followers.c.followed_id == user.id).count() > 0
    
    def follower_count(self):
        return self.followers.count()

    def followed_count(self):
        return self.followed.count()

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(150), nullable=True)
    is_public = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('GroupMembership', backref='group', lazy=True)
    group_messages = db.relationship('GroupMessage', backref='group', lazy=True)

class GroupMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/promote_to_admin/<int:group_id>/<int:user_id>', methods=['POST'])
@login_required
def promote_to_admin(group_id, user_id):
    group = Group.query.get_or_404(group_id)

    if group.created_by != current_user.id:
        flash("Only the group admin can promote members.", "danger")
        return redirect(url_for('group_list'))

    membership = GroupMembership.query.filter_by(group_id=group_id, user_id=user_id).first()
    
    if membership and not membership.is_admin:
        membership.is_admin = True
        db.session.commit()

        admin_notification = Notification(
            user_id=membership.user.id,
            sender_id=current_user.id,
            notification_type='admin_promotion',
            msg=f'You have been promoted to admin in the group {group.name}.',
            is_read=False
        )
        db.session.add(admin_notification)

        group_list_url = url_for('group_list', _external=True)
        msg = Message(
            subject="Admin Promotion Notification",
            recipients=[membership.user.email],
            body=f"Dear {membership.user.username},\n\n"
                 f"You have been promoted to admin in the group '{group.name}'.\n\n"
                 f"Click here to view your groups: {group_list_url}\n\n"
                 "Best regards,\nThe Nurox Team 🛠️"
        )
        mail.send(msg)

        db.session.commit()

        flash(f'{membership.user.username} has been promoted to admin.', 'success')
    else:
        flash('User is already an admin or not found in the group.', 'danger')
    
    return redirect(url_for('group_chat', group_id=group.id))

@app.route('/demote_from_admin/<int:group_id>/<int:user_id>', methods=['POST'])
@login_required
def demote_from_admin(group_id, user_id):
    group = Group.query.get_or_404(group_id)

    if group.created_by != current_user.id:
        flash("Only the group admin can demote members.", "danger")
        return redirect(url_for('group_list'))

    membership = GroupMembership.query.filter_by(group_id=group_id, user_id=user_id).first()
    
    if membership and membership.is_admin:
        membership.is_admin = False
        db.session.commit()

        admin_notification = Notification(
            user_id=membership.user.id,
            sender_id=current_user.id,
            notification_type='admin_demotion',
            msg=f'You have been demoted from admin in the group {group.name}.',
            is_read=False
        )
        db.session.add(admin_notification)

        group_list_url = url_for('group_list', _external=True)
        msg = Message(
            subject="Admin Demotion Notification",
            recipients=[membership.user.email],
            body=f"Dear {membership.user.username},\n\n"
                 f"You have been demoted from admin in the group '{group.name}'.\n\n"
                 f"Click here to view your groups: {group_list_url}\n\n"
                 "Best regards,\nThe Nurox Team 🛠️"
        )
        mail.send(msg)

        db.session.commit()

        flash(f'{membership.user.username} has been demoted from admin.', 'success')
    else:
        flash('User is not an admin or not found in the group.', 'danger')
    
    return redirect(url_for('group_chat', group_id=group.id))

@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_public = request.form.get('is_public') == 'public'
        
        new_group = Group(name=name, description=description, is_public=is_public, created_by=current_user.id)
        db.session.add(new_group)
        db.session.commit()
        flash('Group created successfully', 'success')
        return redirect(url_for('group_list'))
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('create_group.html', unread_count=unread_count, notifications=notifications)

@app.route('/groups')
@login_required
def group_list():
    groups = Group.query.all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    users = User.query.all() 
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('group_list.html', groups=groups, users=users, unread_count=unread_count, notifications=notifications)

class DeletedMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('group_message.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/delete_chats/<int:group_id>', methods=['POST'])
@login_required
def delete_chats(group_id):

    group = Group.query.get_or_404(group_id)

    membership = GroupMembership.query.filter_by(group_id=group.id, user_id=current_user.id).first()

    if not membership or not membership.is_admin:

        if group.created_by != current_user.id:
            flash("Only the group admin can delete messages.", "danger")
            return redirect(url_for('group_list'))

    messages = GroupMessage.query.filter_by(group_id=group_id).all()

    if not messages:
        flash("No chat messages found for this group.", "info")
        return redirect(url_for('group_list'))

    deleted_count = 0

    for message in messages:

        db.session.delete(message)

        deleted_message = DeletedMessage(user_id=current_user.id, message_id=message.id)
        db.session.add(deleted_message)
        
        deleted_count += 1

    db.session.commit()

    if deleted_count > 0:
        flash(f"{deleted_count} chat message(s) have been deleted on this device.", "success")
    else:
        flash("No chat messages to delete.", "info")

    return redirect(url_for('group_list'))

@app.route('/delete_group/<int:group_id>', methods=['POST'])
@login_required
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)

    if group.created_by != current_user.id:
        flash("Only the group admin can delete the group.", "danger")
        return redirect(url_for('group_list'))

    GroupMembership.query.filter_by(group_id=group_id).delete()

    GroupMessage.query.filter_by(group_id=group_id).delete()

    db.session.delete(group)
    db.session.commit()
    
    flash("Group and all its messages and members have been deleted.", "success")
    return redirect(url_for('group_list'))

@app.route('/edit_group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = Group.query.get_or_404(group_id)
    if group.created_by != current_user.id:
        flash("Only the group admin can edit this group.", "danger")
        return redirect(url_for('group_list'))
    
    if request.method == 'POST':
        group.name = request.form.get('name')
        group.description = request.form.get('description')
        group.is_public = request.form.get('is_public') == 'on'
        db.session.commit()
        flash("Group details updated successfully.", "success")
        return redirect(url_for('group_list'))
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('edit_group.html', group=group, unread_count=unread_count, notifications=notifications)

@app.route('/join_group/<int:group_id>', methods=['POST'])
@login_required
def join_group(group_id):
    group = Group.query.get_or_404(group_id)

    existing_membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group.id).first()
    
    if not existing_membership:

        membership = GroupMembership(user_id=current_user.id, group_id=group.id, is_approved=group.is_public)
        db.session.add(membership)
        db.session.commit()

        group_list_url = url_for('group_list', _external=True)

        if group.is_public:

            admin_notification = Notification(
                user_id=group.created_by,
                sender_id=current_user.id,
                notification_type='join_request',
                msg=f'User {current_user.username} has joined your public group {group.name}.',
                is_read=False
            )
            db.session.add(admin_notification)
            db.session.commit()

            admin_email = User.query.get(group.created_by).email
            msg = Message(
                subject="User Joined Your Group",
                recipients=[admin_email],
                body=f"Dear Group Admin,\n\n"
                     f"User {current_user.username} has joined your public group '{group.name}'.\n\n"
                     f"View all your groups here: {group_list_url}\n\n"
                     "Best regards,\nThe Nurox Team 🛠️"
            )
            mail.send(msg)

            flash('Joined group successfully. The admin has been notified.', 'success')
        else:

            admin_notification = Notification(
                user_id=group.created_by,
                sender_id=current_user.id,
                notification_type='join_request',
                msg=f'User {current_user.username} has requested to join your private group {group.name}.',
                is_read=False
            )
            db.session.add(admin_notification)
            db.session.commit()

            admin_email = User.query.get(group.created_by).email
            msg = Message(
                subject="Join Request Notification",
                recipients=[admin_email],
                body=f"Dear Group Admin,\n\n"
                     f"User {current_user.username} has requested to join your private group '{group.name}'.\n\n"
                     f"View all your groups here: {group_list_url}\n\n"
                     "Best regards,\nThe Nurox Team 🛠️"
            )
            mail.send(msg)

            flash('Join request sent', 'info')
    else:
        flash('Already requested to join or are a member of this group.', 'warning')

    return redirect(url_for('group_list'))

@app.route('/leave_group/<int:group_id>', methods=['POST'])
@login_required
def leave_group(group_id):
    group = Group.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group.id, is_approved=True).first()
    
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash('Left group successfully', 'info')
    else:
        flash('Not a member of the group.', 'warning')
    
    return redirect(url_for('group_list'))

@app.route('/approve_member/<int:membership_id>', methods=['POST'])
@login_required
def approve_member(membership_id):
    membership = GroupMembership.query.get_or_404(membership_id)
    group = Group.query.get(membership.group_id)

    if group.created_by != current_user.id:
        flash('Only the group admin can approve members', 'danger')
    else:
        membership.is_approved = True
        db.session.commit()

        user_notification = Notification(
            user_id=membership.user_id,
            sender_id=current_user.id,
            notification_type='approval',
            msg=f'Your request to join the group {group.name} has been approved.',
            is_read=False
        )
        db.session.add(user_notification)
        db.session.commit()

        user = User.query.get(membership.user_id)

        if user:
            group_list_url = url_for('group_list', _external=True)

            msg = Message(
                subject=f"Your request to join {group.name} has been approved",
                recipients=[user.email],
                body=f"Dear {user.username},\n\n"
                     f"Your request to join the group '{group.name}' has been approved by the group admin.\n\n"
                     f"You can view your groups here: {group_list_url}\n\n"
                    "Best regards,\nThe Nurox Team 🛠️"
        )
        mail.send(msg)

        flash('Member approved successfully', 'success')
    
    return redirect(url_for('group_chat', group_id=group.id))

@app.route('/reject_member/<int:membership_id>', methods=['POST'])
@login_required
def reject_member(membership_id):
    membership = GroupMembership.query.get_or_404(membership_id)
    group = membership.group
    
    if group.created_by != current_user.id:
        flash('Only the group admin can reject members', 'danger')
        return redirect(url_for('group_chat', group_id=group.id))
    else:
        db.session.delete(membership)
        db.session.commit()

        user_notification = Notification(
            user_id=membership.user_id,
            sender_id=current_user.id,
            notification_type='rejection',
            msg=f'Your request to join the group {group.name} has been rejected.',
            is_read=False
        )
        db.session.add(user_notification)
        db.session.commit()

        user = User.query.get(membership.user_id)

        if user:
            group_list_url = url_for('group_list', _external=True)

            msg = Message(
                subject=f"Your request to join {group.name} has been rejected",
                recipients=[user.email],
                body=f"Dear {user.username},\n\n"
                     f"Unfortunately, your request to join the group '{group.name}' has been rejected by the group admin.\n\n"
                     f"You can view all your groups here: {group_list_url}\n\n"
                     "Best regards,\nThe Nurox Team 🛠️"
        )
        mail.send(msg)

        flash('Member rejected and removed from the pending list', 'danger')

    return redirect(url_for('group_chat', group_id=group.id))

from sqlalchemy.orm import joinedload

@app.route('/remove_member/<int:group_id>/<int:user_id>', methods=['POST'])
@login_required
def remove_member(group_id, user_id):
    group = Group.query.get_or_404(group_id)

    if group.created_by != current_user.id:
        flash('You are not authorized to remove members from this group.', 'danger')
        return redirect(url_for('group_list'))

    membership = GroupMembership.query.options(joinedload(GroupMembership.user)).filter_by(group_id=group_id, user_id=user_id).first()
    
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash(f'User {membership.user.username} has been removed from the group.', 'success')
    else:
        flash('User not found in this group.', 'danger')
    
    return redirect(url_for('group_chat', group_id=group_id))

@app.route('/group/<int:group_id>')
@login_required
def group_chat(group_id):
    group = Group.query.get_or_404(group_id)

    if group.created_by == current_user.id:

        group_messages = GroupMessage.query.filter_by(group_id=group.id).order_by(GroupMessage.timestamp).all()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return render_template('group_chat.html', group=group, group_messages=group_messages, unread_count=unread_count, notifications=notifications)

    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group.id).first()
    if not membership:
        flash('You are not a member of this group.', 'danger')
        return redirect(url_for('group_list'))
    
    if not membership.is_approved:
        flash('Access Denied. Please wait for approval.', 'danger')
        return redirect(url_for('group_list'))

    group_messages = GroupMessage.query.filter_by(group_id=group.id).order_by(GroupMessage.timestamp).all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template('group_chat.html', group=group, group_messages=group_messages, unread_count=unread_count, notifications=notifications)

@app.route('/send/<int:group_id>', methods=['POST'])
@login_required
def send(group_id):

    content = request.form.get('content')
    
    if not content:
        flash("Message cannot be empty!", "warning")
        return redirect(url_for('group_chat', group_id=group_id))

    new_group_message = GroupMessage(user_id=current_user.id, group_id=group_id, content=content)
    db.session.add(new_group_message)
    db.session.commit()

    group_members = GroupMembership.query.filter_by(group_id=group_id).all()

    group = Group.query.get_or_404(group_id)
    admin_id = group.created_by

    for membership in group_members:
        if membership.user_id != current_user.id:

            notification_msg = f"New message in group '{new_group_message.group.name}' from {current_user.username}: {new_group_message.content}"

            notification = Notification(
                user_id=membership.user_id,
                sender_id=current_user.id,
                notification_type="group_message",
                msg=notification_msg,
                is_read=False
            )
            db.session.add(notification)

    if admin_id != current_user.id and admin_id not in [member.user_id for member in group_members]:
        admin_notification = Notification(
            user_id=admin_id,
            sender_id=current_user.id,
            notification_type="group_message",
            msg=f"New message in group '{new_group_message.group.name}' from {current_user.username}: {new_group_message.content}",
            is_read=False
        )
        db.session.add(admin_notification)

    db.session.commit()

    return redirect(url_for('group_chat', group_id=group_id))

@app.route('/group_chat_updates/<int:group_id>', methods=['GET'])
@login_required
def group_chat_updates(group_id):
    last_message_id = int(request.args.get('last_message_id', 0))
    new_messages = GroupMessage.query.filter(GroupMessage.group_id == group_id, GroupMessage.id > last_message_id).order_by(GroupMessage.timestamp).all()
    return jsonify([
        {
            'id': message.id,
            'user_id': message.user.id,
            'username': message.user.username,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        for message in new_messages
    ])

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        college = request.form.get('college')
        branch = request.form.get('branch')
        bio = request.form.get('bio')
        sectors = request.form.getlist('sectors')
        
        is_admin = request.form.get('is_admin') == 'yes'
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('This username is already taken. Please choose a different one.', 'danger')
            return redirect(request.url)
        current_user.username = username
        current_user.college = college
        current_user.branch = branch
        current_user.bio = bio
        current_user.is_admin = is_admin
        current_user.sectors = ', '.join(sectors)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', user_id=current_user.id))

    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('edit_profile.html', user=current_user, unread_count=unread_count, notifications=notifications)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from sqlalchemy import func

class UserSectorView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sector_name = db.Column(db.String(150), nullable=False)
    user = db.relationship('User', backref='sector_views')

@app.route('/')
@login_required
def home():
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    sectors_list = [
        "Agriculture, Forestry & Fishing", "Mining & Quarrying", "Oil & Gas Exploration", 
        "Renewable Energy", "Water Resource Management", "Food & Beverage Processing", 
        "Textile & Apparel Manufacturing", "Automotive & Transportation Equipment", 
        "Electronics & Semiconductors", "Chemical Manufacturing", "Pharmaceutical Manufacturing", 
        "Construction & Building Materials", "Metalworking & Fabrication", "Plastics & Rubber Products", 
        "Aerospace & Defense Manufacturing", "Healthcare & Medical Services", "Education & E-learning", 
        "Tourism, Hospitality & Leisure", "Retail & Consumer Goods", "Financial Services", 
        "Logistics & Supply Chain Management", "Real Estate & Property Management", "Telecommunications & Networking", 
        "Media & Entertainment", "Sports & Recreation", "Information Technology & Software Development", 
        "Artificial Intelligence & Machine Learning", "Biotechnology & Life Sciences", "Research & Development", 
        "Data Science & Big Data Analytics", "Cybersecurity & Data Protection", "Cloud Computing & Infrastructure", 
        "Government & Public Administration", "Nonprofit & Charity Organizations", "Policy Research & Think Tanks", 
        "International Relations & Diplomacy", "Space Exploration & Aerospace Engineering", "Blockchain & Cryptocurrency", 
        "E-commerce & Digital Marketplaces", "Virtual Reality & Augmented Reality", "Robotics & Automation", 
        "Electric Vehicles & Sustainable Transportation", "Circular Economy & Recycling", 
        "Climate Change Mitigation & Adaptation", "Smart Cities & Internet of Things", 
        "Social Media & Influencer Marketing", "Ethical Fashion & Sustainable Textiles", 
        "Organic & Natural Products", "Arts, Crafts & Design", "Film, Television & Animation", 
        "Music Production & Distribution", "Writing, Publishing & Journalism", "Gaming & Esports", 
        "Legal Services & Advocacy", "Human Resources & Talent Management", "Event Planning & Management", 
        "Safety & Security Services", "Environmental Consulting & Conservation", 
        "Disaster Management & Emergency Services", "Agritech & Precision Farming"
    ]
    sector_problems = {}
    for sector in sectors_list:
        problems_in_sector = Problem.query.filter_by(sector=sector) \
        .order_by(func.random()) \
        .limit(3).all()
        if problems_in_sector:
            sector_problems[sector] = problems_in_sector
    random_stories = Story.query.order_by(func.random()).limit(3).all()
    user = current_user 
    viewed_sectors = db.session.query(UserSectorView.sector_name).filter_by(user_id=current_user.id).all()
    viewed_sectors = [sector[0] for sector in viewed_sectors]
    problems = Problem.query.filter(Problem.sector.in_(viewed_sectors)).order_by(func.random()).all()
    all_groups = Group.query.order_by(func.random()).limit(3).all()
    users = User.query.all() 
    groupss = Group.query.join(GroupMembership).filter(
            GroupMembership.user_id == current_user.id 
        ).filter(
            GroupMembership.is_admin == False  
        ).all()
    return render_template(
        'home.html', 
        unread_count=unread_count, 
        notifications=notifications, 
        sector_problems=sector_problems, user=user, random_stories=random_stories, problems=problems, groups=all_groups, users=users, groupss=groupss
    )

otp_storage = {}

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        sectors = request.form.getlist('sectors')
        selected_sectors = ', '.join(sectors)

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Please enter a valid email address.', 'danger')
            return redirect(request.url)

        existing_user_email = User.query.filter_by(email=email).first()
        if existing_user_email:
            flash('Email is already registered. Please use a different email.', 'danger')
            return redirect(request.url)

        existing_user_username = User.query.filter_by(username=username).first()
        if existing_user_username:
            flash('Username is already taken. Please choose a different username.', 'danger')
            return redirect(request.url)

        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(password_pattern, password):
            flash('Your password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, one digit, and one special character.', 'danger')
            return redirect(request.url)

        user_type = request.form.get('user_type')

        if user_type in ['entrepreneur_innovator', 'both']:
            selected_sectors = ', '.join(sectors)
        else:
            selected_sectors = None

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            user_type=user_type,
            sectors=selected_sectors,
            selected_sectors=selected_sectors
        )
        current_user.selected_sectors = selected_sectors
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    unread_count = 0
    notifications = []
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()

    return render_template('register.html', unread_count=unread_count, notifications=notifications)

@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.json['email']
    otp = random.randint(100000, 999999)
    otp_storage[email] = otp 
    print(f"Sending OTP {otp} to {email}") 

    msg = Message('Your OTP Code', recipients=[email])
    msg.body = f'Your OTP is {otp}. It is valid for the next 10 minutes.'
    mail.send(msg)

    return jsonify({"message": "OTP sent to your email."}), 200

@app.route('/validate_otp', methods=['POST'])
def validate_otp():
    email = request.json['email']
    otp = request.json['otp']

    if otp_storage.get(email) == int(otp):
        del otp_storage[email]  
        return jsonify({"message": "OTP validated successfully!"}), 200
    else:
        return jsonify({"message": "Invalid OTP."}), 400

@app.errorhandler(Exception)
def handle_error(error):
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = []

    app.logger.error(f"Error occurred: {error}")

    return render_template(
        'error.html', 
        unread_count=unread_count, 
        notifications=notifications
    ), 500 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user:
            if user.active_session and user.active_session != request.remote_addr:
                send_login_notification(user, request.remote_addr)
                flash('You are already logged in from another device. Please check your email for details.', 'danger')
                return redirect(request.url)

            try:
                if bcrypt.check_password_hash(user.password, password):
                    user.active_session = request.remote_addr 
                    db.session.commit()
                    login_user(user)
                    send_login_notification(user, request.remote_addr)
                    flash('Logged in successfully.', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('Login failed. Check email and password.', 'danger')
            except ValueError as e:
                flash("There was an issue with your password. Please try resetting your password.", "danger")
                print(f"Password hash error: {e}")
        else:
            flash('Login failed. Check email and password.', 'danger')

    unread_count = 0
    notifications = []
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()

    return render_template('login.html', unread_count=unread_count, notifications=notifications)

def send_login_notification(user, remote_addr):
    msg = Message(
        subject="New Login Notification on Nurox!",
        recipients=[user.email],
        body=(
            f"Hello {user.username},\n\n"
            f"You have logged in to your Nurox account from a new device.\n\n"
            f"IP Address: {remote_addr}\n\n"
            "If this was not you, please change your password immediately and contact support.\n\n"
            "Thank you for being a part of Nurox.\n\n"
            "Best Regards,\n"
            "The Nurox Team 🛠️"
        )
    )
    mail.send(msg)
    
    new_notification = Notification(
        user_id=user.id,
        sender_id=user.id,  
        notification_type="login_alert",
        is_read=False
    )
    db.session.add(new_notification)
    db.session.commit()

@app.route('/logout')
@login_required
def logout():
    current_user.active_session = None  
    db.session.commit()  
    logout_user()
    flash('You have been logged out.', 'info')
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = []

    return redirect(url_for('login', unread_count=unread_count, notifications=notifications))

@app.before_request
def check_active_session():
    if current_user.is_authenticated:
        if current_user.active_session and current_user.active_session != request.remote_addr:
            logout_user()  
            flash('You have been logged out due to login from another device.', 'warning')
            return redirect(url_for('login'))

app.config['UPLOAD_FOLDER'] = 'uploads/'  
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'mp3', 'mp4', 'avi', 'mkv', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

from random import randint

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if not bcrypt.check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(request.url)
        
        hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        current_user.password = hashed_new_password
        
        db.session.commit() 
        flash('Password changed successfully!', 'success')
        return redirect(url_for('profile', user_id=current_user.id)) 
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('change_password.html', unread_count=unread_count, notifications=notifications)

@app.errorhandler(404)
def page_not_found(e):
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 
    
    return render_template('404.html', unread_count=unread_count, notifications=notifications), 404

ADMIN_EMAIL = 'nurox@admin.com'
ADMIN_PASSWORD = 'nurox@6708'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')

    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 

    return render_template('admin_login.html', unread_count=unread_count, notifications=notifications)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    users = User.query.all()
    groups = Group.query.all() 
    problems = Problem.query.all()
    stories = Story.query.order_by(Story.created_at.desc()).all()
    pending_subscriptions = Subscription.query.all()

    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 

    return render_template('admin_dashboard.html', 
                           users=users,
                           groups=groups,
                           unread_count=unread_count, 
                           notifications=notifications, 
                           subscriptions=pending_subscriptions, 
                           stories=stories, 
                           problems=problems)

@app.route('/deletes_problem/<int:problem_id>', methods=['POST'])
def deletes_problem(problem_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    problem = Problem.query.get_or_404(problem_id)
    try:
        db.session.delete(problem)
        db.session.commit()
        flash('Problem deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting problem: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/deletes_story/<int:story_id>', methods=['POST'])
def deletes_story(story_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    story = Story.query.get_or_404(story_id)
    try:
        db.session.delete(story)
        db.session.commit()
        flash('Story deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting story: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/delete_groups/<int:group_id>', methods=['POST'])
def delete_groups(group_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    group = Group.query.get(group_id)
    
    if group:
        try:

            group_memberships = GroupMembership.query.filter_by(group_id=group.id).all()
            for membership in group_memberships:
                db.session.delete(membership)

            group_messages = GroupMessage.query.filter_by(group_id=group.id).all()
            for message in group_messages:
                db.session.delete(message)

            db.session.delete(group)
            db.session.commit()
            
            flash('Group deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    else:
        flash('Group not found.', 'danger')

    return redirect(url_for('admin_dashboard'))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Post {self.title}>'

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    title = request.form['title']
    description = request.form['description']

    new_post = Post(title=title, description=description)
    db.session.add(new_post)
    db.session.commit()
    flash('Post created successfully!', 'success')

    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 

    return redirect(url_for('admin_dashboard', unread_count=unread_count, notifications=notifications))

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'admin_logged_in' not in session:
        flash('You are not authorized to delete this post.', 'danger')
        return redirect(url_for('posts'))  

    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 
    return redirect(url_for('posts', unread_count=unread_count, notifications=notifications))

@app.route('/posts')
def posts():
    all_posts = Post.query.all()
    
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 
    
    return render_template('posts.html', posts=all_posts, unread_count=unread_count, notifications=notifications)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    try:

        user = User.query.get(user_id)
        if user:
            db.session.delete(user) 
            db.session.commit()  
            flash('User deleted successfully!', 'success')
        else:
            flash('User not found!', 'error')

    except Exception as e:
        db.session.rollback()  
        flash('Error occurred while deleting the user: {}'.format(e), 'error')
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return redirect(url_for('admin_dashboard', unread_count=unread_count, notifications=notifications))

@app.route('/faq')
def faq():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 

    return render_template('faq.html', unread_count=unread_count, notifications=notifications)

@app.route('/about')
def about():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 

    return render_template('about.html', unread_count=unread_count, notifications=notifications)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    message_id = db.Column(db.Integer, db.ForeignKey('chat_message.id'), nullable=True)  
    notification_type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    resource_id = db.Column(db.Integer, nullable=True)
    user = db.relationship('User', foreign_keys=[user_id])
    sender = db.relationship('User', foreign_keys=[sender_id])
    message = db.relationship('ChatMessage')
    msg = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/chat/<int:user_id>', methods=['GET'])
@login_required
def chat(user_id):
    other_user = User.query.get(user_id)
    if not current_user.is_following(other_user) or not other_user.is_following(current_user):
        flash('You can only chat with users who have followed you back.', 'warning')
        return redirect(url_for('user_profile', user_id=user_id))
    messages = ChatMessage.query.filter( 
        (ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == user_id) |
        (ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == current_user.id)
    ).order_by(ChatMessage.timestamp).all()

    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    timezone_offset = timedelta(hours=5, minutes=30)
    for message in messages:
        message.local_timestamp = message.timestamp + timezone_offset

    return render_template('chat.html', other_user=other_user, messages=messages, unread_count=unread_count, notifications=notifications)

@app.route('/chat_updates/<int:user_id>', methods=['GET'])
@login_required
def chat_updates(user_id):
    last_message_id = request.args.get('last_message_id', type=int, default=0)

    new_messages = ChatMessage.query.filter(
        (
            (ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == current_user.id) |
            (ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == user_id)
        ) & (ChatMessage.id > last_message_id)
    ).order_by(ChatMessage.timestamp).all()

    timezone_offset = timedelta(hours=5, minutes=30)
    messages_data = []
    for message in new_messages:
        messages_data.append({
            'id': message.id,
            'sender_id': message.sender_id,
            'sender_username': message.sender.username,
            'content': message.content,
            'timestamp': (message.timestamp + timezone_offset).strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify(messages_data)

@app.route('/send_email', methods=['POST'])
def send_email():
    subject = request.form['subject']
    message = request.form['message']
    
    users = User.query.all()

    for user in users:
        msg = Message(subject=subject,
                      sender='factorysoch@gmail.com',  
                      recipients=[user.email])
        msg.body = message
        try:
            mail.send(msg) 
        except Exception as e:
            flash(f"Failed to send email to {user.email}: {str(e)}", "danger")
            continue

    flash("Emails sent successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/send_message/<int:user_id>', methods=['POST'], endpoint='send_chat_message')
@login_required
def send_message(user_id):
    content = request.form['message']
    
    message = ChatMessage(sender_id=current_user.id, receiver_id=user_id, content=content)
    db.session.add(message)
    db.session.commit()

    last_notification = Notification.query.filter_by(user_id=user_id, sender_id=current_user.id, notification_type='chat_message').order_by(Notification.id.desc()).first()

    if not last_notification or last_notification.created_at < datetime.utcnow() - timedelta(hours=1):
        notification = Notification(
            user_id=user_id, 
            sender_id=current_user.id, 
            message_id=message.id,           
            notification_type='chat_message'
        )
        db.session.add(notification)
        db.session.commit()

        send_chat_notification(user_id, current_user.username, content)

    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return redirect(url_for('chat', user_id=user_id, unread_count=unread_count, notifications=notifications))

def send_chat_notification(receiver_user_id, sender_username, message_content):
    receiver = User.query.get(receiver_user_id)
    if receiver and receiver.email:
        chat_link = url_for('chat', user_id=current_user.id, _external=True)
        
        msg = Message(
            subject=f"You have a new message from {sender_username}!",
            recipients=[receiver.email],
            body=(
                f"Dear User,\n\n"
                f"You have received a new message from {sender_username} on Nurox! ✉️\n\n"
                f"Message Content: {message_content}\n\n"
                f"You can view and reply to the message by clicking here: {chat_link}\n\n"
                "Feel free to reply and connect!\n\n"
                "Thank you for being a part of our community.\n\n"
                "Best Regards,\n"
                "The Nurox Team 🛠️"
            )
        )
        mail.send(msg)

@app.route('/notifications', methods=['GET'])
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).all()

    for notification in user_notifications:
        notification.is_read = True

    db.session.commit()

    user_ids = set()
    messages = ChatMessage.query.filter( 
        (ChatMessage.sender_id == current_user.id) | (ChatMessage.receiver_id == current_user.id)
    ).all()

    for message in messages:
        if message.sender_id != current_user.id:
            user_ids.add(message.sender_id)
        else:
            user_ids.add(message.receiver_id)

    unique_users = User.query.filter(User.id.in_(user_ids)).all()

    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    notifications_list = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()

    return render_template('notifications.html', user_notifications=user_notifications, unique_users=unique_users, unread_count=unread_count, notifications=notifications_list)

@app.route('/delete_chat/<int:user_id>', methods=['POST'])
@login_required
def delete_chat(user_id):
    messages_to_delete = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == user_id)) |
        ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == current_user.id))
    ).all()

    for message in messages_to_delete:
        Notification.query.filter_by(message_id=message.id).delete()

        db.session.delete(message)

    db.session.commit()

    flash('Chat deleted successfully.', 'success')
    return redirect(url_for('notifications'))

@app.route('/delete_all_notifications', methods=['POST'])
@login_required
def delete_all_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).all()

    for notification in notifications:
        db.session.delete(notification)

    db.session.commit()

    flash('All notifications have been deleted.', 'success')

    return redirect(url_for('notifications'))

@app.route('/users')
@login_required 
def users_list():
    users = User.query.all()
    
    followed_users = []
    if current_user.is_authenticated:
        followed_users = current_user.followed.all()  
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('users_list.html', users=users, followed_users=followed_users, unread_count=unread_count, notifications=notifications)

from flask import redirect, url_for
from flask_login import current_user, login_required

@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    user_to_follow = User.query.get(user_id)
    if not user_to_follow:
        return jsonify({"error": "User not found."}), 404

    if current_user.is_following(user_to_follow):
        return jsonify({"message": "You are already following this user."}), 200

    current_user.follow(user_to_follow)

    try:
        notification = Notification(
            user_id=user_id,               
            sender_id=current_user.id,     
            message_id=None,                
            notification_type='follow',    
            is_read=False                   
        )
        db.session.add(notification)
        db.session.commit()

        send_follow_notification(user_to_follow.email, current_user.username, current_user.id)

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500  

    return redirect(url_for('user_profile', user_id=user_id))

def send_follow_notification(to_email, follower_username, follower_user_id):
    follower_profile_link = url_for('user_profile', user_id=follower_user_id, _external=True)
    msg = Message(
        subject=f"You have a new follower: {follower_username}!",
        recipients=[to_email],
        body=(
            f"Dear User,\n\n"
            f"We are excited to inform you that {follower_username} has started following you on Nurox! 🎉\n\n"
            f"You can view their profile here: {follower_profile_link}\n\n"
            "Feel free to connect and explore more!\n\n"
            "Thank you for being a part of our community.\n\n"
            "Best Regards,\n"
            "The Nurox Team 🛠️"
        )
    )
    mail.send(msg)

@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    user = User.query.get_or_404(user_id)
    if user is not current_user:
        current_user.unfollow(user)
        db.session.commit()
    return redirect(url_for('user_profile', user_id=user.id))

@app.route('/followers/<int:user_id>')
@login_required
def followers(user_id):
    user = User.query.get_or_404(user_id)
    followers = user.followers.all()  
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('followers_list.html', user=user, followers=followers, unread_count=unread_count, notifications=notifications)

@app.route('/following/<int:user_id>')
@login_required
def following(user_id):
    user = User.query.get_or_404(user_id)
    following = user.followed.all() 
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('following_list.html', user=user, following=following, unread_count=unread_count, notifications=notifications)

@app.route('/verify_account')
@login_required
def verify_account():
    if current_user.is_verified:
        flash('Your account is already verified!', 'info')
        return redirect(url_for('profile', user_id=current_user.id))
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('verify_account.html', user=current_user, otp_sent=False, unread_count=unread_count, notifications=notifications)

@app.route('/send_otps', methods=['POST'])
@login_required
def send_otps():
    email = request.form['email']
    otp = random.randint(100000, 999999) 
    session['otp'] = otp 
    
    msg = Message('Your OTP Code', sender='factorysoch@gmail.com', recipients=[email])
    msg.body = f'Your OTP code is {otp}. It is valid for 10 minutes.'
    mail.send(msg)
    
    flash('An OTP has been sent to your email.', 'info')
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('verify_account.html', user=current_user, otp_sent=True, unread_count=unread_count, notifications=notifications)

@app.route('/verify_otps', methods=['POST'])
@login_required
def verify_otps():
    otp_entered = request.form['otp']
    if 'otp' in session and str(session['otp']) == otp_entered:
        current_user.is_verified = True
        db.session.commit()

        session.pop('otp', None)

        flash('Your account has been successfully verified!', 'success')

        return redirect(url_for('profile', user_id=current_user.id)) 
    else:
        flash('Invalid OTP. Please try again.', 'danger')
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
        return render_template('verify_account.html', user=current_user, otp_sent=True, unread_count=unread_count, notifications=notifications)

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    otp_code = db.Column(db.String(6), nullable=False)
    expiration = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @staticmethod
    def generate_otp(user):
        otp_code = f"{random.randint(100000, 999999)}"
        expiration = datetime.utcnow() + timedelta(minutes=10)
        otp = OTP(otp_code=otp_code, expiration=expiration, user_id=user.id)
        db.session.add(otp)
        db.session.commit()
        return otp_code

@app.route('/forgot_password')
def forgot_password():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 
    return render_template('forgot_password.html', unread_count=unread_count, notifications=notifications)

@app.route('/sends_otp', methods=['POST'])
def sends_otp():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("No account found with that email. Please register first.")
        return redirect(url_for('forgot_password'))

    otp_code = OTP.generate_otp(user)
    msg = Message("Your OTP for Password Reset", recipients=[user.email])
    msg.body = f"Your OTP code is {otp_code}. It is valid for 10 minutes."
    mail.send(msg)

    flash("An OTP has been sent to your email.")
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 
    return render_template('forgot_password.html', email=email, show_otp_form=True, unread_count=unread_count, notifications=notifications)

@app.route('/verifys_otp', methods=['POST'])
def verifys_otp():
    email = request.form.get('email')
    entered_otp = request.form.get('otp')
    user = User.query.filter_by(email=email).first()

    otp_record = OTP.query.filter_by(user_id=user.id, otp_code=entered_otp, is_used=False).first()

    if not otp_record or otp_record.expiration < datetime.utcnow():
        flash("Invalid or expired OTP. Please try again.")
        return redirect(url_for('forgot_password'))

    otp_record.is_used = True
    db.session.commit()
    flash("OTP verified! Please enter your new password.")
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    else:
        unread_count = 0
        notifications = [] 
    return render_template('forgot_password.html', email=email, show_reset_form=True, unread_count=unread_count, notifications=notifications)

@app.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if new_password != confirm_password:
        flash("Passwords do not match. Please try again.")
        return render_template('forgot_password.html', email=email, show_reset_form=True)

    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', new_password):
        flash("Password must contain at least 8 characters, including uppercase, lowercase, number, and special character.")
        return render_template('forgot_password.html', email=email, show_reset_form=True)

    user = User.query.filter_by(email=email).first()
    
    if user is not None:
        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()

        send_password_reset_email(user.email)
        create_password_reset_notification(user)

        flash("Password reset successfully! You can now log in with your new password.")
    else:
        flash("User not found.")
        return redirect(url_for('forgot_password'))

    return redirect(url_for('login'))

def send_password_reset_email(email):
    msg = Message(
        subject="Password Reset Confirmation",
        recipients=[email],
        body=(
            "Hello,\n\n"
            "Your password has been successfully reset. You can now log in with your new password.\n\n"
            "If you did not request this change, please contact support immediately.\n\n"
            "Best Regards,\n"
            "The Nurox Team"
        )
    )
    mail.send(msg)

def create_password_reset_notification(user):
    if not isinstance(user, User):
        print("Error: 'user' is not a User instance")
        return

    try:
        notification = Notification(
            user_id=user.id,
            sender_id=user.id, 
            notification_type="password_reset",
            msg="Your password was successfully reset."
        )
        db.session.add(notification)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {e}")
   
@app.route('/submit_problem', methods=['GET', 'POST'])
@login_required
def submit_problem():
    if request.method == 'POST':
        sector = request.form['sector']
        title = request.form['problem_title']
        description = request.form['problem_description']
        genai.configure(api_key="")

        model = genai.GenerativeModel('gemini-1.5-flash')

        analysis_prompt = f"Analyze this title and problem and tell me whether this problem is legitimate. Can an entrepreneur start a startup based on this problem? Is this problem a real issue? If it is, has a solution been proposed already, or does a platform or product exist to address it? Is this a unique startup idea, and is it useful? Provide a comprehensive analysis in one paragraph covering all these points. Also, give an overall opinion: if a startup is built around this problem, will it be unique, feasible in the future, and valuable in the market?\nTitle: {title}\nDescription: {description}\n"

        response = model.generate_content(analysis_prompt)

        new_problem = Problem(
            sector=sector, 
            title=title, 
            description=description, 
            user_id=current_user.id,
            ai_analysis = response.text
        )
        db.session.add(new_problem)
        random_points = randint(1, 5)
        current_user.points += random_points 
        db.session.commit()

        flash(f'Problem uploaded successfully! You earned {random_points} points.', 'success')
        
        if current_user.points >= 100:
            flash('Congratulations! You have earned 100 points.', 'success')
        
        flash('Problem submitted successfully!', 'success')
        return redirect(url_for('problem_details', problem_id=new_problem.id))

    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('submit_problem.html', unread_count=unread_count, notifications=notifications)

@app.route('/problems')
@login_required
def problems():
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    user = current_user 
    sectors_list = [
        "Agriculture, Forestry & Fishing", "Mining & Quarrying", "Oil & Gas Exploration", 
        "Renewable Energy", "Water Resource Management", "Food & Beverage Processing", 
        "Textile & Apparel Manufacturing", "Automotive & Transportation Equipment", 
        "Electronics & Semiconductors", "Chemical Manufacturing", "Pharmaceutical Manufacturing", 
        "Construction & Building Materials", "Metalworking & Fabrication", "Plastics & Rubber Products", 
        "Aerospace & Defense Manufacturing", "Healthcare & Medical Services", "Education & E-learning", 
        "Tourism, Hospitality & Leisure", "Retail & Consumer Goods", "Financial Services", 
        "Logistics & Supply Chain Management", "Real Estate & Property Management", "Telecommunications & Networking", 
        "Media & Entertainment", "Sports & Recreation", "Information Technology & Software Development", 
        "Artificial Intelligence & Machine Learning", "Biotechnology & Life Sciences", "Research & Development", 
        "Data Science & Big Data Analytics", "Cybersecurity & Data Protection", "Cloud Computing & Infrastructure", 
        "Government & Public Administration", "Nonprofit & Charity Organizations", "Policy Research & Think Tanks", 
        "International Relations & Diplomacy", "Space Exploration & Aerospace Engineering", "Blockchain & Cryptocurrency", 
        "E-commerce & Digital Marketplaces", "Virtual Reality & Augmented Reality", "Robotics & Automation", 
        "Electric Vehicles & Sustainable Transportation", "Circular Economy & Recycling", 
        "Climate Change Mitigation & Adaptation", "Smart Cities & Internet of Things", 
        "Social Media & Influencer Marketing", "Ethical Fashion & Sustainable Textiles", 
        "Organic & Natural Products", "Arts, Crafts & Design", "Film, Television & Animation", 
        "Music Production & Distribution", "Writing, Publishing & Journalism", "Gaming & Esports", 
        "Legal Services & Advocacy", "Human Resources & Talent Management", "Event Planning & Management", 
        "Safety & Security Services", "Environmental Consulting & Conservation", 
        "Disaster Management & Emergency Services", "Agritech & Precision Farming"
    ]
    sector_problems = {}
    for sector in sectors_list:
        problems_in_sector = Problem.query.filter_by(sector=sector).order_by(Problem.created_at.desc()).all()
        if problems_in_sector:
            sector_problems[sector] = problems_in_sector
    viewed_sectors = db.session.query(UserSectorView.sector_name).filter_by(user_id=current_user.id).all()
    viewed_sectors = [sector[0] for sector in viewed_sectors]
    problems = Problem.query.filter(Problem.sector.in_(viewed_sectors)).order_by(func.random()).all()
    return render_template(
        'problems.html', 
        unread_count=unread_count, 
        notifications=notifications, 
        sector_problems=sector_problems, user=user, problems=problems
    )
class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sector = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0, nullable=False)
    unlikes = db.Column(db.Integer, default=0, nullable=False)   
    discussions = db.relationship('Discussion', backref='problem', lazy=True, cascade="all, delete-orphan")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    user = db.relationship('User', backref='problems')
    liked_users = db.relationship('User', secondary='problem_likes', backref='liked_problems')
    unliked_users = db.relationship('User', secondary='problem_unlikes', backref='unliked_problems')
    ai_analysis = db.Column(db.Text)

class ProblemLike(db.Model):
    __tablename__ = 'problem_likes'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), primary_key=True)

class ProblemUnlike(db.Model):
    __tablename__ = 'problem_unlikes'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), primary_key=True)

class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    section = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    replies = db.relationship('Reply', backref='discussion', lazy=True, cascade="all, delete-orphan")
    user = db.relationship('User', foreign_keys=[author_id], backref='discussions')

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', backref='replies')

@app.route('/discussions/<int:discussion_id>/reply', methods=['POST'])
@login_required
def add_reply(discussion_id):
    content = request.form['content']
    reply = Reply(discussion_id=discussion_id, content=content, author_id=current_user.id)
    db.session.add(reply)
    db.session.commit()
    discussion = Discussion.query.get(discussion_id)
    problem = Problem.query.get(discussion.problem_id)
    discussion_owner = discussion.user
    if discussion_owner.id != current_user.id:
        notification = Notification(
            user_id=discussion_owner.id,
            sender_id=current_user.id,
            notification_type="comment_reply",
            msg=f"{current_user.username} replied to your discussion on {problem.title}.",
            resource_id=problem.id
        )
        db.session.add(notification)
        db.session.commit()

    return redirect(request.referrer)

@app.route('/delete_problem/<int:problem_id>', methods=['POST'])
@login_required
def delete_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    if problem.user_id != current_user.id:
        abort(403)
    try:
        db.session.delete(problem)
        db.session.commit()
        flash('Problem deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting problem: {e}', 'danger')
    return redirect(url_for('problems'))

@app.route('/edit_problem/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def edit_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    if problem.user_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        problem.title = request.form['problem_title']
        problem.description = request.form['problem_description']
        db.session.commit()
        flash('Problem updated successfully!', 'success')
        return redirect(url_for('problem_details', problem_id=problem.id))
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('edit_problem.html', problem=problem,
        unread_count=unread_count,
        notifications=notifications)

@app.route('/problems/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def problem_details(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    discussions = Discussion.query.filter_by(problem_id=problem.id).all()
    
    viewed_problems_count = UserSectorView.query.filter_by(user_id=current_user.id).count()
    if viewed_problems_count >= 1000000 and current_user.subscription_status != 'Active':
        if current_user.user_type in ['entrepreneur_innovator', 'both']:
            flash("You need a subscription to view more problems. Please subscribe to get unlimited access.", "warning")
            return redirect(url_for('subscribe'))
    
    if not UserSectorView.query.filter_by(user_id=current_user.id, sector_name=problem.sector).first():
        sector_view = UserSectorView(user_id=current_user.id, sector_name=problem.sector)
        db.session.add(sector_view)
        db.session.commit()
    if request.method == 'POST':
        if 'like' in request.form:
            if current_user not in problem.liked_users:
                problem.likes += 1
                problem.liked_users.append(current_user)
                if current_user in problem.unliked_users:
                    problem.unlikes -= 1
                    problem.unliked_users.remove(current_user)
                db.session.commit()
        elif 'unlike' in request.form:
            if current_user not in problem.unliked_users:
                problem.unlikes += 1
                problem.unliked_users.append(current_user)
                if current_user in problem.liked_users:
                    problem.likes -= 1
                    problem.liked_users.remove(current_user)
                db.session.commit()
    if problem.likes + problem.unlikes > 0:
        authenticity = (problem.likes / (problem.likes + problem.unlikes)) * 100
    else:
        authenticity = 0

    return render_template(
        'problem_details.html',
        problem=problem,
        unread_count=unread_count,
        notifications=notifications,
        discussions=discussions,
        current_user=current_user,
        authenticity=round(authenticity, 2)
    )

@app.route('/problems/<int:problem_id>/add_discussion', methods=['POST'])
@login_required
def add_discussion(problem_id):
    section = request.form['section']
    content = request.form['content']
    new_discussion = Discussion(problem_id=problem_id, section=section, content=content, author_id=current_user.id)
    db.session.add(new_discussion)
    db.session.commit()
    problem = Problem.query.get(problem_id)
    problem_owner = problem.user
    if problem_owner.id != current_user.id:
        notification = Notification(
            user_id=problem_owner.id,
            sender_id=current_user.id,
            notification_type="comment",
            msg=f"{current_user.username} commented on your problem: {problem.title}.",
            resource_id=problem.id
        )
        db.session.add(notification)
        db.session.commit()

    return redirect(url_for('problem_details', problem_id=problem_id))

class ProblemUserAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    action = db.Column(db.String(10), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'problem_id', name='user_problem_unique'),
    )

class Story(db.Model):
    __tablename__ = 'stories'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    background_image = db.Column(db.String(7), nullable=False, default='#ffffff')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text_color = db.Column(db.String(7), nullable=False)
    user = db.relationship('User', backref=db.backref('stories', lazy=True))

    def __repr__(self):
        return f'<Story {self.id}>'

@app.route('/create_story', methods=['GET', 'POST'])
@login_required
def create_story():
    if request.method == 'POST':
        content = request.form.get('content')
        background_image = request.form.get('background_image')
        text_color = request.form.get('text_color')
        
        if content:
            new_story = Story(content=content, background_image=background_image, text_color=text_color, user_id=current_user.id)
            db.session.add(new_story)
            db.session.commit()
            return redirect(url_for('story_detail', story_id=new_story.id))
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    
    return render_template('create_story.html', unread_count=unread_count, notifications=notifications)

@app.route('/stories')
@login_required
def story_feed():
    stories = Story.query.order_by(Story.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('story_feed.html', stories=stories,
        unread_count=unread_count,
        notifications=notifications)

@app.route('/story/<int:story_id>')
@login_required
def story_detail(story_id):
    story = Story.query.get_or_404(story_id)
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('story_detail.html', story=story, unread_count=unread_count, notifications=notifications)

@app.route('/edit_story/<int:story_id>', methods=['GET', 'POST'])
@login_required
def edit_story(story_id):
    story = Story.query.get_or_404(story_id)
    
    if story.user_id != current_user.id:
        flash("You are not authorized to edit this story.", 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        story.content = request.form['content']
        story.background_image = request.form['background_image']
        story.text_color = request.form['text_color']
        
        db.session.commit()
        flash("Your story has been updated.", 'success')
        return redirect(url_for('story_feed'))
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).limit(10).all()
    return render_template('edit_story.html', story=story,
        unread_count=unread_count,
        notifications=notifications)

@app.route('/delete_story/<int:story_id>', methods=['POST'])
@login_required
def delete_story(story_id):
    story = Story.query.get_or_404(story_id)
    if story.user_id != current_user.id:
        flash('You do not have permission to delete this story.', 'danger')
        return redirect(url_for('story_feed'))
    db.session.delete(story)
    db.session.commit()
    flash('Story deleted successfully.', 'success')
    return redirect(url_for('story_feed'))

@app.context_processor
def inject_total_users():
    total_users = User.query.count()
    return dict(total_users=total_users)

@app.before_request
def create_tables():
    if not hasattr(app, 'db_created'):
        db.create_all()
        app.db_created = True

@app.route('/ads.txt')
def serve_ads_txt():
    return send_from_directory(os.getcwd(), 'ads.txt')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
