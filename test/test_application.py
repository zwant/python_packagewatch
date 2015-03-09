from package_monitor import app, db, bcrypt, models
from flask import Flask
from flask.ext.testing import TestCase

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

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_add_package(self):
        response = self.client.post('/', data=dict(package_name='Django',
                                                   package_version='1.6.0'))
        self.assertRedirects(response, '/')
        
    def test_update_package(self):
        self.client.post('/', data=dict(package_name='Django',
                                        package_version='1.5.0'))
        response = self.client.post('/package/Django/', data=dict(new_package_version='1.6.0'))
        self.assertRedirects(response, '/')

    def test_update_package(self):
        self.client.post('/', data=dict(package_name='Django',
                                        package_version='1.5.0'))
        response = self.client.delete('/package/Django/')
        self.assertEquals(response.json, {'result': 'SUCCESS'})
        
