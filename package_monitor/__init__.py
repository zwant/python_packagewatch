import os
import sqlite3
import requests
from flask import Flask, g, render_template, request
from wtforms import Form, TextField, validators

app = Flask(__name__)

DATABASE = os.path.dirname(os.path.realpath(__file__)) + '/database.db'

class AddPackageForm(Form):
    package_name = TextField('Package Name', [validators.Required(),
                                              validators.Length(min=1, max=50)])
    package_version = TextField('Package Version', [validators.Regexp(ur'^\d{1,3}(\.\d{1,3})*$'),
                                                    validators.Length(min=1, max=10)])


def connect_db():
    return sqlite3.connect(DATABASE)

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


@app.route('/', methods=['GET', 'POST'])
def start_page():
    form = AddPackageForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        g.db.execute('INSERT INTO watched_packages(package_name, package_version) VALUES (?,?)', [form.package_name.data, form.package_version.data])
        g.db.commit()
    all_packages = query_db('SELECT * FROM watched_packages')

    for package in all_packages:
        r = requests.get('http://pypi.python.org/pypi/{0}/json'.format(package['package_name']))
        if r.status_code == requests.codes.ok:
            package['latest_version'] = r.json()['info']['version']

    return render_template('start_page.html', form=form, all_packages=all_packages)


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
