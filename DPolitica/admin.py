"""
DPolitica - Admin Panel Blueprint
All admin routes, session-based auth, action logging.
"""

import os
from functools import wraps
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Candidate, Source, Connection, Submission, AdminLog

admin_bp = Blueprint('admin', __name__, url_prefix='/admin',
                     template_folder='templates/admin')

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def admin_required(f):
    """Decorator: redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_authenticated'):
            flash('Debes iniciar sesión para acceder al panel.', 'error')
            return redirect(url_for('admin.login', next=request.path))
        return f(*args, **kwargs)
    return decorated


def log_action(action, details='', target_type=None, target_id=None):
    """Helper – persist an admin action to the log."""
    entry = AdminLog(
        action=action,
        details=details,
        target_type=target_type,
        target_id=target_id,
    )
    db.session.add(entry)
    db.session.commit()

# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_authenticated'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        expected = os.environ.get('ADMIN_PASSWORD', '')
        if password and expected and password == expected:
            session['admin_authenticated'] = True
            log_action('admin_login', 'Inicio de sesión exitoso')
            flash('Bienvenido al panel de administración.', 'success')
            next_url = request.args.get('next', url_for('admin.dashboard'))
            return redirect(next_url)
        flash('Contraseña incorrecta.', 'error')

    return render_template('login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_authenticated', None)
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('admin.login'))

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin_bp.route('/')
@admin_required
def dashboard():
    pending = Submission.query.filter_by(verification_status='pending').count()
    under_review = Submission.query.filter_by(verification_status='under_review').count()
    total_candidates = Candidate.query.count()
    unverified_connections = Connection.query.filter_by(verified=False).count()
    total_sources = Source.query.count()
    recent_logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(15).all()

    return render_template('dashboard.html',
                         pending=pending,
                         under_review=under_review,
                         total_candidates=total_candidates,
                         unverified_connections=unverified_connections,
                         total_sources=total_sources,
                         recent_logs=recent_logs)

# ---------------------------------------------------------------------------
# Submissions management
# ---------------------------------------------------------------------------

@admin_bp.route('/submissions')
@admin_required
def submissions():
    status_filter = request.args.get('status', 'pending')
    if status_filter == 'all':
        subs = Submission.query.order_by(Submission.created_at.desc()).all()
    else:
        subs = Submission.query.filter_by(verification_status=status_filter)\
                .order_by(Submission.created_at.desc()).all()
    return render_template('submissions.html', submissions=subs, status_filter=status_filter)


@admin_bp.route('/submissions/<int:sub_id>/update', methods=['POST'])
@admin_required
def update_submission(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    new_status = request.form.get('status', '')
    notes = request.form.get('notes', '').strip()

    if new_status in Submission.STATUS_CHOICES:
        old_status = sub.verification_status
        sub.verification_status = new_status
        sub.is_verified = (new_status == 'verified')
        sub.verification_notes = notes
        sub.reviewed_at = datetime.utcnow()
        sub.reviewed_by = 'admin'
        db.session.commit()
        log_action('submission_status_changed',
                   f'Denuncia #{sub.id}: {old_status} → {new_status}',
                   target_type='submission', target_id=sub.id)
        flash(f'Denuncia #{sub.id} actualizada a "{new_status}".', 'success')
    else:
        flash('Estado inválido.', 'error')

    return redirect(url_for('admin.submissions', status=request.args.get('status', 'pending')))

# ---------------------------------------------------------------------------
# Candidate management
# ---------------------------------------------------------------------------

@admin_bp.route('/candidates')
@admin_required
def candidates_list():
    cands = Candidate.query.order_by(Candidate.name.asc()).all()
    return render_template('candidates.html', candidates=cands)


@admin_bp.route('/candidates/new', methods=['GET', 'POST'])
@admin_required
def candidate_new():
    if request.method == 'POST':
        c = Candidate(
            name=request.form.get('name', '').strip()[:200],
            party=request.form.get('party', '').strip()[:200],
            background_summary=request.form.get('background_summary', '').strip(),
            political_history=request.form.get('political_history', '').strip(),
            criminal_connections=request.form.get('criminal_connections', '').strip(),
            funding_sources=request.form.get('funding_sources', '').strip(),
        )
        if not c.name:
            flash('El nombre es obligatorio.', 'error')
            return render_template('candidate_edit.html', candidate=None)
        db.session.add(c)
        db.session.commit()
        log_action('candidate_created', f'Candidato creado: {c.name}',
                   target_type='candidate', target_id=c.id)
        flash(f'Candidato "{c.name}" creado.', 'success')
        return redirect(url_for('admin.candidates_list'))
    return render_template('candidate_edit.html', candidate=None)


@admin_bp.route('/candidates/<int:cid>/edit', methods=['GET', 'POST'])
@admin_required
def candidate_edit(cid):
    c = Candidate.query.get_or_404(cid)
    if request.method == 'POST':
        c.name = request.form.get('name', c.name).strip()[:200]
        c.party = request.form.get('party', '').strip()[:200]
        c.background_summary = request.form.get('background_summary', '').strip()
        c.political_history = request.form.get('political_history', '').strip()
        c.criminal_connections = request.form.get('criminal_connections', '').strip()
        c.funding_sources = request.form.get('funding_sources', '').strip()
        db.session.commit()
        log_action('candidate_updated', f'Candidato actualizado: {c.name}',
                   target_type='candidate', target_id=c.id)
        flash(f'Candidato "{c.name}" actualizado.', 'success')
        return redirect(url_for('admin.candidates_list'))
    return render_template('candidate_edit.html', candidate=c)


@admin_bp.route('/candidates/<int:cid>/delete', methods=['POST'])
@admin_required
def candidate_delete(cid):
    c = Candidate.query.get_or_404(cid)
    name = c.name
    db.session.delete(c)
    db.session.commit()
    log_action('candidate_deleted', f'Candidato eliminado: {name}',
               target_type='candidate', target_id=cid)
    flash(f'Candidato "{name}" eliminado.', 'success')
    return redirect(url_for('admin.candidates_list'))

# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

@admin_bp.route('/connections')
@admin_required
def connections_list():
    conns = Connection.query.order_by(Connection.id.desc()).all()
    cands = Candidate.query.order_by(Candidate.name.asc()).all()
    return render_template('connections.html', connections=conns, candidates=cands,
                         connection_types=Connection.TYPES)


@admin_bp.route('/connections/add', methods=['POST'])
@admin_required
def connection_add():
    candidate_id = request.form.get('candidate_id', type=int)
    if not candidate_id or not Candidate.query.get(candidate_id):
        flash('Candidato inválido.', 'error')
        return redirect(url_for('admin.connections_list'))

    conn = Connection(
        candidate_id=candidate_id,
        connection_type=request.form.get('connection_type', 'other'),
        organization=request.form.get('organization', '').strip()[:200],
        description=request.form.get('description', '').strip(),
        verified='verified' in request.form,
    )
    db.session.add(conn)
    db.session.commit()
    log_action('connection_added',
               f'Conexión "{conn.connection_type}" añadida a candidato #{candidate_id}',
               target_type='connection', target_id=conn.id)
    flash('Conexión añadida.', 'success')
    return redirect(url_for('admin.connections_list'))


@admin_bp.route('/connections/<int:conn_id>/verify', methods=['POST'])
@admin_required
def connection_verify(conn_id):
    conn = Connection.query.get_or_404(conn_id)
    conn.verified = not conn.verified
    db.session.commit()
    status = 'verificada' if conn.verified else 'des-verificada'
    log_action('connection_verified',
               f'Conexión #{conn.id} {status}',
               target_type='connection', target_id=conn.id)
    flash(f'Conexión #{conn.id} {status}.', 'success')
    return redirect(url_for('admin.connections_list'))

# ---------------------------------------------------------------------------
# Source management
# ---------------------------------------------------------------------------

@admin_bp.route('/sources')
@admin_required
def sources_list():
    srcs = Source.query.order_by(Source.created_at.desc()).all()
    cands = Candidate.query.order_by(Candidate.name.asc()).all()
    return render_template('sources.html', sources=srcs, candidates=cands)


@admin_bp.route('/sources/add', methods=['POST'])
@admin_required
def source_add():
    candidate_id = request.form.get('candidate_id', type=int)
    if not candidate_id or not Candidate.query.get(candidate_id):
        flash('Candidato inválido.', 'error')
        return redirect(url_for('admin.sources_list'))

    url = request.form.get('url', '').strip()[:500]
    if not url:
        flash('La URL es obligatoria.', 'error')
        return redirect(url_for('admin.sources_list'))

    src = Source(
        candidate_id=candidate_id,
        url=url,
        description=request.form.get('description', '').strip()[:500],
        source_type=request.form.get('source_type', 'article'),
    )
    db.session.add(src)
    db.session.commit()
    log_action('source_added',
               f'Fuente añadida a candidato #{candidate_id}: {url[:60]}',
               target_type='source', target_id=src.id)
    flash('Fuente añadida.', 'success')
    return redirect(url_for('admin.sources_list'))
