import os
from flask import Flask
from database import db

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "dev-secret-key-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

db.init_app(app)

with app.app_context():
    import models
    db.create_all()

from routes import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
