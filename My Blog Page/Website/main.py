from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = '9gj1!4aknfO8a54TQjxaNhg$3jPG]3[h;@579]nT2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
