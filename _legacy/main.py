import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from threading import Thread
import os
import time

from meetings import meetings_bp
from biometrics import biometrics_bp
from telegram_bot import start_telegram_bot

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

app.register_blueprint(meetings_bp, url_prefix='/api')
app.register_blueprint(biometrics_bp, url_prefix='/api')

# The prototype uses in-memory storage; SQLAlchemy can be configured here for persistence.

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    # Start telegram bot in a background thread (if TELEGRAM_TOKEN is provided)
    token = os.environ.get('TELEGRAM_TOKEN')
    if token:
        def bot_thread():
            try:
                start_telegram_bot(token, api_base_url='http://localhost:5000/api')
            except Exception as e:
                print('Telegram bot failed to start:', e)

        t = Thread(target=bot_thread, daemon=True)
        t.start()
        # give bot a moment to connect
        time.sleep(1)

    app.run(host='0.0.0.0', port=5000, debug=True)

