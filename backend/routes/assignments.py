from flask import request, jsonify
from datetime import datetime
from . import assignments_bp
from database_models import db, Equipment, User, Assignment
from utils import log_change


@assignments_bp.route('/assignments', methods=['GET'])
def get_all_assignments():
    """전체 할당 이력 조회"""
    assignments = Assignment.query.order_by(Assignment.assignment_date.desc()).all()
    return jsonify([assignment.to_dict(include_details=True) for assignment in assignments])


@assignments_bp.route('/assignments/active', methods=['GET'])
def get_active_assignments():
    """현재 사용중인 할당 목록"""
    assignments = Assignment.query.filter_by(status='사용중').all()
    return jsonify([assignment.to_dict(include_details=True) for assignment in assignments])


@assignments_bp.route('/assignments', methods=['POST'])
def create_assignment():
    """장비 할당 (자산번호로 빠른 할당)"""
    data = request.json
    
    # 자산번호로 장비 찾기
    equipment = Equipment.query.filter_by(asset_number=data['asset_number']).first()
    if not equipment:
        return jsonify({'error': '해당 자산번호의 장비를 찾을 수 없습니다.'}), 404
    
    # 이미 할당되어 있는지 확인
    existing_assignment = Assignment.query.filter_by(
        equipment_id=equipment.id,
        status='사용중'
    ).first()
    
    if existing_assignment:
        return jsonify({'error': '이미 사용중인 장비입니다.'}), 400
    
    # 사용자 찾기
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
    
    # 할당 생성
    assignment = Assignment(
        equipment_id=equipment.id,
        user_id=data['user_id'],
        assignment_date=datetime.strptime(data.get('assignment_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
        status='사용중',
        reason=data.get('reason'),
        assigned_by=data.get('assigned_by')
    )
    
    # 장비 상태 변경
    equipment.status = '사용중'
    
    db.session.add(assignment)
    db.session.commit()
    
    # 이력 기록
    log_change('assignment', assignment.id, '장비 할당', '할당',
               None, f"{user.name} → {equipment.asset_number}",
               data.get('assigned_by'), data.get('reason'))
    
    return jsonify(assignment.to_dict(include_details=True)), 201


@assignments_bp.route('/assignments/<int:id>/return', methods=['PUT'])
def return_assignment(id):
    """장비 반납"""
    assignment = Assignment.query.get_or_404(id)
    data = request.json
    
    if assignment.status == '반납':
        return jsonify({'error': '이미 반납된 장비입니다.'}), 400
    
    assignment.status = '반납'
    assignment.return_date = datetime.strptime(
        data.get('return_date', datetime.now().strftime('%Y-%m-%d')), 
        '%Y-%m-%d'
    ).date()
    
    # 장비 상태 변경
    equipment = Equipment.query.get(assignment.equipment_id)
    equipment.status = '사용가능'
    
    db.session.commit()
    
    # 이력 기록
    user = User.query.get(assignment.user_id)
    log_change('assignment', assignment.id, '장비 반납', '반납',
               f"{user.name} → {equipment.asset_number}", None,
               data.get('assigned_by'), data.get('reason'))
    
    return jsonify(assignment.to_dict(include_details=True))


@assignments_bp.route('/assignments/user/<int:user_id>', methods=['GET'])
def get_user_assignments(user_id):
    """특정 사용자의 할당 이력"""
    assignments = Assignment.query.filter_by(user_id=user_id).order_by(Assignment.assignment_date.desc()).all()
    return jsonify([assignment.to_dict(include_details=True) for assignment in assignments])


@assignments_bp.route('/assignments/equipment/<int:equipment_id>', methods=['GET'])
def get_equipment_assignments(equipment_id):
    """특정 장비의 할당 이력"""
    assignments = Assignment.query.filter_by(equipment_id=equipment_id).order_by(Assignment.assignment_date.desc()).all()
    return jsonify([assignment.to_dict(include_details=True) for assignment in assignments])