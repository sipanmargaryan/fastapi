import datetime

from app.helpers.database import SessionLocal
from app.routers.organization.models import UserOrganization, VerificationStatusTypes
from app.worker import celery_app


@celery_app.task(bind=True, acks_late=True)
def mark_invitation_expired(self):
    with SessionLocal() as session:
        users = (
            session.query(UserOrganization)
            .filter_by(verification_status=VerificationStatusTypes.pending)
            .all()
        )
        for user in users:
            delta = datetime.datetime.utcnow() - user.created_at
            if delta >= datetime.timedelta(days=7):
                user.verification_status = VerificationStatusTypes.expired
        session.commit()
