"""
Seed script to populate the database with test data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Candidate, Source, Connection, Submission
from datetime import datetime, timedelta, timezone
import random

def seed_data():
    """Seed the database with sample data"""
    app = create_app()

    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()

        # Sample data
        parties = ['MAS', 'COS', 'VERD', 'LIDERCIA', 'FPV', 'SANTE', 'PDC', 'ML', 'LIBRE']

        candidates = []
        parties_used = set()

        # Create candidates
        for i in range(15):
            party = random.choice(parties)
            parties_used.add(party)

            candidate = Candidate(
                name=f'Político de Ejemplo {i+1}',
                party=party,
                background_summary=f'Político boliviano de {party}',
                political_history=f'Experiencia política de más de 10 años en Bolivia, participó en múltiples elecciones.',
                criminal_connections=f'Algunas conexiones cuestionables con sectores controvertidos.',
                funding_sources=f'Financiado por diversos grupos económicos y políticos.'
            )
            candidates.append(candidate)

        db.session.add_all(candidates)
        db.session.commit()
        print(f'Created {len(candidates)} candidates')

        # Create connections for each candidate
        all_candidates = Candidate.query.all()
        for candidate in all_candidates:
            num_connections = random.randint(2, 5)
            for _ in range(num_connections):
                connection = Connection(
                    candidate_id=candidate.id,
                    connection_type=random.choice(Connection.TYPES),
                    organization=f'Organización {random.randint(1, 50)}',
                    description='Descripción detallada de la conexión',
                    verified=random.choice([True, False])
                )
                db.session.add(connection)

        db.session.commit()
        print(f'Created {Connection.query.count()} connections')

        # Create sources for each candidate
        for candidate in all_candidates:
            num_sources = random.randint(3, 6)
            for _ in range(num_sources):
                source = Source(
                    candidate_id=candidate.id,
                    url=f'https://example.com/article/{random.randint(1, 1000)}',
                    description=f'Artículo de referencia {random.randint(1, 100)}',
                    source_type=random.choice(['article', 'report', 'video', 'official_doc']),
                    scraped_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
                )
                db.session.add(source)

        db.session.commit()
        print(f'Created {Source.query.count()} sources')

        # Create submissions
        submission_types = ['tip', 'evidence', 'document']
        for i in range(10):
            candidate = random.choice(all_candidates) if random.random() > 0.3 else None

            submission = Submission(
                candidate_id=candidate.id if candidate else None,
                content=f'Tip anónima sobre actividad cuestionable de {candidate.name if candidate else "un político"}',
                source_link=f'https://example.com/evidence/{i}' if random.random() > 0.5 else None,
                source_type=random.choice(submission_types),
                is_verified=random.choice([True, False]),
                verification_status=random.choice(Submission.STATUS_CHOICES),
                is_anonymous=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))
            )
            db.session.add(submission)

        db.session.commit()
        print(f'Created {Submission.query.count()} submissions')

        # Update candidate stats
        for candidate in all_candidates:
            candidate.connection_count = Connection.query.filter_by(candidate_id=candidate.id).count()

        db.session.commit()
        print('Updated candidate connection counts')

        print('\n=== Data seeded successfully ===')
        print(f'Total candidates: {Candidate.query.count()}')
        print(f'Total sources: {Source.query.count()}')
        print(f'Total connections: {Connection.query.count()}')
        print(f'Total submissions: {Submission.query.count()}')

if __name__ == '__main__':
    seed_data()
