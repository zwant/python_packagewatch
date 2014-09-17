import sqlite3
import datetime

from package_monitor import utils
from flask import Flask, g, render_template, request, redirect, url_for, jsonify, abort
from wtforms import Form, TextField, validators


app = Flask(__name__)
app.config.from_object('package_monitor.config')


class AddPackageForm(Form):
    package_name = TextField('Package Name', [validators.Required(),
                                              validators.Length(min=1, max=50)])
    package_version = TextField('Package Version', [validators.Regexp(r'^\d{1,3}(\.\d{1,3})*$'),
                                                    validators.Length(min=1, max=10)])

class UpdatePackageForm(Form):
    new_package_version = TextField('New Package Version', [validators.Regexp(r'^\d{1,3}(\.\d{1,3})*$'),
                                                            validators.Length(min=1, max=10)])

def connect_db():
    return sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

def _delete_package(package_name):
    g.db.execute('DELETE FROM watched_packages WHERE package_name=?', [package_name])
    g.db.commit()

def _update_package_version(package_name, new_version):
    g.db.execute('UPDATE watched_packages SET package_version=? WHERE package_name=?', [new_version,
                                                                                        package_name])
    g.db.commit()

@app.route('/package/<package_name>/', methods=['DELETE', 'POST'])
def update_package(package_name):
    if request.method == 'DELETE':
        _delete_package(package_name)
        return jsonify(result='SUCCESS')
    elif request.method == 'POST':
        form = UpdatePackageForm(request.form, csrf_enabled=False)
        if form.validate():
            _update_package_version(package_name, form.new_package_version.data)
            return redirect(url_for('start_page'))
    abort(400)


@app.route('/', methods=['GET', 'POST'])
def start_page():
    form = AddPackageForm(request.form, csrf_enabled=False)
    error_msg = None
    if request.method == 'POST' and form.validate():
        # Check that the package exists
        if utils.check_if_package_exists_on_pypi(form.package_name.data):
            g.db.execute('INSERT INTO watched_packages(package_name, package_version) VALUES (?,?)', [form.package_name.data, form.package_version.data])
            g.db.commit()
            return redirect(url_for('start_page'))
        else:
            error_msg = 'No such package found on PyPI'

    all_packages = query_db('SELECT * FROM watched_packages')

    for package in all_packages:
        # Check if we have a recent version already...
        max_age = ( datetime.datetime.now() - datetime.timedelta(hours=app.config['MAX_AGE_HOURS_BEFORE_UPDATE']))
        if not package['last_updated'] or \
           ( package['last_updated'] and
             package['last_updated'] <  max_age):
            # No recent version...
            pypi_package_info = utils.get_package_info_from_pypi(package['package_name'])
            if pypi_package_info:
                package['latest_version'] = pypi_package_info['version']
                package['package_url'] = pypi_package_info['package_url']
                g.db.execute('UPDATE watched_packages SET latest_version=?, last_updated=?, package_url=? WHERE package_name=?', [package['latest_version'],
                                                                                                                                  datetime.datetime.now(),
                                                                                                                                  package['package_url'],
                                                                                                                                  package['package_name']])
                g.db.commit()
        # Latest is newer than current
        if utils.compare_package_versions(package['latest_version'], package['package_version']):
            package['is_old'] = True
        else:
            package['is_old'] = False

    return render_template('start_page.html', form=form, all_packages=all_packages, error_msg=error_msg)


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
