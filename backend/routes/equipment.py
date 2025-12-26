from flask import request, jsonify
from datetime import datetime
from . import equipment_bp
from database_models import db, Equipment, User, Assignment, SecuritySeal
from utils import format_asset_number, format_seal_number, check_seal_duplicate, log_change


@equipment_bp.route('/equipment', methods=['GET'])
def get_all_equipment():
    """전체 장비 목록 조회 (페이지네이션 지원)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    asset_number = request.args.get('asset_number', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    model_name = request.args.get('model_name', '')
    user_name = request.args.get('user_name', '')
    department = request.args.get('department', '')
    
    query = Equipment.query
    
    if asset_number:
        query = query.filter(Equipment.asset_number.like(f'%{asset_number}%'))
    if category:
        query = query.filter(Equipment.category == category)
    if status:
        query = query.filter(Equipment.status == status)
    if model_name:
        query = query.filter(Equipment.model_name.like(f'%{model_name}%'))
    
    if user_name or department:
        query = query.outerjoin(Assignment, 
            db.and_(Assignment.equipment_id == Equipment.id, Assignment.status == '사용중')
        ).outerjoin(User, Assignment.user_id == User.id)
        
        if user_name:
            query = query.filter(User.name.like(f'%{user_name}%'))
        if department:
            query = query.filter(User.department.like(f'%{department}%'))
    
    total = query.count()
    equipment_list = query.order_by(Equipment.asset_number).offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'items': [eq.to_dict(include_current_user=True) for eq in equipment_list],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@equipment_bp.route('/equipment/<int:id>', methods=['GET'])
def get_equipment(id):
    """특정 장비 조회"""
    equipment = Equipment.query.get_or_404(id)
    return jsonify(equipment.to_dict(include_current_user=True))


@equipment_bp.route('/equipment/asset/<string:asset_number>', methods=['GET'])
def get_equipment_by_asset(asset_number):
    """자산번호로 장비 조회"""
    equipment = Equipment.query.filter_by(asset_number=asset_number).first_or_404()
    return jsonify(equipment.to_dict(include_current_user=True))


@equipment_bp.route('/equipment', methods=['POST'])
def create_equipment():
    """장비 등록"""
    data = request.json
    acquisition_date = datetime.strptime(data['acquisition_date'], '%Y-%m-%d').date()
    
    formatted_asset_number = format_asset_number(data['asset_number'])
    
    existing_equipment = Equipment.query.filter_by(asset_number=formatted_asset_number).first()
    if existing_equipment:
        return jsonify({'error': f'이미 존재하는 자산번호입니다: {formatted_asset_number}'}), 400
    
    # 보안씰 중복 체크
    if 'seal_numbers' in data and data['seal_numbers']:
        seal_numbers = [s.strip() for s in data['seal_numbers'].split(',') if s.strip()]
        for seal_num in seal_numbers:
            formatted_seal_num = format_seal_number(seal_num)
            existing_seal = check_seal_duplicate(formatted_seal_num)
            if existing_seal:
                eq = Equipment.query.get(existing_seal.equipment_id)
                eq_info = eq.asset_number if eq else 'N/A'
                return jsonify({
                    'error': f'보안씰 {formatted_seal_num}은(는) 이미 장비 {eq_info}에 할당되어 있습니다.'
                }), 400
    
    equipment = Equipment(
        asset_number=formatted_asset_number,
        category=data['category'],
        model_name=data['model_name'],
        acquisition_date=acquisition_date,
        ip_address=data.get('ip_address'),
        network_type=data.get('network_type'),
        windows_version=data.get('windows_version'),
        status='사용가능',
        notes=data.get('notes')
    )
    
    db.session.add(equipment)
    db.session.flush()
    
    log_change('equipment', equipment.id, '장비 등록', '신규 장비', None, 
               f"{formatted_asset_number} ({equipment.model_name})", data.get('changed_by'), 
               auto_commit=False)
    
    # 보안씰 추가
    if 'seal_numbers' in data and data['seal_numbers']:
        seal_numbers = [s.strip() for s in data['seal_numbers'].split(',') if s.strip()]
        for seal_num in seal_numbers:
            formatted_seal_num = format_seal_number(seal_num)
            seal = SecuritySeal(
                seal_number=formatted_seal_num,
                equipment_id=equipment.id
            )
            db.session.add(seal)
            db.session.flush()
            
            log_change('security_seal', seal.id, '보안씰 등록', '신규 보안씰', 
                       None, f"{formatted_seal_num} → 장비({formatted_asset_number})", 
                       data.get('changed_by'), auto_commit=False)
    
    db.session.commit()
    
    return jsonify(equipment.to_dict()), 201


@equipment_bp.route('/equipment/<int:id>', methods=['PUT'])
def update_equipment(id):
    """장비 정보 수정 (보안씰 포함)"""
    equipment = Equipment.query.get_or_404(id)
    data = request.json
    
    changes = {}
    
    # 자산번호 변경
    if 'asset_number' in data:
        formatted_asset_number = format_asset_number(data['asset_number'])
        if equipment.asset_number != formatted_asset_number:
            existing = Equipment.query.filter(
                Equipment.asset_number == formatted_asset_number,
                Equipment.id != id
            ).first()
            if existing:
                return jsonify({'error': f'이미 존재하는 자산번호입니다: {formatted_asset_number}'}), 400
            
            changes['자산번호'] = (equipment.asset_number, formatted_asset_number)
            equipment.asset_number = formatted_asset_number
    
    # 나머지 필드 처리
    field_mapping = {
        'category': '구분',
        'model_name': '모델명',
        'ip_address': 'IP주소',
        'network_type': '망분리',
        'windows_version': '윈도우버전',
        'status': '상태',
        'notes': '비고'
    }
    
    for field, korean_name in field_mapping.items():
        if field in data:
            old_value = getattr(equipment, field)
            new_value = data[field]
            if old_value != new_value:
                changes[korean_name] = (old_value, new_value)
                setattr(equipment, field, new_value)
    
    if 'acquisition_date' in data:
        new_date = datetime.strptime(data['acquisition_date'], '%Y-%m-%d').date()
        if equipment.acquisition_date != new_date:
            changes['취득일자'] = (equipment.acquisition_date.isoformat(), new_date.isoformat())
            equipment.acquisition_date = new_date
    
    # 보안씰 수정 처리
    if 'seal_numbers' in data:
        old_seals = {seal.seal_number: seal for seal in equipment.security_seals}
        old_seal_numbers = set(old_seals.keys())
        
        new_seal_numbers_raw = data['seal_numbers']
        if new_seal_numbers_raw:
            new_seal_numbers = set(format_seal_number(s.strip()) for s in new_seal_numbers_raw.split(',') if s.strip())
        else:
            new_seal_numbers = set()
        
        # 새로 추가되는 보안씰 중복 체크
        seals_to_add = new_seal_numbers - old_seal_numbers
        for seal_num in seals_to_add:
            existing_seal = check_seal_duplicate(seal_num, exclude_equipment_id=id)
            if existing_seal:
                eq = Equipment.query.get(existing_seal.equipment_id)
                eq_info = eq.asset_number if eq else 'N/A'
                return jsonify({
                    'error': f'보안씰 {seal_num}은(는) 이미 장비 {eq_info}에 할당되어 있습니다.'
                }), 400
        
        if old_seal_numbers != new_seal_numbers:
            # 삭제할 보안씰
            seals_to_remove = old_seal_numbers - new_seal_numbers
            for seal_num in seals_to_remove:
                seal = old_seals[seal_num]
                log_change('security_seal', seal.id, '보안씰 삭제', '보안씰 제거',
                           f"{seal_num} (장비: {equipment.asset_number})", None,
                           data.get('changed_by'), data.get('reason'), auto_commit=False)
                db.session.delete(seal)
            
            # 추가할 보안씰
            for seal_num in seals_to_add:
                new_seal = SecuritySeal(
                    seal_number=seal_num,
                    equipment_id=equipment.id
                )
                db.session.add(new_seal)
                db.session.flush()
                
                log_change('security_seal', new_seal.id, '보안씰 등록', '신규 보안씰',
                           None, f"{seal_num} → 장비({equipment.asset_number})",
                           data.get('changed_by'), data.get('reason'), auto_commit=False)
            
            old_seal_str = ', '.join(sorted(old_seal_numbers)) if old_seal_numbers else '없음'
            new_seal_str = ', '.join(sorted(new_seal_numbers)) if new_seal_numbers else '없음'
            changes['보안씰'] = (old_seal_str, new_seal_str)
    
    # 변경 이력 기록
    for field_name, (old_val, new_val) in changes.items():
        log_change('equipment', id, '장비 정보변경', field_name, str(old_val), 
                   str(new_val), data.get('changed_by'), data.get('reason'), auto_commit=False)
    
    db.session.commit()
    
    return jsonify(equipment.to_dict())


@equipment_bp.route('/equipment/<int:id>', methods=['DELETE'])
def delete_equipment(id):
    """장비 삭제"""
    equipment = Equipment.query.get_or_404(id)
    
    active_assignment = Assignment.query.filter_by(equipment_id=id, status='사용중').first()
    if active_assignment:
        return jsonify({'error': '사용중인 장비는 삭제할 수 없습니다.'}), 400
    
    db.session.delete(equipment)
    db.session.commit()
    return jsonify({'message': '삭제되었습니다'}), 200


@equipment_bp.route('/equipment/search', methods=['GET'])
def search_equipment():
    """장비 검색"""
    query = Equipment.query
    
    asset_number = request.args.get('asset_number')
    category = request.args.get('category')
    model_name = request.args.get('model_name')
    status = request.args.get('status')
    
    if asset_number:
        query = query.filter(Equipment.asset_number.like(f'%{asset_number}%'))
    if category:
        query = query.filter(Equipment.category == category)
    if model_name:
        query = query.filter(Equipment.model_name.like(f'%{model_name}%'))
    if status:
        query = query.filter(Equipment.status == status)
    
    equipment_list = query.all()
    return jsonify([eq.to_dict(include_current_user=True) for eq in equipment_list])


@equipment_bp.route('/equipment/available', methods=['GET'])
def get_available_equipment():
    """사용 가능한 장비 목록 (할당용)"""
    equipment_list = Equipment.query.filter_by(status='사용가능').order_by(Equipment.asset_number).all()
    return jsonify([eq.to_dict() for eq in equipment_list])


@equipment_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """대시보드 통계"""
    total_equipment = Equipment.query.count()
    total_users = User.query.count()
    total_seals = SecuritySeal.query.count()
    active_assignments = Assignment.query.filter_by(status='사용중').count()
    
    status_stats = db.session.query(
        Equipment.status,
        db.func.count(Equipment.id)
    ).group_by(Equipment.status).all()
    
    category_stats = db.session.query(
        Equipment.category,
        db.func.count(Equipment.id)
    ).group_by(Equipment.category).all()
    
    department_stats = db.session.query(
        User.department,
        db.func.count(User.id)
    ).group_by(User.department).all()
    
    location_stats = db.session.query(
        User.location,
        db.func.count(User.id)
    ).group_by(User.location).all()
    
    seal_status_stats = db.session.query(
        SecuritySeal.status,
        db.func.count(SecuritySeal.id)
    ).group_by(SecuritySeal.status).all()
    
    return jsonify({
        'total_equipment': total_equipment,
        'total_users': total_users,
        'total_seals': total_seals,
        'active_assignments': active_assignments,
        'by_status': dict(status_stats),
        'by_category': dict(category_stats),
        'by_department': dict(department_stats),
        'by_location': dict(location_stats),
        'by_seal_status': dict(seal_status_stats)
    })