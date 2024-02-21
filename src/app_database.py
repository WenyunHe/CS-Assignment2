from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
class CompetitorNews(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    OEM = db.Column(db.String(255), unique=True, nullable=False)
    news = db.Column(db.JSON)
