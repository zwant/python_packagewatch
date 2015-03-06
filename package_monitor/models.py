from package_monitor import db

class Package(db.Model):
    __tablename__ = 'packages'
    id = db.Column(db.Integer, primary_key=True)
    package_name = db.Column(db.String, unique=True)
    package_url = db.Column(db.String)
    latest_version = db.Column(db.String)
    python3_compat = db.Column(db.Boolean)
    last_updated = db.Column(db.DateTime(timezone=True))
    watchers = db.relationship("WatchedPackage", order_by="WatchedPackage.package_name", backref="package")

    def __repr__(self):
        return '<Package %s>' % self.package_name

class WatchedPackage(db.Model):
    __tablename__ = 'watched_packages'
    package_name = db.Column(db.String, db.ForeignKey('packages.package_name'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    version = db.Column(db.String)

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

