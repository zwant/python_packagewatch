import datetime
import pytz

from package_monitor import utils, models, app, db, bcrypt
from flask import render_template, request, redirect, url_for, jsonify, abort, session, Blueprint
from wtforms import Form, TextField, validators
from werkzeug import secure_filename


blueprint = Blueprint('views', __name__)

class AddPackageForm(Form):
    package_name = TextField('Package Name', [validators.Required(),
                                              validators.Length(min=1, max=50)])
    package_version = TextField('Package Version', [validators.Length(min=1, max=10)])

class UpdatePackageForm(Form):
    new_package_version = TextField('New Package Version', [validators.Length(min=1, max=10)])

class RegistrationForm(Form):
    email = TextField('Email', [validators.Required()])
    password = TextField('Password', [validators.Required()])

class LoginForm(Form):
    email = TextField('Email', [validators.Required()])
    password = TextField('Password', [validators.Required()])



@blueprint.route('/package/<package_name>/', methods=['DELETE', 'POST'])
def update_package(package_name):
    if request.method == 'DELETE':
        utils.delete_package(session['user_email'], package_name)
        return jsonify(result='SUCCESS')
    elif request.method == 'POST':
        form = UpdatePackageForm(request.form, csrf_enabled=False)
        if form.validate():
            utils.update_package_version(session['user_email'], package_name, form.new_package_version.data)
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
                                   password=bcrypt.generate_password_hash(form.password.data))
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

        if user and bcrypt.check_password_hash(user.password, form.password.data):
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

    if request.method == 'POST' and form.validate() and user:
        if utils.add_package(user, form.package_name.data, form.package_version.data):
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
                    package = models.Package.from_pypi_package_info(pypi_package_info)
                    db.session.merge(package)

            to_return_package = {'package_name': package.package_name,
                                 'latest_version': package.latest_version,
                                 'package_url': package.package_url,
                                 'python3_compat': package.python3_compat,
                                 'version': str(watched_package.version)}
            # Latest is newer than current
            watched_package.latest_version = package.latest_version
            if utils.compare_package_versions(package.latest_version, watched_package.version) < 0:
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
                if not line:
                    continue
                (package, version) = utils.parse_line_from_requirements(line.decode('utf-8'))
                if package and version and not user.watches_package(package):
                    if not utils.add_package(user, package, version):
                        print('Unable to find package: {0}'.format(package))

    return redirect(url_for('views.start_page'))


