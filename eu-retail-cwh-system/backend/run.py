import os
import sys
import threading
import time
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', '0') == '1'
    auto_open = os.environ.get('AUTO_OPEN_BROWSER', '1') == '1'
    if auto_open and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        def _open_browser():
            time.sleep(1.5)
            webbrowser.open(f'http://127.0.0.1:{port}')
        threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=port, debug=debug)
