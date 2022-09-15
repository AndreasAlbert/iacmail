import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SendingAttempt(Base):
    __tablename__ = "sending_attempts"

    message_hash = sa.Column(sa.String(64), primary_key=True)
    address = sa.Column(sa.String(64), primary_key=True)
    attempt = sa.Column(sa.Integer(), primary_key=True)

    detail = sa.Column(sa.String(64))
    successful = sa.Column(sa.Boolean())
    time = sa.Column(sa.DateTime())
