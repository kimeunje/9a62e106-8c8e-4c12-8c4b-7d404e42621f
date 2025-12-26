from flask import request, jsonify
from . import users_bp
from database_models import db, User, Assignment
from utils import log_change


@users_bp.route('/users', methods=['GET'])
def get_all_users():
    """전체 사용자 목록 조회"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


@users_bp.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    """특정 사용자 조회"""
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())


@users_bp.route('/users', methods=['POST'])
def create_user():
    """사용자 등록"""
    data = request.json
    
    user = User(
        name=data['name'],
        department=data['department'],
        location=data['location'],
        phone=data.get('phone'),
        email=data.get('email')
    )
    
    db.session.add(user)
    db.session.commit()
    
    log_change('user', user.id, '사용자 등록', '신규 사용자', None, 
               f"{user.name} ({user.department})", data.get('changed_by'))
    
    return jsonify(user.to_dict()), 201


@users_bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    """사용자 정보 수정"""
    user = User.query.get_or_404(id)
    data = request.json
    
    changes = {}
    field_mapping = {
        'name': '이름',
        'department': '부서',
        'location': '위치',
        'phone': '전화번호',
        'email': '이메일'
    }
    
    for field, korean_name in field_mapping.items():
        if field in data:
            old_value = getattr(user, field)
            new_value = data[field]
            if old_value != new_value:
                changes[korean_name] = (old_value, new_value)
                setattr(user, field, new_value)
    
    db.session.commit()
    
    for field_name, (old_val, new_val) in changes.items():
        log_change('user', id, '사용자 정보변경', field_name, str(old_val), 
                   str(new_val), data.get('changed_by'), data.get('reason'))
    
    return jsonify(user.to_dict())


@users_bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    """사용자 삭제"""
    user = User.query.get_or_404(id)
    
    active_assignments = Assignment.query.filter_by(user_id=id, status='사용중').count()
    if active_assignments > 0:
        return jsonify({'error': '사용중인 장비가 있어 삭제할 수 없습니다.'}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': '삭제되었습니다'}), 200


@users_bp.route('/users/search', methods=['GET'])
def search_users():
    """사용자 검색"""
    query = User.query
    
    name = request.args.get('name')
    department = request.args.get('department')
    location = request.args.get('location')
    
    if name:
        query = query.filter(User.name.like(f'%{name}%'))
    if department:
        query = query.filter(User.department.like(f'%{department}%'))
    if location:
        query = query.filter(User.location.like(f'%{location}%'))
    
    users = query.all()
    return jsonify([user.to_dict() for user in users])