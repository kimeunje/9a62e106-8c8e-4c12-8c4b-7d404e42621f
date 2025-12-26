from flask import request, jsonify
from datetime import datetime
from . import maintenance_bp
from database_models import db, Equipment, MaintenanceLog, Assignment


@maintenance_bp.route('/maintenance-logs', methods=['GET'])
def get_all_maintenance_logs():
    """전체 수리/점검 이력"""
    query = MaintenanceLog.query
    
    maintenance_type = request.args.get('maintenance_type')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if maintenance_type:
        query = query.filter(MaintenanceLog.maintenance_type == maintenance_type)
    if status:
        query = query.filter(MaintenanceLog.status == status)
    if start_date:
        query = query.filter(MaintenanceLog.maintenance_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(MaintenanceLog.maintenance_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    logs = query.order_by(MaintenanceLog.maintenance_date.desc()).all()
    return jsonify([log.to_dict(include_equipment=True) for log in logs])


@maintenance_bp.route('/maintenance-logs', methods=['POST'])
def create_maintenance_log():
    """수리/점검 이력 등록"""
    data = request.json
    
    log = MaintenanceLog(
        equipment_id=data['equipment_id'],
        maintenance_date=datetime.strptime(data['maintenance_date'], '%Y-%m-%d').date(),
        maintenance_type=data['maintenance_type'],
        description=data['description'],
        technician=data.get('technician'),
        cost=data.get('cost'),
        status=data.get('status', '완료'),
        notes=data.get('notes'),
        created_by=data.get('created_by')
    )
    
    db.session.add(log)
    
    # 수리중이면 장비 상태 변경
    if data['maintenance_type'] == '수리' and data.get('status') != '완료':
        equipment = Equipment.query.get(data['equipment_id'])
        if equipment:
            equipment.status = '수리중'
    
    db.session.commit()
    
    return jsonify(log.to_dict(include_equipment=True)), 201


@maintenance_bp.route('/maintenance-logs/<int:id>', methods=['GET'])
def get_maintenance_log(id):
    """특정 수리/점검 이력 조회"""
    log = MaintenanceLog.query.get_or_404(id)
    return jsonify(log.to_dict(include_equipment=True))


@maintenance_bp.route('/maintenance-logs/<int:id>', methods=['PUT'])
def update_maintenance_log(id):
    """수리/점검 이력 수정"""
    log = MaintenanceLog.query.get_or_404(id)
    data = request.json
    
    if 'maintenance_date' in data:
        log.maintenance_date = datetime.strptime(data['maintenance_date'], '%Y-%m-%d').date()
    if 'maintenance_type' in data:
        log.maintenance_type = data['maintenance_type']
    if 'description' in data:
        log.description = data['description']
    if 'technician' in data:
        log.technician = data['technician']
    if 'cost' in data:
        log.cost = data['cost']
    if 'status' in data:
        log.status = data['status']
        # 완료되면 장비 상태 변경
        if data['status'] == '완료':
            equipment = Equipment.query.get(log.equipment_id)
            current_assignment = Assignment.query.filter_by(
                equipment_id=equipment.id, 
                status='사용중'
            ).first()
            if current_assignment:
                equipment.status = '사용중'
            else:
                equipment.status = '사용가능'
    if 'notes' in data:
        log.notes = data['notes']
    
    db.session.commit()
    return jsonify(log.to_dict(include_equipment=True))


@maintenance_bp.route('/maintenance-logs/<int:id>', methods=['DELETE'])
def delete_maintenance_log(id):
    """수리/점검 이력 삭제"""
    log = MaintenanceLog.query.get_or_404(id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({'message': '삭제되었습니다'}), 200


@maintenance_bp.route('/maintenance-logs/equipment/<int:equipment_id>', methods=['GET'])
def get_equipment_maintenance_logs(equipment_id):
    """특정 장비의 수리/점검 이력"""
    logs = MaintenanceLog.query.filter_by(equipment_id=equipment_id).order_by(
        MaintenanceLog.maintenance_date.desc()
    ).all()
    return jsonify([log.to_dict() for log in logs])