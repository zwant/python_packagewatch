from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('package_monitor.config')
db = SQLAlchemy(app)

from views import blueprint
app.register_blueprint(blueprint)


if __name__ == '__main__':

    app.run(host='0.0.0.0', debug=True)
