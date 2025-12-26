from flask import request, jsonify
from datetime import datetime
from . import seals_bp
from database_models import db, Equipment, SecuritySeal
from utils import format_seal_number, check_seal_duplicate, log_change


@seals_bp.route('/security-seals', methods=['GET'])
def get_all_security_seals():
    """전체 보안씰 목록 조회"""
    seals = SecuritySeal.query.all()
    result = []
    for seal in seals:
        seal_data = seal.to_dict()
        if seal.equipment:
            seal_data['equipment'] = {
                'id': seal.equipment.id,
                'asset_number': seal.equipment.asset_number,
                'model_name': seal.equipment.model_name,
                'category': seal.equipment.category
            }
        result.append(seal_data)
    return jsonify(result)


@seals_bp.route('/security-seals/search', methods=['GET'])
def search_security_seals():
    """보안씰 검색"""
    query = SecuritySeal.query
    
    seal_number = request.args.get('seal_number')
    status = request.args.get('status')
    asset_number = request.args.get('asset_number')
    
    if seal_number:
        query = query.filter(SecuritySeal.seal_number.like(f'%{seal_number}%'))
    if status:
        query = query.filter(SecuritySeal.status == status)
    if asset_number:
        query = query.join(Equipment).filter(Equipment.asset_number.like(f'%{asset_number}%'))
    
    seals = query.all()
    result = []
    for seal in seals:
        seal_data = seal.to_dict()
        if seal.equipment:
            seal_data['equipment'] = {
                'id': seal.equipment.id,
                'asset_number': seal.equipment.asset_number,
                'model_name': seal.equipment.model_name,
                'category': seal.equipment.category
            }
        result.append(seal_data)
    return jsonify(result)


@seals_bp.route('/security-seals/<int:id>', methods=['GET'])
def get_security_seal(id):
    """특정 보안씰 조회"""
    seal = SecuritySeal.query.get_or_404(id)
    seal_data = seal.to_dict()
    if seal.equipment:
        seal_data['equipment'] = {
            'id': seal.equipment.id,
            'asset_number': seal.equipment.asset_number,
            'model_name': seal.equipment.model_name,
            'category': seal.equipment.category
        }
    return jsonify(seal_data)


@seals_bp.route('/security-seals', methods=['POST'])
def create_security_seal():
    """보안씰 등록"""
    data = request.json
    
    formatted_seal_number = format_seal_number(data['seal_number'])
    
    # 중복 체크
    existing_seal = check_seal_duplicate(formatted_seal_number)
    if existing_seal:
        eq = Equipment.query.get(existing_seal.equipment_id)
        eq_info = eq.asset_number if eq else 'N/A'
        return jsonify({
            'error': f'보안씰 {formatted_seal_number}은(는) 이미 장비 {eq_info}에 할당되어 있습니다.'
        }), 400
    
    # 장비 정보 조회
    equipment = Equipment.query.get(data['equipment_id'])
    if not equipment:
        return jsonify({'error': '장비를 찾을 수 없습니다.'}), 404
    
    seal = SecuritySeal(
        seal_number=formatted_seal_number,
        equipment_id=data['equipment_id'],
        attached_location=data.get('attached_location'),
        status=data.get('status', '정상'),
        notes=data.get('notes')
    )
    
    if 'attached_date' in data:
        seal.attached_date = datetime.strptime(data['attached_date'], '%Y-%m-%d').date()
    
    db.session.add(seal)
    db.session.flush()
    
    log_change('security_seal', seal.id, '보안씰 등록', '신규 보안씰',
               None, f"{formatted_seal_number} → 장비({equipment.asset_number})",
               data.get('changed_by'), auto_commit=False)
    
    db.session.commit()
    
    seal_data = seal.to_dict()
    seal_data['equipment'] = {
        'id': equipment.id,
        'asset_number': equipment.asset_number,
        'model_name': equipment.model_name,
        'category': equipment.category
    }
    
    return jsonify(seal_data), 201


@seals_bp.route('/security-seals/<int:id>', methods=['PUT'])
def update_security_seal(id):
    """보안씰 수정"""
    seal = SecuritySeal.query.get_or_404(id)
    data = request.json
    
    equipment = Equipment.query.get(seal.equipment_id)
    equipment_info = equipment.asset_number if equipment else 'N/A'
    
    changes = {}
    
    # 씰번호 변경
    if 'seal_number' in data:
        formatted_seal_number = format_seal_number(data['seal_number'])
        if seal.seal_number != formatted_seal_number:
            existing_seal = check_seal_duplicate(formatted_seal_number, exclude_seal_id=id)
            if existing_seal:
                eq = Equipment.query.get(existing_seal.equipment_id)
                eq_info = eq.asset_number if eq else 'N/A'
                return jsonify({
                    'error': f'보안씰 {formatted_seal_number}은(는) 이미 장비 {eq_info}에 할당되어 있습니다.'
                }), 400
            
            changes['씰번호'] = (seal.seal_number, formatted_seal_number)
            seal.seal_number = formatted_seal_number
    
    # 장비 변경
    if 'equipment_id' in data and seal.equipment_id != data['equipment_id']:
        old_equipment = Equipment.query.get(seal.equipment_id)
        new_equipment = Equipment.query.get(data['equipment_id'])
        if not new_equipment:
            return jsonify({'error': '장비를 찾을 수 없습니다.'}), 404
        
        old_eq_info = old_equipment.asset_number if old_equipment else 'N/A'
        new_eq_info = new_equipment.asset_number if new_equipment else 'N/A'
        changes['할당장비'] = (old_eq_info, new_eq_info)
        seal.equipment_id = data['equipment_id']
        equipment_info = new_eq_info
    
    if 'attached_location' in data and seal.attached_location != data['attached_location']:
        changes['부착위치'] = (seal.attached_location or '없음', data['attached_location'] or '없음')
        seal.attached_location = data['attached_location']
    
    if 'status' in data and seal.status != data['status']:
        changes['상태'] = (seal.status, data['status'])
        seal.status = data['status']
    
    if 'notes' in data and seal.notes != data['notes']:
        changes['비고'] = (seal.notes or '없음', data['notes'] or '없음')
        seal.notes = data['notes']
    
    if 'inspection_date' in data:
        new_date = datetime.strptime(data['inspection_date'], '%Y-%m-%d').date() if data['inspection_date'] else None
        old_date = seal.inspection_date.isoformat() if seal.inspection_date else '없음'
        new_date_str = new_date.isoformat() if new_date else '없음'
        if seal.inspection_date != new_date:
            changes['점검일'] = (old_date, new_date_str)
            seal.inspection_date = new_date
    
    if 'attached_date' in data:
        new_date = datetime.strptime(data['attached_date'], '%Y-%m-%d').date() if data['attached_date'] else None
        old_date = seal.attached_date.isoformat() if seal.attached_date else '없음'
        new_date_str = new_date.isoformat() if new_date else '없음'
        if seal.attached_date != new_date:
            changes['부착일'] = (old_date, new_date_str)
            seal.attached_date = new_date
    
    # 변경 이력 기록
    for field_name, (old_val, new_val) in changes.items():
        log_change('security_seal', id, '보안씰 수정', field_name, 
                   str(old_val), str(new_val), 
                   data.get('changed_by'), f"장비: {equipment_info}", auto_commit=False)
    
    db.session.commit()
    
    seal_data = seal.to_dict()
    current_equipment = Equipment.query.get(seal.equipment_id)
    if current_equipment:
        seal_data['equipment'] = {
            'id': current_equipment.id,
            'asset_number': current_equipment.asset_number,
            'model_name': current_equipment.model_name,
            'category': current_equipment.category
        }
    
    return jsonify(seal_data)


@seals_bp.route('/security-seals/<int:id>', methods=['DELETE'])
def delete_security_seal(id):
    """보안씰 삭제"""
    seal = SecuritySeal.query.get_or_404(id)
    
    equipment = Equipment.query.get(seal.equipment_id)
    equipment_info = equipment.asset_number if equipment else 'N/A'
    seal_number = seal.seal_number
    
    changed_by = None
    if request.json:
        changed_by = request.json.get('changed_by')
    
    log_change('security_seal', id, '보안씰 삭제', '보안씰 제거',
               f"{seal_number} (장비: {equipment_info})", None,
               changed_by, auto_commit=False)
    
    db.session.delete(seal)
    db.session.commit()
    return jsonify({'message': '삭제되었습니다'}), 200


@seals_bp.route('/security-seals/equipment/<int:equipment_id>', methods=['GET'])
def get_equipment_seals(equipment_id):
    """특정 장비의 보안씰 목록"""
    seals = SecuritySeal.query.filter_by(equipment_id=equipment_id).all()
    return jsonify([seal.to_dict() for seal in seals])


@seals_bp.route('/security-seals/check-duplicate', methods=['GET'])
def check_seal_duplicate_api():
    """보안씰 중복 체크 API"""
    seal_number = request.args.get('seal_number')
    exclude_id = request.args.get('exclude_id', type=int)
    
    if not seal_number:
        return jsonify({'error': '보안씰 번호가 필요합니다.'}), 400
    
    formatted_seal_number = format_seal_number(seal_number)
    existing_seal = check_seal_duplicate(formatted_seal_number, exclude_seal_id=exclude_id)
    
    if existing_seal:
        eq = Equipment.query.get(existing_seal.equipment_id)
        return jsonify({
            'duplicate': True,
            'seal_number': formatted_seal_number,
            'equipment_asset_number': eq.asset_number if eq else None,
            'equipment_id': existing_seal.equipment_id
        })
    
    return jsonify({
        'duplicate': False,
        'seal_number': formatted_seal_number
    })