from flask import render_template, redirect, url_for, flash, request, send_from_directory
from Website.main import app
from Website.forms import RegisterForm, LoginForm, CreatePostForm, DeletePostForm, ChangeDisplayNameForm, ChangePasswordForm, AddCommentForm
from Website.models import db, user_model, post_model, comment_model
from flask_bcrypt import Bcrypt
import flask_login
import secrets
import werkzeug


# Initiating Bcrypt
bcrypt = Bcrypt(app)

# Initiating the database
db.init_app(app)
with app.app_context():
    db.create_all()

    #post1 = post_model(title="this is the title", content="this is the content", user_id=1)
    #db.session.add_all([post1])
    #db.session.commit()


# Initiating login manager
login_manager = flask_login.LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)


# Login manager callbacks and user loader

@login_manager.unauthorized_handler
def unauthorized_user_callback():
    flash(message="Register to access the rest of the website.", category="info")
    return redirect(url_for('register'))

@login_manager.user_loader
def load_user(user_id):
    return user_model.query.get(int(user_id))


# Website routes

@app.route('/show_attachment/<filename>', methods=['GET', 'POST'])
def show_attachment(filename):
    if filename:
        print(f"{filename} exists")

    else:
        print("no filename")

    return send_from_directory(app.config['UPLOAD_DIRECTORY'], filename)


@app.route('/like_post/')


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    posts = post_model.query.all()[::-1]
    users = []

    for post in posts:
        users.append( user_model.query.filter_by(user_id=post.user_id).first() )
        
    return render_template('public/home.html', posts_and_users=zip(posts,users))


@app.route('/view_post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    current_user = flask_login.current_user
    addCommentForm = AddCommentForm()
    deletePostForm = DeletePostForm()
    
    try:
        post = post_model.query.filter_by(post_id=post_id).first()
        comments = comment_model.query.filter_by(post_id=post_id)
        user = user_model.query.filter_by(user_id=post.user_id).first()
    
    except AttributeError:
        return redirect(url_for('home'))

    if addCommentForm.validate_on_submit():
        print("added comment")
        newComment = comment_model(content=addCommentForm.content.data, user_id=current_user.user_id, username=current_user.username, display_name=current_user.display_name, post_id=post.post_id)
        db.session.add_all([newComment])
        db.session.commit()

        flash('Your comment was added!', category="success")
        return redirect(url_for('view_post', post_id=post_id))

    if deletePostForm.validate_on_submit():
        if post.user_id == current_user.user_id:
            print("post deleted")
            db.session.delete(post)
            db.session.commit()

            flash('Your post was succesfully deleted.', category="success")
            return redirect(url_for('home'))
    
    return render_template('public/view_post.html', post=post, user=user,  comments=comments, current_user=current_user, addCommentForm=addCommentForm, deletePostForm=deletePostForm)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        # Using a guard clause to ensure that the username and password are not the same
        if username == password:
            flash(message="Your username and password must not be the same.", category="danger")
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password=password).decode('utf-8')
        user = user_model(username=username, display_name=username, email=email, password=hashed_password) #keeping display and user same for now
        db.session.add(user)
        db.session.commit()
        
        flash(message=f"Registration successful. Please login now.", category="info")
        return redirect(url_for('login'))

    return render_template('user/auth/register.html', form=form, current_user=flask_login.current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = user_model.query.filter_by(email=email).first()
        if user:
            # Checking whether the password is right
            if bcrypt.check_password_hash(user.password, password): # (hashed_password, entered_password)
                flask_login.login_user(user)

                flash(message=f"You are logged in as {user.username}.", category="success")
                return redirect(url_for('home'))
            
            # If incorrect password is given
            flash(message=f"Incorrect password.", category="danger")
            return redirect(url_for('login'))
        
        else:
            # Checking whether the email given exists or not
            flash(message="An account with that email doesn't exist. Please register here.", category="danger")
            return redirect(url_for('register'))


    return render_template('user/auth/login.html', form=form)


@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for('home'))


@app.route('/settings', methods=['GET', 'POST'])
@flask_login.login_required
def settings():
    changeDisplayNameForm = ChangeDisplayNameForm()
    changePasswordForm = ChangePasswordForm()
    user = flask_login.current_user

    # Change display name form
    if changeDisplayNameForm.validate_on_submit():
        #queriedUser = user_model.query.filter_by(user_id=user.user_id).first()

        if bcrypt.check_password_hash(user.password, changeDisplayNameForm.password.data):
            user.changeDisplayName( changeDisplayNameForm.new_display_name.data )
            db.session.commit()
            print(user.display_name)

        else:
            flash(message=f"Incorrect password.", category="danger")
            return redirect(url_for('settings'))
    
    # Change password form
    if changePasswordForm.validate_on_submit():
        #queriedUser = user_model.query.filter_by(user_id=user.user_id).first()

        if bcrypt.check_password_hash(user.password, changePasswordForm.password.data):
            user.changePassword( bcrypt.generate_password_hash(password=changePasswordForm.new_password.data) )
            db.session.commit()
            print(user.password)
        
        else:
            flash(message=f"Incorrect password.", category="danger")
            return redirect(url_for('settings'))

    return render_template('user/utils/settings.html', current_user=user, changeDisplayNameForm=changeDisplayNameForm, changePasswordForm=changePasswordForm)


@app.route('/create_post', methods=['GET', 'POST'])
@flask_login.login_required
def create_post():
    form = CreatePostForm()

    if form.validate_on_submit():
        user = flask_login.current_user
        
        newPostTitle = form.title.data
        newPostContent = form.content.data
        newPostAttachmentFile = request.files['attachment']
        

        if newPostAttachmentFile:
            newPostAttachmentFileName = newPostAttachmentFile.filename.split('.')[0] # "dog"
            newPostAttachmentFileExtension = "." + newPostAttachmentFile.filename.split('.')[1] # ".webp" or ".png"

            newPostAttachmentFileNameSecure = werkzeug.utils.secure_filename(f"{secrets.token_hex(32)}{newPostAttachmentFileName}{newPostAttachmentFileExtension}") # rough example: "1N38U4g349ut092jFiSDnsvZdog.png"
            print(f"Custom Logging/Image Upload Alert: {newPostAttachmentFileName} was submitted as an attachment to a post called {newPostTitle}!")
            
            newPostAttachmentFile.save(f'Website/static/uploads/{newPostAttachmentFileNameSecure}')

        else:
            newPostAttachmentFileNameSecure = None
        
        newPost = post_model(title=newPostTitle, content=newPostContent, user_id=user.user_id, upvote_count=0, downvote_count=0, attachment=newPostAttachmentFileNameSecure)
        
        db.session.add_all([newPost])
        db.session.commit()

        flash(message="Your post has been published!", category="success")
        return redirect(url_for('home'))

    return render_template('user/utils/create_post.html', form=form)




    