from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_ckeditor import CKEditorField

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=200)])
    summary = TextAreaField('Summary', validators=[DataRequired(), Length(min=10, max=500)])
    content = CKEditorField('Content', validators=[DataRequired()])
    featured_image = FileField('Featured Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    publish = BooleanField('Publish')
    submit = SubmitField('Save')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Post Comment')
