from flask import Flask
from flask_cors import CORS
from config import Config
from database_models import db

# Blueprint 임포트
from routes.users import users_bp
from routes.equipment import equipment_bp
from routes.assignments import assignments_bp
from routes.seals import seals_bp
from routes.maintenance import maintenance_bp
from routes.history import history_bp
from routes.imports import imports_bp
from routes.floorplan import floorplan_bp


def create_app(config_class=Config):
    """애플리케이션 팩토리"""
    app = Flask(__name__)
    
    # 설정 적용
    app.config.from_object(config_class)
    
    # 확장 초기화
    CORS(app)
    db.init_app(app)
    
    # Blueprint 등록
    app.register_blueprint(users_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(seals_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(imports_bp)
    app.register_blueprint(floorplan_bp)
    
    # 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
    
    return app


# 애플리케이션 인스턴스 생성
app = create_app()


# 헬스 체크 엔드포인트
@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'healthy', 'message': '전산장비 관리 시스템 정상 작동 중'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
