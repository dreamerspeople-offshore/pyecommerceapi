import unittest
from app import create_app
from flask import json

class TestUserRoutes(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_get_users(self):
        response = self.client.get('/api/users')
        self.assertEqual(response.status_code, 200)

    def test_add_user(self):
        user_data = {'name': 'John Doe', 'email': 'john@example.com'}
        response = self.client.post('/api/users', data=json.dumps(user_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)

if __name__ == "__main__":
    unittest.main()
