"""
DPolitica - Main Flask Application
Political Transparency Platform for Bolivia
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Candidate, Source, Submission, Connection
from datetime import datetime
from functools import wraps

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'change-this-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dpolitica.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    @app.context_processor
    def now():
        return {'now': datetime.utcnow().strftime('%Y-%m-%d')}

    with app.app_context():
        db.create_all()

    # Register routes
    app.add_url_rule('/', view_func=index)
    app.add_url_rule('/candidates', view_func=candidates)
    app.add_url_rule('/candidates/<int:candidate_id>', view_func=candidate_detail)
    app.add_url_rule('/submit', view_func=submit, methods=['GET', 'POST'])
    app.add_url_rule('/sources', view_func=sources)
    app.add_url_rule('/api/candidates', view_func=api_candidates, methods=['GET', 'POST'])
    app.add_url_rule('/api/candidates/<int:candidate_id>', view_func=api_candidate_detail, methods=['GET'])

    return app

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple admin check - expand as needed
        return f(*args, **kwargs)
    return decorated_function

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

    if min_connections:
        query = query.filter(Candidate.connection_count >= min_connections)

    candidates = query.order_by(Candidate.name.asc()).all()

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

def submit():
    """Anonymous submission form for tips and data"""
    if request.method == 'POST':
        candidate_name = request.form.get('candidate_name', '').strip()
        content = request.form.get('content', '').strip()
        source_link = request.form.get('source_link', '').strip()
        source_type = request.form.get('source_type', 'tip')

        if not content:
            flash('Please provide information.', 'error')
            return redirect(url_for('submit'))

        # Find or create candidate
        candidate = None
        if candidate_name:
            candidate = Candidate.query.filter_by(name=candidate_name).first()
            if not candidate:
                # Auto-create candidate entry
                candidate = Candidate(name=candidate_name)
                db.session.add(candidate)
                db.session.flush()

        # Create submission
        submission = Submission(
            candidate_id=candidate.id if candidate else None,
            content=content,
            source_link=source_link if source_link else None,
            source_type=source_type,
            is_verified=False
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

def api_candidates():
    """API endpoint for candidates"""
    # POST: Create new candidate
    if request.method == 'POST':
        data = request.get_json()

        candidate = Candidate(
            name=data.get('name', 'Unknown'),
            party=data.get('party', ''),
            background_summary=data.get('background_summary', ''),
            political_history=data.get('political_history', ''),
            criminal_connections=data.get('criminal_connections', ''),
            funding_sources=data.get('funding_sources', '')
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

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
