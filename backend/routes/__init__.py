from flask import Blueprint

# Blueprint 생성
users_bp = Blueprint('users', __name__, url_prefix='/api')
equipment_bp = Blueprint('equipment', __name__, url_prefix='/api')
assignments_bp = Blueprint('assignments', __name__, url_prefix='/api')
seals_bp = Blueprint('seals', __name__, url_prefix='/api')
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/api')
history_bp = Blueprint('history', __name__, url_prefix='/api')
imports_bp = Blueprint('imports', __name__, url_prefix='/api')
floorplan_bp = Blueprint('floorplan', __name__, url_prefix='/api')

# 각 라우트 모듈에서 사용할 수 있도록 export
__all__ = [
    'users_bp',
    'equipment_bp', 
    'assignments_bp',
    'seals_bp',
    'maintenance_bp',
    'history_bp',
    'imports_bp',
    'floorplan_bp'
]
