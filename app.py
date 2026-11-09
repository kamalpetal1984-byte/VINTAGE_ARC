import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "CHANGE-THIS-TO-A-LONG-RANDOM-SECRET")
database_url = os.environ.get("DATABASE_URL", "sqlite:///vintage.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
db = SQLAlchemy(app)

MEMBER_CODE = os.environ.get("MEMBER_CODE", "")
ADMIN_CODE = os.environ.get("ADMIN_CODE", "")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    role = db.Column(db.String(10), default="member", nullable=False)
    bio = db.Column(db.String(180), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.String(2000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship("User", backref="posts")
    likes = db.relationship("Like", backref="post", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="post", cascade="all, delete-orphan", order_by="Comment.created_at.asc()")

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "post_id"),)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship("User")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.String(2000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User")

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_user():
    return {"current_user": User.query.get(session["user_id"]) if session.get("user_id") else None}

@app.route("/")
def home():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    posts = Post.query.order_by(Post.created_at.desc()).limit(100).all()
    users = User.query.order_by(User.username.asc()).all()
    stories = Story.query.filter(Story.created_at >= datetime.utcnow()-timedelta(hours=24)).order_by(Story.created_at.desc()).all()
    return render_template("home.html", posts=posts, users=users, stories=stories)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        code = request.form.get("code", "")
        if not username or len(username) > 32 or not username.replace("_", "").replace("-", "").isalnum():
            flash("Naam 1–32 characters ka ho; letters, numbers, _ aur - use karo.")
            return redirect(url_for("login"))
        role = "admin" if ADMIN_CODE and code == ADMIN_CODE else "member" if MEMBER_CODE and code == MEMBER_CODE else None
        if not role:
            flash("Secret code galat hai.")
            return redirect(url_for("login"))
        user = User.query.filter_by(username=username).first()
        if user and user.role != role:
            flash("Is account ka access type match nahi karta.")
            return redirect(url_for("login"))
        if not user:
            user = User(username=username, role=role)
            db.session.add(user)
            db.session.commit()
        session.clear()
        session["user_id"] = user.id
        session["role"] = user.role
        session.permanent = True
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/post", methods=["POST"])
@login_required
def create_post():
    body = request.form.get("body", "").strip()
    if body and len(body) <= 2000:
        db.session.add(Post(user_id=session["user_id"], body=body))
        db.session.commit()
    else:
        flash("Post 1–2000 characters ka hona chahiye.")
    return redirect(url_for("home"))

@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify(ok=False), 404
    existing = Like.query.filter_by(user_id=session["user_id"], post_id=post_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=session["user_id"], post_id=post_id))
        liked = True
    db.session.commit()
    count = Like.query.filter_by(post_id=post_id).count()
    return jsonify(ok=True, liked=liked, count=count)

@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment(post_id):
    body = request.form.get("body", "").strip()
    if not db.session.get(Post, post_id):
        return redirect(url_for("home"))
    if body and len(body) <= 500:
        db.session.add(Comment(user_id=session["user_id"], post_id=post_id, body=body))
        db.session.commit()
    return redirect(url_for("home"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = db.session.get(User, session["user_id"])
    if request.method == "POST":
        user.bio = request.form.get("bio", "").strip()[:180]
        db.session.commit()
        flash("Profile updated.")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)

@app.route("/messages")
@login_required
def messages():
    users = User.query.filter(User.id != session["user_id"]).order_by(User.username.asc()).all()
    selected = request.args.get("to", type=int)
    recipient = db.session.get(User, selected) if selected else (users[0] if users else None)
    if recipient and recipient.id == session["user_id"]:
        recipient = None
    return render_template("messages.html", users=users, recipient=recipient, my_id=session["user_id"])

@app.route("/api/messages/<int:other_id>")
@login_required
def api_messages(other_id):
    other = db.session.get(User, other_id)
    if not other or other.id == session["user_id"]:
        return jsonify(messages=[])
    me = session["user_id"]
    rows = Message.query.filter(
        or_(
            (Message.sender_id == me) & (Message.recipient_id == other_id),
            (Message.sender_id == other_id) & (Message.recipient_id == me)
        )
    ).order_by(Message.created_at.asc()).limit(200).all()
    return jsonify(messages=[{
        "id": m.id, "sender": m.sender.username, "sender_id": m.sender_id,
        "body": m.body, "time": m.created_at.strftime("%d %b %H:%M")
    } for m in rows])

@app.route("/api/messages/<int:other_id>", methods=["POST"])
@login_required
def send_message(other_id):
    other = db.session.get(User, other_id)
    body = request.json.get("body", "").strip() if request.is_json else ""
    if not other or other.id == session["user_id"] or not body or len(body) > 2000:
        return jsonify(ok=False), 400
    msg = Message(sender_id=session["user_id"], recipient_id=other_id, body=body)
    db.session.add(msg)
    db.session.commit()
    return jsonify(ok=True)

@app.route("/story", methods=["POST"])
@login_required
def create_story():
    body = request.form.get("body", "").strip()
    if body and len(body) <= 500:
        db.session.add(Story(user_id=session["user_id"], body=body))
        db.session.commit()
    return redirect(url_for("home"))

@app.route("/admin")
@login_required
def admin():
    if session.get("role") != "admin":
        flash("Admin access required.")
        return redirect(url_for("home"))
    return render_template("admin.html", users=User.query.order_by(User.created_at.desc()).all(),
                           posts=Post.query.order_by(Post.created_at.desc()).limit(50).all())

@app.route("/admin/delete-post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    if session.get("role") != "admin":
        return "Forbidden", 403
    post = db.session.get(Post, post_id)
    if post:
        Like.query.filter_by(post_id=post_id).delete()
        Comment.query.filter_by(post_id=post_id).delete()
        db.session.delete(post)
        db.session.commit()
    return redirect(url_for("admin"))

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", message="Page not found."), 404

@app.errorhandler(500)
def server_error(_):
    db.session.rollback()
    return render_template("error.html", message="Something went wrong. Please try again."), 500

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
