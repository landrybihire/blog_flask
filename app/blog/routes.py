from flask import render_template, flash, redirect, url_for, request, current_app, abort, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Post, User, Comment, Like
from app.blog import bp
from app.blog.forms import PostForm, CommentForm
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from slugify import slugify
import sqlalchemy as sa

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(
        db.select(Post)
        .where(Post.published == True)
        .order_by(Post.created_at.desc()),
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )

    next_url = url_for('blog.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('blog.index', page=posts.prev_num) if posts.has_prev else None

    return render_template('blog/index.html', title='Blog',
                           posts=posts.items, next_url=next_url, prev_url=prev_url)

@bp.route('/post/<slug>', methods=['GET', 'POST'])
def post(slug):
    post = db.session.scalar(
        db.select(Post).where(Post.slug == slug, Post.published == True)
    )

    if post is None:
        abort(404)

    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if current_user.is_authenticated:
            comment = Comment(content=comment_form.content.data, author=current_user, post=post)
            db.session.add(comment)
            db.session.commit()
            flash('Your comment has been added!')
            return redirect(url_for('blog.post', slug=post.slug))
        else:
            flash('You must be logged in to comment.')
            return redirect(url_for('auth.login'))

    # Get comments for the post
    comments = db.session.scalars(
        db.select(Comment)
        .where(Comment.post_id == post.id)
        .order_by(Comment.created_at.asc())
    ).all()

    # Check if the current user has liked the post
    user_liked = False
    if current_user.is_authenticated:
        like = db.session.scalar(
            db.select(Like).where(Like.user_id == current_user.id, Like.post_id == post.id)
        )
        user_liked = like is not None

    # Get the total number of likes for the post
    like_count = db.session.scalar(
        sa.select(sa.func.count()).select_from(Like).where(Like.post_id == post.id)
    ) or 0


    return render_template('blog/post.html', title=post.title, post=post,
                           comment_form=comment_form, comments=comments,
                           user_liked=user_liked, like_count=like_count)

@bp.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = db.session.get(Post, post_id)
    if post is None:
        return jsonify({'error': 'Post not found'}), 404

    like = db.session.scalar(
        db.select(Like).where(Like.user_id == current_user.id, Like.post_id == post.id)
    )

    if like is None:
        # User has not liked the post, add a like
        new_like = Like(user=current_user, post=post)
        db.session.add(new_like)
        db.session.commit()
        liked = True
    else:
        # User has liked the post, remove the like
        db.session.delete(like)
        db.session.commit()
        liked = False

    like_count = db.session.scalar(
        sa.select(sa.func.count()).select_from(Like).where(Like.post_id == post.id)
    ) or 0

    return jsonify({'liked': liked, 'like_count': like_count})


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PostForm()
    if form.validate_on_submit():
        slug = slugify(form.title.data)

        # Check if slug already exists
        existing_post = db.session.scalar(
            db.select(Post).where(Post.slug == slug)
        )

        if existing_post:
            # Append a unique identifier to make the slug unique
            slug = f"{slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Handle featured image upload
        featured_image = None
        if form.featured_image.data:
            filename = secure_filename(form.featured_image.data.filename)
            # Create a unique filename
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{filename}"
            form.featured_image.data.save(os.path.join(
                current_app.config['UPLOAD_FOLDER'], unique_filename
            ))
            featured_image = unique_filename

        post = Post(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            slug=slug,
            featured_image=featured_image,
            published=form.publish.data,
            author=current_user
        )

        db.session.add(post)
        db.session.commit()

        flash('Your post has been created!')
        return redirect(url_for('blog.post', slug=post.slug))

    return render_template('blog/editor.html', title='Create Post', form=form)

@bp.route('/edit/<slug>', methods=['GET', 'POST'])
@login_required
def edit(slug):
    post = db.session.scalar(
        db.select(Post).where(Post.slug == slug)
    )

    if post is None:
        abort(404)

    if post.author != current_user:
        abort(403)

    form = PostForm()
    if form.validate_on_submit():
        # Only update slug if title has changed
        if post.title != form.title.data:
            new_slug = slugify(form.title.data)

            # Check if new slug already exists
            existing_post = db.session.scalar(
                db.select(Post).where(Post.slug == new_slug, Post.id != post.id)
            )

            if existing_post:
                # Append a unique identifier to make the slug unique
                new_slug = f"{new_slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            post.slug = new_slug

        # Handle featured image upload
        if form.featured_image.data:
            # Delete old image if it exists
            if post.featured_image:
                try:
                    os.remove(os.path.join(
                        current_app.config['UPLOAD_FOLDER'], post.featured_image
                    ))
                except:
                    pass

            filename = secure_filename(form.featured_image.data.filename)
            # Create a unique filename
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{filename}"
            form.featured_image.data.save(os.path.join(
                current_app.config['UPLOAD_FOLDER'], unique_filename
            ))
            post.featured_image = unique_filename

        post.title = form.title.data
        post.content = form.content.data
        post.summary = form.summary.data
        post.published = form.publish.data

        db.session.commit()

        flash('Your post has been updated!')
        return redirect(url_for('blog.post', slug=post.slug))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.summary.data = post.summary
        form.publish.data = post.published

    return render_template('blog/editor.html', title='Edit Post', form=form)

@bp.route('/delete/<slug>', methods=['POST'])
@login_required
def delete(slug):
    post = db.session.scalar(
        db.select(Post).where(Post.slug == slug)
    )

    if post is None:
        abort(404)

    if post.author != current_user:
        abort(403)

    # Delete featured image if it exists
    if post.featured_image:
        try:
            os.remove(os.path.join(
                current_app.config['UPLOAD_FOLDER'], post.featured_image
            ))
        except:
            pass

    db.session.delete(post)
    db.session.commit()

    flash('Your post has been deleted!')
    return redirect(url_for('blog.index'))
