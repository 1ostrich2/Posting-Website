from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

