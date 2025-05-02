import click
from app import create_app, db
from app.models import User, Post

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}

@app.cli.command('create-admin')
def create_admin():
    """Creates the default admin user."""
    username = 'landryb'
    password = 'sudomkdir'
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'Utilisateur admin "{username}" créé avec succès.')
    else:
        print(f'L\'utilisateur admin "{username}" existe déjà.')

if __name__ == '__main__':
    app.run(debug=True)
