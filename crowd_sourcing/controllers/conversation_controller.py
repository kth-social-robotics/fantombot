import datetime

from fantom_util.database import db_session
from fantom_util.database.models import Rating, RatingUtteranceRow
from sqlalchemy.orm import joinedload


def get_rating(rating_id):
    return db_session.query(Rating).get(rating_id)


def get_ratings(start_time, end_time):
    if not end_time:
        end_time, = db_session.query(Rating.start_time).filter(Rating.start_time.isnot(None)).order_by(Rating.start_time.desc()).first()

    if not start_time:
        start_time = (end_time - datetime.timedelta(days=1)).replace(hour=0, minute=0)

    return db_session.query(Rating) \
        .filter(Rating.start_time >= start_time, Rating.start_time <= end_time)\
        .order_by(Rating.start_time.desc())\
        .all()
