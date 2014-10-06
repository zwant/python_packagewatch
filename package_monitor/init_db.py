import sys
import psycopg2
from package_monitor import models
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from flask import Flask


app = Flask('__name__')
app.config.from_object('package_monitor.config')

def create_user_and_db(db_user):
    con = psycopg2.connect(dbname='postgres', user=db_user, host='localhost')
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute("select datname from pg_database where datname='packagewatch'")
    if cur.fetchone():
        print('Database already created, initializing schema!')
        con.close()
        return
    cur.execute('CREATE USER packagewatch')
    cur.execute('CREATE DATABASE packagewatch OWNER packagewatch')
    con.close()


def init_db(db_user):
    models.db.drop_all()
    models.db.create_all()

    models.db.session.commit()

    print('Done!')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please specify a super-user role for the database')
        sys.exit(1)
    models.db.init_app(app)
    create_user_and_db(sys.argv[1])
    with app.app_context():
        init_db(sys.argv[1])
