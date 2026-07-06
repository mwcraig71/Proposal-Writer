import os
from flask import Flask
from flask_session import Session
from database import db

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "dev-secret-key-change-in-production"
if not os.environ.get("SESSION_SECRET"):
    print("WARNING: SESSION_SECRET not set; using insecure development secret key.")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 120,
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "connect_args": {
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
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

    # create_all() does not add new indexes to existing tables, so create any
    # missing ones explicitly (idempotent).
    try:
        from sqlalchemy import inspect as _sa_inspect
        _insp = _sa_inspect(db.engine)
        for _table in db.metadata.tables.values():
            _existing = {ix['name'] for ix in _insp.get_indexes(_table.name)}
            for _index in _table.indexes:
                if _index.name not in _existing:
                    _index.create(db.engine)
                    print(f"Created index {_index.name} on {_table.name}")
    except Exception as _idx_err:
        print(f"Index check skipped: {_idx_err}")

    from models import User
    if User.query.count() == 0:
        admin_password = os.environ.get('APP_PASSWORD', 'admin')
        admin_user = User(
            username='admin',
            display_name='Administrator',
            role='admin'
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Created default admin user (username: admin)")

# Global error handler for production debugging
@app.errorhandler(500)
def handle_500_error(e):
    import traceback
    original = getattr(e, 'original_exception', None)
    if original is not None:
        error_trace = ''.join(traceback.format_exception(type(original), original, original.__traceback__))
    else:
        error_trace = traceback.format_exc()
    app.logger.error("500 Error: %s\n%s", e, error_trace)
    if not app.debug:
        error_trace = 'Details have been logged on the server.'
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

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

from routes import *

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
