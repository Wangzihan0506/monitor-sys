 import pytest
from app import create_app
from app.exts import db
from app.models.employee import Employee, Attendance
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

def test_attendance_records_endpoint(client):
    """测试签到记录接口"""
    response = client.get('/api/attendance/records')
    # 未认证应该返回 401
    assert response.status_code == 401

def test_user_attendance_records_endpoint(client):
    """测试用户签到记录接口"""
    response = client.get('/api/attendance/records/user')
    # 未认证应该返回 401
    assert response.status_code == 401