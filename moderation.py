from database import db, User
from datetime import datetime, timedelta

def mute_user(target_id, muter_id, duration_minutes, reason):
    user = User.query.get(target_id)
    if user:
        user.muted_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        user.muted_reason = reason
        user.muted_by_id = muter_id
        db.session.commit()

def promote_user(target_id, new_role):
    user = User.query.get(target_id)
    if user:
        user.role = new_role
        db.session.commit()
