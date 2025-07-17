 import pytest
from app import create_app
from app.exts import db
from app.models.user import User

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_user_registration(client):
    """测试用户注册"""
    response = client.post('/api/auth/register/', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'sliderVerified': True
    })
    assert response.status_code in [200, 201]

def test_user_login(client):
    """测试用户登录"""
    # 先注册用户
    client.post('/api/auth/register/', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'sliderVerified': True
    })
    
    # 测试登录
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123',
        'sliderVerified': True
    })
    assert response.status_code == 200

def test_protected_endpoint_without_auth(client):
    """测试未认证访问受保护接口"""
    response = client.get('/api/users')
    assert response.status_code == 401