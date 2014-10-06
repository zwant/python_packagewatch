from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('package_monitor.config')
db = SQLAlchemy(app)

if __name__ == '__main__':
    from package_monitor import models
    from views import blueprint
    app.register_blueprint(blueprint)

    app.run(host='0.0.0.0', debug=True)
