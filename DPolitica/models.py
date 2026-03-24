"""
DPolitica - Database Models
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Candidate(db.Model):
    """Political candidate profiles"""

    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    party = db.Column(db.String(200), index=True)

    # Background and history
    background_summary = db.Column(db.Text)  # Short summary for listings
    political_history = db.Column(db.Text)  # Full political background
    criminal_connections = db.Column(db.Text)  # Alleged criminal ties
    funding_sources = db.Column(db.Text)  # Who funds them

    # Connection count for quick stats
    connection_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sources = db.relationship('Source', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    connections = db.relationship('Connection', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Candidate {self.name} ({self.party})>'


class Source(db.Model):
    """External sources for candidate information"""

    __tablename__ = 'sources'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500))  # Brief description of what this source is
    source_type = db.Column(db.String(50), default='article')  # article, report, video, official_doc, etc.
    scraped_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Source {self.url}>'


class Connection(db.Model):
    """Connections between candidates and organizations/people"""

    __tablename__ = 'connections'

    # Connection types
    TYPES = ['political_associate', 'family_member', 'business_partner',
             'criminal_organization', 'narcotics', 'lobbying', 'financial_backer',
             'party_official', 'campaign_contributor', 'other']

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    connection_type = db.Column(db.String(50), nullable=False)
    organization = db.Column(db.String(200))  # Organization/person they're connected to
    description = db.Column(db.Text)  # Details about the connection
    verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Connection {self.connection_type}: {self.organization}>'


class Submission(db.Model):
    """User-submitted information (tips, whistleblowing)"""

    __tablename__ = 'submissions'

    STATUS_CHOICES = ['pending', 'under_review', 'verified', 'rejected', 'partially_verified']

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    source_link = db.Column(db.String(500))  # Link to source if available
    source_type = db.Column(db.String(50), default='tip')  # tip, evidence, document, etc.

    # Verification status
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(50), default='pending')
    verification_notes = db.Column(db.Text)  # For admin notes on verification

    # Anonymity
    is_anonymous = db.Column(db.Boolean, default=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.String(100))  # Admin who reviewed

    def __repr__(self):
        return f'<Submission {self.verification_status}: {self.content[:50]}>'
