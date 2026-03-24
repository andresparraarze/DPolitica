"""
DPolitica - Main Flask Application
Political Transparency Platform for Bolivia
"""

import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, Candidate, Source, Submission, Connection, AdminLog
from datetime import datetime
from functools import wraps

# Load .env from the same directory as this file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

MAX_CANDIDATE_NAME = 200
MAX_CONTENT = 5000
MAX_SOURCE_LINK = 500
MAX_PARTY = 200
MAX_SUMMARY = 2000
MAX_HISTORY = 5000

ALLOWED_SOURCE_TYPES = {'tip', 'evidence', 'document', 'video', 'witness', 'other'}


def validate_url(url: str) -> bool:
    """Return True if *url* uses an http(s) scheme, False otherwise."""
    if not url:
        return True  # empty is acceptable (optional field)
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https')
    except Exception:
        return False


def create_app():
    app = Flask(__name__)

    # ---------- Configuration ----------
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-in-production')

    # Database: use DATABASE_URL (PostgreSQL) if set, otherwise SQLite for local dev
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Railway uses postgres:// but SQLAlchemy 1.4+ requires postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dpolitica.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Production mode
    flask_env = os.environ.get('FLASK_ENV', 'development')
    app.config['DEBUG'] = (flask_env == 'development')

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.context_processor
    def now():
        return {'now': datetime.utcnow().strftime('%Y-%m-%d')}

    with app.app_context():
        db.create_all()

    # ---------- Routes ----------
    app.add_url_rule('/', view_func=index)
    app.add_url_rule('/candidates', view_func=candidates)
    app.add_url_rule('/candidates/<int:candidate_id>', view_func=candidate_detail)
    app.add_url_rule('/submit', view_func=submit, methods=['GET', 'POST'])
    app.add_url_rule('/sources', view_func=sources)
    app.add_url_rule('/api/candidates', view_func=api_candidates, methods=['GET', 'POST'])
    app.add_url_rule('/api/candidates/<int:candidate_id>', view_func=api_candidate_detail, methods=['GET'])
    app.add_url_rule('/health', view_func=health)

    # Admin panel
    from admin import admin_bp
    app.register_blueprint(admin_bp)

    return app

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple admin check - expand as needed
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@csrf.exempt
def health():
    """Health check endpoint for Railway / load balancers."""
    return jsonify({'status': 'ok'}), 200

def index():
    """Homepage with stats and featured candidates"""
    total_candidates = Candidate.query.count()
    total_submissions = Submission.query.count()
    verified_submissions = Submission.query.filter_by(is_verified=True).count()

    # Featured: recently added or high-profile candidates
    featured = Candidate.query.order_by(Candidate.created_at.desc()).limit(3).all()

    return render_template('index.html',
                         total_candidates=total_candidates,
                         total_submissions=total_submissions,
                         verified_submissions=verified_submissions,
                         featured=featured)

def candidates():
    """List all candidates with search and filters"""
    search = request.args.get('search', '')
    party = request.args.get('party', '')
    min_connections = request.args.get('connections', type=int)

    query = Candidate.query

    if search:
        query = query.filter(Candidate.name.contains(search))

    if party:
        query = query.filter(Candidate.party.contains(party))

    candidates = query.order_by(Candidate.name.asc()).all()

    # Filter by connection count in Python (property-based, not a DB column)
    if min_connections is not None:
        candidates = [c for c in candidates if c.connection_count >= min_connections]

    return render_template('candidates.html',
                         candidates=candidates,
                         search=search,
                         party=party,
                         min_connections=min_connections)

def candidate_detail(candidate_id):
    """Detailed view of a single candidate"""
    candidate = Candidate.query.get_or_404(candidate_id)

    # Get related data
    sources = Source.query.filter_by(candidate_id=candidate_id).all()
    connections = Connection.query.filter_by(candidate_id=candidate_id).all()
    submissions = Submission.query.filter_by(
        candidate_id=candidate_id, is_verified=True
    ).order_by(Submission.created_at.desc()).all()

    return render_template('candidate.html',
                         candidate=candidate,
                         sources=sources,
                         connections=connections,
                         submissions=submissions)

@limiter.limit("5 per minute", methods=["POST"])
def submit():
    """Anonymous submission form for tips and data"""
    if request.method == 'POST':
        candidate_name = request.form.get('candidate_name', '').strip()
        content = request.form.get('content', '').strip()
        source_link = request.form.get('source_link', '').strip()
        source_type = request.form.get('source_type', 'tip')

        # --- Input length validation ---
        if len(candidate_name) > MAX_CANDIDATE_NAME:
            flash('El nombre del candidato es demasiado largo (máx. 200 caracteres).', 'error')
            return redirect(url_for('submit'))

        if not content:
            flash('Please provide information.', 'error')
            return redirect(url_for('submit'))

        if len(content) > MAX_CONTENT:
            flash('La información es demasiado larga (máx. 5000 caracteres).', 'error')
            return redirect(url_for('submit'))

        if len(source_link) > MAX_SOURCE_LINK:
            flash('El enlace es demasiado largo (máx. 500 caracteres).', 'error')
            return redirect(url_for('submit'))

        # --- URL validation ---
        if source_link and not validate_url(source_link):
            flash('El enlace debe usar http:// o https://.', 'error')
            return redirect(url_for('submit'))

        # --- Source type validation ---
        if source_type not in ALLOWED_SOURCE_TYPES:
            source_type = 'tip'

        # Find or create candidate
        candidate = None
        if candidate_name:
            candidate = Candidate.query.filter_by(name=candidate_name).first()
            if not candidate:
                # Auto-create candidate entry
                candidate = Candidate(name=candidate_name)
                db.session.add(candidate)
                db.session.flush()

        # Read the anonymous checkbox (unchecked = not sent, so default to False)
        is_anonymous = 'anonymous' in request.form

        # Create submission
        submission = Submission(
            candidate_id=candidate.id if candidate else None,
            content=content,
            source_link=source_link if source_link else None,
            source_type=source_type,
            is_verified=False,
            is_anonymous=is_anonymous
        )
        db.session.add(submission)
        db.session.commit()

        flash('Thank you for your submission. This will be reviewed before publication.', 'success')
        return redirect(url_for('index'))

    return render_template('submit.html')

def sources():
    """View all sources and their links"""
    sources = Source.query.order_by(Source.created_at.desc()).all()
    return render_template('sources.html', sources=sources)

@csrf.exempt
def api_candidates():
    """API endpoint for candidates"""
    # POST: Create new candidate (requires API key)
    if request.method == 'POST':
        # --- API key authentication ---
        api_key = request.headers.get('X-API-Key', '')
        expected_key = os.environ.get('API_KEY', '')
        if not api_key or not expected_key or api_key != expected_key:
            return jsonify({'error': 'Unauthorized. Valid X-API-Key header required.'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON.'}), 400

        # --- Input length validation ---
        name = data.get('name', 'Unknown')
        if len(name) > MAX_CANDIDATE_NAME:
            return jsonify({'error': f'name exceeds {MAX_CANDIDATE_NAME} characters.'}), 400

        party = data.get('party', '')
        if len(party) > MAX_PARTY:
            return jsonify({'error': f'party exceeds {MAX_PARTY} characters.'}), 400

        background_summary = data.get('background_summary', '')
        if len(background_summary) > MAX_SUMMARY:
            return jsonify({'error': f'background_summary exceeds {MAX_SUMMARY} characters.'}), 400

        political_history = data.get('political_history', '')
        if len(political_history) > MAX_HISTORY:
            return jsonify({'error': f'political_history exceeds {MAX_HISTORY} characters.'}), 400

        criminal_connections = data.get('criminal_connections', '')
        if len(criminal_connections) > MAX_HISTORY:
            return jsonify({'error': f'criminal_connections exceeds {MAX_HISTORY} characters.'}), 400

        funding_sources = data.get('funding_sources', '')
        if len(funding_sources) > MAX_HISTORY:
            return jsonify({'error': f'funding_sources exceeds {MAX_HISTORY} characters.'}), 400

        candidate = Candidate(
            name=name,
            party=party,
            background_summary=background_summary,
            political_history=political_history,
            criminal_connections=criminal_connections,
            funding_sources=funding_sources
        )

        db.session.add(candidate)
        db.session.commit()

        return jsonify({
            'id': candidate.id,
            'name': candidate.name,
            'party': candidate.party,
            'message': 'Candidate created successfully'
        }), 201

    # GET: List candidates
    search = request.args.get('search', '')

    query = Candidate.query
    if search:
        query = query.filter(Candidate.name.contains(search))

    candidates = query.all()

    result = []
    for c in candidates:
        result.append({
            'id': c.id,
            'name': c.name,
            'party': c.party,
            'summary': c.background_summary,
            'connection_count': len(c.connections.all())
        })

    return jsonify(result)

@csrf.exempt
def api_candidate_detail(candidate_id):
    """API endpoint for single candidate"""
    candidate = Candidate.query.get_or_404(candidate_id)

    result = {
        'id': candidate.id,
        'name': candidate.name,
        'party': candidate.party,
        'background_summary': candidate.background_summary,
        'political_history': candidate.political_history,
        'criminal_connections': candidate.criminal_connections,
        'funding_sources': candidate.funding_sources,
        'connections': [
            {
                'id': conn.id,
                'type': conn.connection_type,
                'description': conn.description,
                'organization': conn.organization
            } for conn in candidate.connections
        ],
        'sources': [
            {
                'url': src.url,
                'description': src.description,
                'date_added': src.created_at.isoformat()
            } for src in candidate.sources
        ]
    }

    return jsonify(result)

# Module-level app for gunicorn: `gunicorn app:app`
app = create_app()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
