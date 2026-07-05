import hashlib
import hmac
import os
import time
from flask import Flask, request, jsonify, g, send_from_directory

# ========== Auth Config ==========
_SECRET_KEY = os.urandom(32)
_USERS = {
    'qiteng': {'display': 'Qiteng', 'password': '84405995', 'role': 'admin'},
    'juan': {'display': 'Juan', 'password': '00655485', 'role': 'user'},
    'zoya': {'display': 'Zoya', 'password': '00598850', 'role': 'user'},
    'pi': {'display': 'Pi', 'password': '00496517', 'role': 'user'},
    'limin': {'display': 'Limin', 'password': '00622861', 'role': 'user'},
    'yuji': {'display': 'Yuji', 'password': '00566461', 'role': 'user'},
    'xuan': {'display': 'Xuan', 'password': '84416525', 'role': 'user'},
    'ziyi': {'display': 'Ziyi', 'password': '84409733', 'role': 'user'},
}


def verify_password(username, password):
    user_key = (username or '').strip().lower()
    user = _USERS.get(user_key)
    if not user:
        return None
    expected = hmac.new(_SECRET_KEY, user['password'].encode(), hashlib.sha256).hexdigest()
    actual = hmac.new(_SECRET_KEY, str(password or '').encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual, expected):
        return None
    return {'username': user['display'], 'role': user['role']}

def generate_token():
    token = os.urandom(32).hex()
    ts = str(int(time.time()))
    raw = f"{token}:{ts}"
    sig = hmac.new(_SECRET_KEY, raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}:{sig}"

def verify_token(token_str):
    try:
        parts = token_str.split(':')
        if len(parts) != 3:
            return False
        token, ts, sig = parts
        raw = f"{token}:{ts}"
        expected = hmac.new(_SECRET_KEY, raw.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False

_active_tokens = {}

_PUBLIC_PATHS = {'/api/auth/login', '/api/auth/check', '/'}


def check_token_auth():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return False
    token = auth[7:]
    user = _active_tokens.get(token)
    if not user:
        return False
    g.current_user = user.get('username')
    g.current_role = user.get('role')
    g.is_admin = user.get('role') == 'admin'
    return True


def require_auth():
    path = request.path
    if path.startswith('/static/'):
        return None
    if not path.startswith('/api/'):
        return None
    if path in _PUBLIC_PATHS:
        return None
    if check_token_auth():
        return None
    return jsonify({'error': 'unauthorized', 'code': 401}), 401


def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 物流看板数据库 (shipments)
    app.config['DATABASE'] = os.path.join(BASE_DIR, 'app', 'data', 'warehouse.db')
    # WMS 库存数据库
    app.config['WMS_DATABASE'] = os.path.join(BASE_DIR, 'app', 'data', 'wms.db')
    # 上传目录
    app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'app', 'static', 'images')

    # Auth
    AUTH_ENABLED = os.environ.get('DASHBOARD_AUTH', '1') == '1'
    if AUTH_ENABLED:
        @app.before_request
        def _require_auth():
            return require_auth()

    @app.after_request
    def add_no_cache_headers(response):
        if response.content_type and (
            'application/json' in response.content_type
            or 'text/html' in response.content_type
            or request.path == '/'
            or request.path.endswith('/index.html')
        ):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    # Create data directories
    os.makedirs(os.path.join(BASE_DIR, 'app', 'data'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'app', 'data', 'uploads'), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'app', 'static', 'report_assets'), exist_ok=True)

    # Register blueprints
    from .routes import main_bp
    from .wms_routes import inventory_bp, delivery_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(delivery_bp)

    # Init databases
    from .db import init_db, init_wms_db
    init_db(app)
    init_wms_db(app)

    # Auth API
    @app.route('/api/auth/login', methods=['POST'])
    def api_login():
        data = request.get_json(silent=True) or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        user = verify_password(username, password)
        if user:
            token = generate_token()
            _active_tokens[token] = user
            return jsonify({'success': True, 'token': token, 'user': user})
        return jsonify({'error': '用户名或密码错误'}), 401

    @app.route('/api/auth/check', methods=['GET'])
    def api_auth_check():
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
            if token in _active_tokens:
                return jsonify({'authenticated': True, 'user': _active_tokens[token]})
        return jsonify({'authenticated': False}), 401

    # Serve Vue shell. The legacy index is kept only as reference during rebuild.
    STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')
    @app.route('/')
    def index():
        vue_index = os.path.join(STATIC_DIR, 'vue', 'index.html')
        if os.path.exists(vue_index):
            return send_from_directory(os.path.join(STATIC_DIR, 'vue'), 'index.html')
        return send_from_directory(STATIC_DIR, 'index.html')

    @app.route('/<path:frontend_path>')
    def vue_fallback(frontend_path):
        if frontend_path.startswith('api/'):
            return jsonify({'error': 'not found'}), 404
        vue_index = os.path.join(STATIC_DIR, 'vue', 'index.html')
        if os.path.exists(vue_index):
            return send_from_directory(os.path.join(STATIC_DIR, 'vue'), 'index.html')
        return send_from_directory(STATIC_DIR, 'index.html')

    return app
