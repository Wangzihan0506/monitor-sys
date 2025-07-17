from flask import Flask, jsonify
from app import create_app

app = create_app()

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': '2024-01-01T00:00:00Z',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)