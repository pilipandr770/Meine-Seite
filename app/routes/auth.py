"""Authentication routes for RoZoom website"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
import logging
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.database import db
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm, PasswordResetForm, PasswordChangeForm

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    
    if form.validate_on_submit():
        logger.info('Login attempt: form validated; email=%s, remember=%s, csrf=%s',
                    form.email.data, form.remember.data, getattr(form.csrf_token, 'data', None))
        # Find user by email
        user = User.query.filter_by(email=form.email.data.lower()).first()
        logger.info('Lookup user by email=%s -> %s', form.email.data.lower(), 'found' if user else 'not found')

        # Check if user exists and password is correct
        pw_ok = user and check_password_hash(user.password_hash, form.password.data)
        logger.info('Password check result for user %s: %s', form.email.data.lower(), bool(pw_ok))
        if pw_ok:
            # Check if user is active
            if not user.is_active:
                logger.info('Login blocked: account inactive for %s', user.email)
                flash('Your account is inactive. Please contact an administrator.', 'danger')
                return render_template('auth/login.html', form=form)

            # Log the user in
            login_user(user, remember=form.remember.data)
            logger.info('User logged in: %s (is_admin=%s)', user.email, bool(user.is_admin))

            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)

            # Redirect to admin dashboard for admins, or homepage for regular users
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            logger.info('Invalid login attempt for email=%s', form.email.data.lower())
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout the current user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data.lower()).first()
        if existing_user:
            flash('A user with that email already exists.', 'danger')
            return render_template('auth/register.html', form=form)
            
        # Check if username already exists
        existing_username = User.query.filter_by(username=form.username.data).first()
        if existing_username:
            flash('That username is already taken.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        new_user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            password_hash=generate_password_hash(form.password.data),
            is_admin=False,  # Default to non-admin
            is_active=True   # Default to active
        )
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Your account has been created! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/password-reset', methods=['GET', 'POST'])
def password_reset_request():
    """Password reset request page"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        # Find user by email
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        # Don't reveal if email exists or not for security reasons
        flash('If that email exists in our system, a password reset link has been sent.', 'info')
        
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            
            # Send email with reset link
            # TODO: Implement email sending functionality
            # For now, we'll just print the token for testing purposes
            print(f"Reset token for {user.email}: {token}")
            
        return redirect(url_for('auth.login'))
    
    return render_template('auth/password_reset_request.html', form=form)

@auth_bp.route('/password-reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    """Password reset page with token"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    # Verify token and get user
    user = User.verify_reset_token(token)
    
    if not user:
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.password_reset_request'))
    
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        # Update password
        user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        
        flash('Your password has been updated! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/password_reset.html', form=form)

@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html')
