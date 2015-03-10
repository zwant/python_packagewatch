from package_monitor import db, bcrypt
import sqlalchemy as sa
from pip._vendor.packaging.version import parse, Version, LegacyVersion
import pytz
import datetime

class PipVersionType(sa.types.TypeDecorator):
    impl = sa.types.String

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return parse(value)

    def __repr__(self):
        return str(sa.String())

class Package(db.Model):
    __tablename__ = 'packages'
    id = db.Column(db.Integer, primary_key=True)
    package_name = db.Column(db.String, unique=True)
    package_url = db.Column(db.String)
    latest_version = db.Column(PipVersionType)
    python3_compat = db.Column(db.Boolean)
    last_updated = db.Column(db.DateTime(timezone=True))
    watchers = db.relationship("WatchedPackage", order_by="WatchedPackage.package_name", backref="package")

    def __repr__(self):
        return '<Package %s>' % self.package_name
    
    def populate_from_pypi_package_info(self, pypi_package_info):
        package.package_url = pypi_package_info['package_url']
        package.latest_version = pypi_package_info['version']
        package.python3_compat = pypi_package_info['python3_compat']
        package.last_updated = datetime.datetime.now(tz=pytz.utc)

class WatchedPackage(db.Model):
    __tablename__ = 'watched_packages'
    package_name = db.Column(db.String, db.ForeignKey('packages.package_name'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    version = db.Column(PipVersionType)

    def __repr__(self):
        return '<WatchedPackage %s - %s>' % (self.package_name, self.version)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    watched_packages = db.relationship("WatchedPackage", order_by="WatchedPackage.package_name", backref="user")

    def __repr__(self):
        return '<User %s, %s>' % (self.id, self.email)

    def watches_package(self, package_name):
        if WatchedPackage.query.filter_by(package_name=package_name).filter_by(user_id=self.id).first():
            return True

        else:
            return False

