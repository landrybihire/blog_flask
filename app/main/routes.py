from flask import render_template, url_for, current_app
from app.main import bp
from app.models import Post
from app import db

@bp.route('/')
@bp.route('/index')
def index():
    # Get the latest 5 published posts
    posts = db.session.execute(
        db.select(Post)
        .where(Post.published == True)
        .order_by(Post.created_at.desc())
        .limit(5)
    ).scalars().all()
    
    return render_template('main/index.html', title='Home', posts=posts)

@bp.route('/about')
def about():
    return render_template('main/about.html', title='About')

@bp.route('/contact')
def contact():
    return render_template('main/contact.html', title='Contact')
