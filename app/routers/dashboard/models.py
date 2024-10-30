from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.helpers.database import BaseDBModel
from app.routers.auth.models import User
from app.routers.organization.models import Organization


class Dashboard(BaseDBModel):
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship(Organization, backref="dashboard_organizations")
    deleted = Column(Boolean, default=False)
    consultant_id = Column(Integer, ForeignKey("users.id"))
    dashboard_unique_identifier = Column(String, unique=True)


class UserDashboard(BaseDBModel):
    __tablename__ = "user_dashboard"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship(User, backref="user_dashboards")
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    dashboard = relationship("Dashboard", backref="dashboards_users")
    last_viewed = Column(DateTime, default=datetime.now())
    pinned = Column(Boolean, default=False)
    pinned_date = Column(DateTime, default=datetime.now())


class Chart(BaseDBModel):
    __tablename__ = "chart"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    config = Column(JSONB)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))
    dashboard = relationship("Dashboard", backref="chart")
    consultant_id = Column(Integer, ForeignKey("users.id"))
    dashboard_chart_unique_identifier = Column(String)


@event.listens_for(Dashboard, "before_update")
@event.listens_for(UserDashboard, "before_update")
@event.listens_for(Chart, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
