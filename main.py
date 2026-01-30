import os
from flask import Flask
from flask_session import Session
from database import db

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "dev-secret-key-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max upload

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "/tmp/flask_session"
app.config["SESSION_PERMANENT"] = False
Session(app)

db.init_app(app)

with app.app_context():
    import models
    db.create_all()

# Global error handler for production debugging
@app.errorhandler(500)
def handle_500_error(e):
    import traceback
    error_trace = traceback.format_exc()
    print(f"500 Error: {e}")
    print(f"Traceback: {error_trace}")
    from flask import render_template_string, request as flask_request
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>Server Error</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>Something went wrong</h1>
            <p>Error: {{ error }}</p>
            <p><a href="javascript:history.back()">Go Back</a></p>
            <details style="margin-top: 20px;">
                <summary>Technical Details</summary>
                <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">{{ trace }}</pre>
            </details>
        </body>
        </html>
    ''', error=str(e), trace=error_trace), 500

from routes import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
