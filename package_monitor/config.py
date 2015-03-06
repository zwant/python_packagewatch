import os
import urlparse

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

SQLALCHEMY_DATABASE_URI = url.geturl()
DEBUG = True
MAX_AGE_HOURS_BEFORE_UPDATE = 6
SECRET_KEY = 'svante_is_awesome'
SESSION_COOKIE_NAME = 'python_packagewatch'