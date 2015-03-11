from package_monitor import app, db, bcrypt, models, utils
from flask import Flask
from flask.ext.testing import TestCase
import responses
from StringIO import StringIO

class BasicTest(TestCase):
    render_templates = False

    def create_app(self):
        return app

    def setUp(self):
        db.create_all()
        user = models.User(email='test@paldan.se',
                           password=bcrypt.generate_password_hash('12345'))
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_start_page_loads(self):
        self.assertStatus(self.client.get('/'), 200)

    def test_login(self):
        response = self.client.post('/login/', data=dict(email='test@paldan.se',
                                                         password='12345'))
        self.assertEquals(response.json, {'result': 'SUCCESS'})

    def test_login_wrong_password(self):
        response = self.client.post('/login/', data=dict(email='test@paldan.se',
                                                         password='123456'))
        self.assertEquals(response.json, {'result': 'INVALID_DATA'})

    def test_login_wrong_email(self):
        response = self.client.post('/login/', data=dict(email='test2@paldan.se',
                                                         password='12345'))
        self.assertEquals(response.json, {'result': 'INVALID_DATA'})

class LoggedInTest(TestCase):
    render_templates = False

    def create_app(self):
        return app

    def setUp(self):
        db.create_all()
        user = models.User(email='test@paldan.se',
                           password=bcrypt.generate_password_hash('12345'))
        db.session.add(user)
        db.session.commit()
        # Log in the user
        response = self.client.post('/login/', data=dict(email='test@paldan.se',
                                                         password='12345'))
        self.assertEquals(response.json, {'result': 'SUCCESS'})
        responses.add(responses.GET, 'https://pypi.python.org/pypi/Django/json',
                  body="""{
                            "info": {
                                "maintainer": null,
                                "docs_url": "",
                                "requires_python": null,
                                "maintainer_email": null,
                                "cheesecake_code_kwalitee_id": null,
                                "keywords": null,
                                "package_url": "http://pypi.python.org/pypi/Django",
                                "author": "Django Software Foundation",
                                "author_email": "foundation@djangoproject.com",
                                "download_url": null,
                                "platform": "UNKNOWN",
                                "version": "1.8b1",
                                "cheesecake_documentation_id": null,
                                "_pypi_hidden": false,
                                "description": "UNKNOWN",
                                "release_url": "http://pypi.python.org/pypi/Django/1.8b1",
                                "downloads": {
                                    "last_month": 380500,
                                    "last_week": 147485,
                                    "last_day": 11067
                                },
                                "_pypi_ordering": 76,
                                "requires_dist": [
                                    "bcrypt; extra == 'bcrypt'"
                                ],
                                "classifiers": [
                                    "Development Status :: 4 - Beta",
                                    "Environment :: Web Environment",
                                    "Framework :: Django",
                                    "Intended Audience :: Developers",
                                    "License :: OSI Approved :: BSD License",
                                    "Operating System :: OS Independent",
                                    "Programming Language :: Python",
                                    "Programming Language :: Python :: 2",
                                    "Programming Language :: Python :: 2.7",
                                    "Programming Language :: Python :: 3",
                                    "Programming Language :: Python :: 3.2",
                                    "Programming Language :: Python :: 3.3",
                                    "Programming Language :: Python :: 3.4",
                                    "Topic :: Internet :: WWW/HTTP",
                                    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
                                    "Topic :: Internet :: WWW/HTTP :: WSGI",
                                    "Topic :: Software Development :: Libraries :: Application Frameworks",
                                    "Topic :: Software Development :: Libraries :: Python Modules"
                                ],
                                "bugtrack_url": "",
                                "name": "Django",
                                "license": "BSD",
                                "summary": "A high-level Python Web framework that encourages rapid development and clean, pragmatic design.",
                                "home_page": "http://www.djangoproject.com/",
                                "stable_version": null,
                                "cheesecake_installability_id": null
                            }}""", 
                  status=200,
                  content_type='application/json')

        responses.add(responses.HEAD, 'https://pypi.python.org/pypi/Django/json',
                  body='', status=200,
           content_type='application/json')

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @responses.activate
    def test_package_properly_marked_as_old(self):
        response = self.client.post('/', data=dict(package_name='Django',
                                                   package_version='1.6.0'))
        user = models.User.query.filter_by(email='test@paldan.se').first()
        self.assertEqual(len(user.watched_packages), 1)
        watched_package = user.watched_packages[0]
        package = models.Package.query.filter_by(package_name='Django').first()
        self.assertIsNotNone(package)
        self.assertEqual(utils.compare_package_versions(package.latest_version, watched_package.version), 1)
        self.assertEqual(utils.compare_package_versions(watched_package.version, package.latest_version), -1)

    @responses.activate
    def test_add_package(self):
        response = self.client.post('/', data=dict(package_name='Django',
                                                   package_version='1.6.0'))
        # One head and one GET
        assert len(responses.calls) == 2
        self.assertRedirects(response, '/')

    @responses.activate
    def test_update_package(self):
        self.client.post('/', data=dict(package_name='Django',
                                        package_version='1.5.0'))
        response = self.client.post('/package/Django/', data=dict(new_package_version='1.6.0'))
        self.assertRedirects(response, '/')
        assert len(responses.calls) == 2

    @responses.activate
    def test_delete_package(self):
        self.client.post('/', data=dict(package_name='Django',
                                        package_version='1.5.0'))
        response = self.client.delete('/package/Django/')
        self.assertEquals(response.json, {'result': 'SUCCESS'})
        assert len(responses.calls) == 2

    @responses.activate
    def test_upload_file(self):
        files = {'file': (StringIO('Django==1.6.0'), 'requirements.txt')}
        response = self.client.post('/upload/', data=files)
        self.assertRedirects(response, '/')
