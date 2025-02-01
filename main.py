import base64
from flask import request, session, send_from_directory
from flask import Flask, render_template, redirect, request, url_for, flash,g,abort,Response,jsonify
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
from datetime import date,datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm,UserForm,LogForm,CommentsForm
from flask_gravatar import Gravatar
from flask_bcrypt import Bcrypt
from functools import wraps
import os
from flask_migrate import Migrate
from dotenv import find_dotenv,load_dotenv
import requests

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ALLOWED_EXTENSIONS = set(['txt','pdf','png','jpg','jpeg','gif'])
UPLOAD_FOLDER = "static/assets/images"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy()
db.init_app(app)
flask_bcrypt = Bcrypt()
flask_bcrypt.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
migrate = Migrate(app, db) 

# ckeditor = CKEditor()
# ckeditor.init_app(app)
CLIENT_id = os.getenv('CLIENT_id')
TMDB_API_KEY  = os.getenv('TMDB_API_KEY')
API_READ_KEY = os.getenv('API_READ_KEY')
##CONNECT TO DB

##CREATE TABLE IN DB
likes = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('userpost.id'), primary_key=True),  # Updated to 'userpost.id'
    db.Column('timestamp', db.DateTime, default=datetime.now)
)
class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000),unique=True)
    anime = db.relationship("UserAnime", back_populates="user") 
    manga = db.relationship("UserManga", back_populates="user")
    posts = db.relationship("UserPost", back_populates="author", cascade="all, delete-orphan")  
    liked_posts = db.relationship('UserPost', secondary=likes, backref=db.backref('liked_by', lazy='dynamic'))
    def __repr__(self):
        return '<User %r>' % self.name

class UserAnime(db.Model):
    __tablename__ = "useranime"
    id = db.Column(db.Integer, primary_key=True)
    mal_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("Users", back_populates="anime")
    review = db.Column(db.String(200))
    status = db.Column(db.String(200))
    details = db.Column(db.JSON)
    rating = db.Column(db.Float)
    date = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return '<UserAnime %r>' % self.name

class UserManga(db.Model):
    __tablename__ = "usermanga"
    id = db.Column(db.Integer, primary_key=True)
    mal_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("Users", back_populates="manga")
    review = db.Column(db.String(200))
    status = db.Column(db.String(200))
    details = db.Column(db.JSON)
    rating = db.Column(db.Float)
    date = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return '<UserManga %r>' % self.name

# class Likes(db.Model):
#     __tablename__ = "likes"
#     user_id = 

class UserPost(db.Model):
    __tablename__ = "userpost"
    id = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = db.relationship("Users", back_populates="posts")
    img_name = db.Column(db.String(200))
    image = db.Column(db.Text)
    mimetype = db.Column(db.Text)
    date = db.Column(db.String(250), nullable=False)
    anime_tag_name = db.Column(db.String(200))
    anime_tag_mal_id = db.Column(db.Integer)
    tag_class = db.Column(db.Text)
    
    def __repr__(self):
        return '<UserPost %r>' % self.img_name
        


with app.app_context():
    db.create_all()



def get_season(month):
    winter = ["January","Febuary","March"] 
    spring = ["April","May","June"]
    summer = ["July","August","September"]
    fall = ["October","November","December"]
    if month in winter:
        return "winter"
    elif month in spring:
        return "spring"
    elif month in summer:
        return "summer"
    else:
        return "fall"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return  db.session.get(Users, int(user_id))

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.get_id() != '1':
            return abort(403)
        return f(*args, **kwargs)        
    return decorated_function


@app.route("/")
def cover():
    return render_template("cover_index.html")

@app.route("/main")
def home():
    all_posts = UserPost.query.all()
    return render_template(
        "index.html",
        logged_in=current_user.is_authenticated,
        active=True,
        all_posts=all_posts
    )

@app.route('/image/<int:image_id>')
def serve_image(image_id):
    # Retrieve the image data from the database
    image = UserPost.query.get(image_id)
    if not image or not image.image:
        abort(404)  # Return 404 if the image doesn't exist or is empty

    # Send the image binary data as a response
    return Response(
        base64.b64decode(image.image),
        mimetype=image.mimetype  # Use the MIME type stored in the database
    )


@app.route("/main", methods=["GET", "POST"]) # type: ignore
@login_required
def post():
    author = Users.query.get(current_user.id)
    if request.method == "POST":
        body = request.form.get("post_body")
        imagefile = request.files.get("file")
        if imagefile and allowed_file(imagefile.filename):
            filename = secure_filename(imagefile.filename)
            mimetype = imagefile.mimetype
            image_data = base64.b64encode(imagefile.read()).decode('utf-8')
            new_post = UserPost(
                author = author,
                post=body,
                img_name=filename,
                mimetype=mimetype,
                image=image_data,
                date=date.today().strftime("%B %d, %Y")
            )
        else:
            new_post = UserPost(
                author = author,
                post=body,
                date=date.today().strftime("%B %d, %Y")
            )

        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))

@app.route('/tagged post', methods=['POST', 'GET'])
@login_required
def post_tagged():
    author = Users.query.get(current_user.id)
    anime_tag_name = request.form.get("tag_name")
    anime_tag_mal_id = request.form.get("tag_mal_id")
    tag_type = request.form.get("tag_type")
    if anime_tag_name:
        print("anime_tag_name")

    if request.method == "POST":
        body = request.form.get("post_body")
        imagefile = request.files.get("file")

        if not body:
            flash("Post body cannot be empty.", "error")
            return redirect(url_for('home', anime_tag_name=anime_tag_name, anime_tag_mal_id=anime_tag_mal_id))

        try:
            if imagefile and allowed_file(imagefile.filename):
                filename = secure_filename(imagefile.filename)
                mimetype = imagefile.mimetype
                image_data = base64.b64encode(imagefile.read()).decode('utf-8')

                new_post = UserPost(
                    author=author,
                    post=body,
                    img_name=filename,
                    mimetype=mimetype,
                    image=image_data,
                    date=date.today().strftime("%B %d, %Y"),
                    anime_tag_name=anime_tag_name,
                    anime_tag_mal_id=anime_tag_mal_id,
                    tag_class = tag_type
                )
            else:
                new_post = UserPost(
                    author=author,
                    post=body,
                    date=date.today().strftime("%B %d, %Y"),
                    anime_tag_mal_id=anime_tag_mal_id,
                    anime_tag_name=anime_tag_name,
                    tag_class  =tag_type
                )

            db.session.add(new_post)
            db.session.commit()
            flash("Post created successfully!", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "error")
            print(f"Error: {str(e)}")

    return redirect(url_for('home', anime_tag_name=anime_tag_name, anime_tag_mal_id=anime_tag_mal_id,tag_type = tag_type))


@app.route("/sign up",methods=["GET","POST"])
def register():
    if Users.query.filter_by(name=request.form.get("name")).first():
        flash("Name already taken")
    elif Users.query.filter_by(email = request.form.get("email")).first():
        flash("Email already registered, log in instead")
        return redirect("login")
    else:
        if request.method == "POST":
            new_user = Users(
                name = request.form.get("name"),
                email = request.form.get("email"),
                password = flask_bcrypt.generate_password_hash(request.form.get("password"),10)
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('profile'))
    return render_template("sign.html", active=True)



@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    animes = UserAnime.query.filter_by(user_id=current_user.get_id()).all()
    return render_template("profile.html",
                           user = current_user,logged_in = current_user.is_authenticated,
                           animes=animes,active=True)


@app.route("/mangas", methods=["GET","POST"])
@login_required
def mangas():
    mangas = UserManga.query.filter_by(user_id=current_user.get_id()).all()
    return render_template("mangas.html",
                           user = current_user,logged_in = current_user.is_authenticated,
                           mangas=mangas, active=True)

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        if not Users.query.filter_by(email = request.form.get("email")).first():
            flash("Email not registered, register instead")
            return redirect('register')
    
        user = Users.query.filter_by(email= request.form.get("email")).first()
        if flask_bcrypt.check_password_hash(user.password,request.form.get("password")):
            login_user(user)
            return redirect(url_for('profile'))
        else:
            flash("Password Incorrect")
            return redirect(url_for('login'))
    return render_template("login.html",logged_in = True)


@app.route("/shows",methods=["GET","POST"])
@login_required
def shows():
    if request.method == "POST":
        new = request.form.get("search")
        parameters = {
             "q":f"{new}",
            }
        headers = {
            "X-MAL-CLIENT-ID":f"{CLIENT_id}"
            }
        response = requests.get(url="https://api.myanimelist.net/v2/anime",
                                params=parameters,headers=headers)     
        an = response.json()["data"] 
        params = {
             "q":f"{new}",
            }
        manga = requests.get(url="https://api.myanimelist.net/v2/manga",
                                params=params,headers=headers)     
        mg = manga.json()["data"]
                
        return render_template("shows.html",an = an, search=True, mangas = mg, active=True)
    return render_template("shows.html", active=True)


@app.route("/add show",methods=["GET","POST"])
@login_required
def add():
    anime_id = request.args.get("id")
    posts = UserPost.query.filter_by(anime_tag_mal_id = anime_id).all()

    parameters = {
            "fields":"id,title,main_picture,alternative_titles,synopsis,genres,num_episodes,start_season,recommendations"
        }
    headers = {
        "X-MAL-CLIENT-ID":f"{CLIENT_id}"
        }
    response = requests.get(url=f"https://api.myanimelist.net/v2/anime/{anime_id}",params=parameters,headers=headers) 
    if response.status_code == 200:
        anime = response.json()
        return render_template("add.html",anime = anime, 
                               genres=anime['genres'],
                               synonyms =anime['alternative_titles']['synonyms'],recomendations = anime['recommendations'],
                               num_recommendations = len(anime['recommendations']),
                               tag_type = "anime",all_posts = posts,num_posts = len(posts))
    return render_template("add.html")


@app.route("/add manga",methods=["GET","POST"])
@login_required
def add_manga():
    manga_id = request.args.get("id")
    posts = UserPost.query.filter_by(anime_tag_mal_id = manga_id).all()
    parameters = {
            "fields":"id,title,main_picture,alternative_titles,synopsis,genres,num_chapters,num_volumes,start_date,related_manga,related_anime,recommendations,status"
        }
    headers = {
        "X-MAL-CLIENT-ID":f"{CLIENT_id}"
        }
    response = requests.get(url=f"https://api.myanimelist.net/v2/manga/{manga_id}",params=parameters,headers=headers) 
    if response.status_code == 200:
        manga = response.json()
        return render_template("add_manga.html",manga = manga, 
                               genres=manga['genres'],
                               synonyms =manga['alternative_titles']['synonyms'],
                               tag_type = "manga" ,all_posts = posts,num_posts = len(posts))

    return render_template("add_manga.html",all_posts = posts,num_posts = len(posts))


@app.route("/add",methods=["GET","POST"])
@login_required
def addshow():
    anime_id = request.args.get("id")
    parameters = {
            "fields":"id,title,main_picture,alternative_titles,synopsis,genres,num_episodes,start_season,recommendations"
        }
    headers = {
        "X-MAL-CLIENT-ID":f"{CLIENT_id}"
        }
    response = requests.get(url=f"https://api.myanimelist.net/v2/anime/{anime_id}",params=parameters,headers=headers) 
    if response.status_code == 200:
        anime = response.json()
    if request.form.get("rating"):
        rating = float(request.form.get("rating"))  # Convert to integer
        if rating > 5:
            flash("Rating should not be more than 5")
    if request.method == "POST":
        new_anime = UserAnime(
            mal_id = request.args.get("id"),
            name = request.args.get("title"),
            user = current_user,
            review = request.form.get("overview"),
            rating = request.form.get("rating"),
            status = request.form.get("status"),
            date=date.today().strftime("%B %d, %Y"),
            details = anime
        )
        db.session.add(new_anime)
        db.session.commit()
    return redirect(url_for('profile'))
    
@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = UserPost.query.get_or_404(post_id)
    if current_user in post.liked_by:
        # Unlike the post
        post.liked_by.remove(current_user)
        db.session.commit()
        return jsonify({'status': 'unliked', 'likes_count': post.liked_by.count()})
    else:
        # Like the post
        post.liked_by.append(current_user)
        db.session.commit()
        return jsonify({'status': 'liked', 'likes_count': post.liked_by.count()})

@app.route('/post/<int:post_id>')
def show_post(post_id):
    post = UserPost.query.get_or_404(post_id)
    return render_template('post.html', post=post)


@app.route("/addmanga",methods=["GET","POST"])
@login_required
def addmanga():
    manga_id = request.args.get("id")
    parameters = {
            "fields":"id,title,main_picture,alternative_titles,synopsis,genres,num_chapters,num_volumes,start_date,related_manga,related_anime,recommendations,status"
        }
    headers = {
        "X-MAL-CLIENT-ID":f"{CLIENT_id}"
        }
    response = requests.get(url=f"https://api.myanimelist.net/v2/manga/{manga_id}",params=parameters,headers=headers) 
    if response.status_code == 200:
        manga = response.json()
    if request.form.get("rating"):
        rating = float(request.form.get("rating"))  # Convert to integer
        if rating > 5:
            flash("Rating should not be more than 5")
    if request.method == "POST":
        new_manga = UserManga(
            mal_id = request.args.get("id"),
            name = request.args.get("title"),
            user = current_user,
            review = request.form.get("overview"),
            rating = request.form.get("rating"),
            status = request.form.get("status"),
            date=date.today().strftime("%B %d, %Y"),
            details = manga
        )
        db.session.add(new_manga)
        db.session.commit()
    return redirect(url_for('mangas'))


@app.route("/log out")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)