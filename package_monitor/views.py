import datetime
import pytz

from package_monitor import utils, models, app, db
from flask import render_template, request, redirect, url_for, jsonify, abort, session, Blueprint
from wtforms import Form, TextField, validators
from werkzeug import secure_filename


blueprint = Blueprint('views', __name__)

class AddPackageForm(Form):
    package_name = TextField('Package Name', [validators.Required(),
                                              validators.Length(min=1, max=50)])
    package_version = TextField('Package Version', [validators.Regexp(r'^\d{1,3}(\.\d{1,3})*$'),
                                                    validators.Length(min=1, max=10)])

class UpdatePackageForm(Form):
    new_package_version = TextField('New Package Version', [validators.Regexp(r'^\d{1,3}(\.\d{1,3})*$'),
                                                            validators.Length(min=1, max=10)])

class RegistrationForm(Form):
    email = TextField('Email', [validators.Required()])
    password = TextField('Password', [validators.Required()])

class LoginForm(Form):
    email = TextField('Email', [validators.Required()])
    password = TextField('Password', [validators.Required()])

def _delete_package(user, package_name):
    package_to_delete = models.WatchedPackage.query \
           .join(models.User) \
           .filter(models.User.email == user) \
           .filter(models.WatchedPackage.package_name == package_name) \
           .first()
    if package_to_delete:
        db.session.delete(package_to_delete)
        db.session.commit()
    else:
        db.session.rollback()

def _update_package_version(user, package_name, new_version):
    package = models.WatchedPackage.query \
                                   .join(models.User) \
                                   .filter(models.User.email == user) \
                                   .filter(models.WatchedPackage.package_name == package_name) \
                                   .first()
    if package:
        package.version = new_version
        db.session.commit()
    else:
        db.session.rollback()

def _check_python3_compat(info):
    if "classifiers" in info and "Programming Language :: Python :: 3" in info['classifiers']:
        return True
    return False

def _add_package(user, package_name, version):
    # Check that the package exists
    if utils.check_if_package_exists_on_pypi(package_name):
        package = models.Package.query.filter_by(package_name=package_name).first()
        # New package that we have never seen before :)
        if not package:
            package = models.Package(package_name=package_name)
            pypi_package_info = utils.get_package_info_from_pypi(package_name)
            package.package_url = pypi_package_info['package_url']
            package.latest_version = pypi_package_info['version']
            package.last_updated = datetime.datetime.now(tz=pytz.utc)
            db.session.add(package)
        watched_package = models.WatchedPackage(package_name=package.package_name,
                                                version=version)
        user.watched_packages.append(watched_package)
        db.session.commit()

        return True
    else:
        return None

@blueprint.route('/package/<package_name>/', methods=['DELETE', 'POST'])
def update_package(package_name):
    if request.method == 'DELETE':
        _delete_package(session['user_email'], package_name)
        return jsonify(result='SUCCESS')
    elif request.method == 'POST':
        form = UpdatePackageForm(request.form, csrf_enabled=False)
        if form.validate():
            _update_package_version(session['user_email'], package_name, form.new_package_version.data)
            return redirect(url_for('views.start_page'))
    db.session.rollback()
    abort(400)

@blueprint.route('/register/', methods=['POST'])
def register():
    form = RegistrationForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        existing_user = models.User.query.filter_by(email=form.email.data).first()

        if existing_user:
            db.session.rollback()
            return jsonify(result='INVALID_EMAIL')
        else:
            new_user = models.User(email=form.email.data,
                                   password=form.password.data)
            db.session.add(new_user)
            db.session.commit()
            session['user_email'] = form.email.data
            return jsonify(result='SUCCESS')

    return jsonify(result='INVALID_DATA')

@blueprint.route('/login/', methods=['POST'])
def login():
    form = LoginForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        user = models.User.query.filter_by(email=form.email.data).first()

        if user and user.password == form.password.data:
            session['user_email'] = form.email.data
            return jsonify(result='SUCCESS')
        else:
            return jsonify(result='INVALID_DATA')

    return jsonify(result='INVALID_DATA')

@blueprint.route('/logout/', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('views.start_page'))

@blueprint.route('/', methods=['GET', 'POST'])
def start_page():
    form = AddPackageForm(request.form, csrf_enabled=False)
    error_msg = None
    user = None
    if 'user_email' in session:
        user = models.User.query.filter_by(email=session['user_email']).first()

    if request.method == 'POST' and form.validate():
        if _add_package(user, form.package_name.data, form.package_version.data):
            return redirect(url_for('views.start_page'))
        else:
            error_msg = 'No such package found on PyPI'

    to_return = []

    if user:
        for watched_package in user.watched_packages:
            package = watched_package.package
            # Check if we have a recent version already...
            max_age = (datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(hours=app.config['MAX_AGE_HOURS_BEFORE_UPDATE']))
            if not package.last_updated or \
               (  package.last_updated and
                  package.last_updated <  max_age):
                # No recent version...
                pypi_package_info = utils.get_package_info_from_pypi(package.package_name)
                if pypi_package_info:
                    package.latest_version = pypi_package_info['version']
                    package.package_url = pypi_package_info['package_url']
                    package.python3_compat = _check_python3_compat(pypi_package_info)
                    package.last_updated = datetime.datetime.now(tz=pytz.utc)

            to_return_package = {'package_name': package.package_name,
                                 'latest_version': package.latest_version,
                                 'package_url': package.package_url,
                                 'python3_compat': package.python3_compat,
                                 'version': watched_package.version}
            # Latest is newer than current
            watched_package.latest_version = package.latest_version
            if utils.compare_package_versions(package.latest_version, watched_package.version):
                to_return_package['is_old'] = True
            else:
                to_return_package['is_old'] = False

            to_return.append(to_return_package)

    db.session.commit()
    return render_template('start_page.html', form=form, all_packages=to_return, logged_in='user_email' in session, error_msg=error_msg)

ALLOWED_EXTENSIONS = set(['txt'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@blueprint.route('/upload/', methods=['POST'])
def upload_file():
    if 'user_email' in session:
        user = models.User.query.filter_by(email=session['user_email']).first()

        file = request.files['file']
        if file and allowed_file(file.filename):
            for line in file.readlines():
                (package, version) = utils.parse_line_from_requirements(line.decode('utf-8'))
                if not _add_package(user, package, version):
                    print('Unable to find package: {0}'.format(package))

    return redirect(url_for('views.start_page'))


