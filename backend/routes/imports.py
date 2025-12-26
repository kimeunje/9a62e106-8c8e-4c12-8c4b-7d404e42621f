from flask import request, jsonify, send_file
from datetime import datetime
from io import BytesIO
import pandas as pd
from . import imports_bp
from database_models import db, Equipment, User, Assignment, SecuritySeal
from utils import (
    format_asset_number, format_seal_number, clean_value, parse_date, log_change
)


@imports_bp.route('/export/excel', methods=['GET'])
def export_excel():
    """엑셀 내보내기"""
    assignments = Assignment.query.filter_by(status='사용중').all()
    
    data = []
    for assignment in assignments:
        equipment = assignment.equipment
        user = assignment.user
        seal_numbers = ', '.join([seal.seal_number for seal in equipment.security_seals])
        
        data.append({
            '구분': equipment.category,
            '모델 명': equipment.model_name,
            '자산 번호': equipment.asset_number,
            '취득일자': equipment.acquisition_date.isoformat() if equipment.acquisition_date else '',
            'IP': equipment.ip_address or '-',
            '사용자': user.name,
            '부서': user.department,
            '위치': user.location,
            '보안씰': seal_numbers or '-',
            '사용월수': f"{equipment.calculate_usage_months()}개월",
            '사용년수': f"{equipment.calculate_usage_years()}년",
            '망분리': equipment.network_type or '-',
            '윈도우 버전': equipment.windows_version or '-',
            '할당일자': assignment.assignment_date.isoformat() if assignment.assignment_date else ''
        })
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='전산장비목록')
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'전산장비목록_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )


@imports_bp.route('/import/excel/preview', methods=['POST'])
def preview_excel_import():
    """엑셀 파일 미리보기"""
    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': '엑셀 파일(.xlsx, .xls)만 지원합니다.'}), 400
    
    try:
        df = pd.read_excel(file, engine='openpyxl')
        df.columns = df.columns.str.strip()
        
        # 필수 컬럼 확인
        required_columns = ['번호', '구분', '모델 명']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'error': f'필수 컬럼이 없습니다: {", ".join(missing_columns)}',
                'found_columns': list(df.columns)
            }), 400
        
        preview_data = []
        errors = []
        new_count = 0
        update_count = 0
        
        for idx, row in df.iterrows():
            row_num = idx + 2
            
            asset_number_raw = clean_value(row.get('번호'))
            if not asset_number_raw:
                errors.append(f'행 {row_num}: 번호(자산번호)가 비어있습니다.')
                continue
            
            asset_number = format_asset_number(asset_number_raw)
            
            category = clean_value(row.get('구분'))
            if not category:
                errors.append(f'행 {row_num}: 구분이 비어있습니다.')
                continue
            
            model_name = clean_value(row.get('모델 명'))
            if not model_name:
                errors.append(f'행 {row_num}: 모델 명이 비어있습니다.')
                continue
            
            existing_equipment = Equipment.query.filter_by(asset_number=asset_number).first()
            is_new = existing_equipment is None
            
            if is_new:
                new_count += 1
            else:
                update_count += 1
            
            user_name = clean_value(row.get('사용자'))
            department = clean_value(row.get('부서'))
            location = clean_value(row.get('위치'))
            
            seals = []
            for seal_col in ['보안씰1', '보안씰2', '보안씰3']:
                seal_val = clean_value(row.get(seal_col))
                if seal_val:
                    seals.append(format_seal_number(seal_val))
            
            acquisition_date = parse_date(row.get('취득일자'))
            
            preview_data.append({
                'row_num': row_num,
                'is_new': is_new,
                'asset_number': asset_number,
                'category': category,
                'model_name': model_name,
                'spec': clean_value(row.get('규격')),
                'acquisition_date': acquisition_date.isoformat() if acquisition_date else None,
                'ip_address': clean_value(row.get('IP')),
                'network_type': clean_value(row.get('망분리')),
                'windows_version': clean_value(row.get('win버전')),
                'notes': clean_value(row.get('비고')),
                'user_name': user_name,
                'department': department,
                'location': location,
                'seals': seals
            })
        
        return jsonify({
            'success': True,
            'total_rows': len(df),
            'valid_rows': len(preview_data),
            'new_count': new_count,
            'update_count': update_count,
            'errors': errors[:20],
            'error_count': len(errors),
            'preview': preview_data[:10],
            'columns': list(df.columns)
        })
        
    except Exception as e:
        return jsonify({'error': f'파일 처리 중 오류: {str(e)}'}), 500


@imports_bp.route('/import/excel/execute', methods=['POST'])
def execute_excel_import():
    """엑셀 데이터 실제 저장"""
    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다.'}), 400
    
    file = request.files['file']
    overwrite = request.form.get('overwrite', 'false').lower() == 'true'
    changed_by = request.form.get('changed_by', '엑셀 임포트')
    
    try:
        df = pd.read_excel(file, engine='openpyxl')
        df.columns = df.columns.str.strip()
        
        results = {
            'equipment_created': 0,
            'equipment_updated': 0,
            'users_created': 0,
            'assignments_created': 0,
            'seals_created': 0,
            'errors': []
        }
        
        for idx, row in df.iterrows():
            row_num = idx + 2
            
            try:
                asset_number_raw = clean_value(row.get('번호'))
                if not asset_number_raw:
                    continue
                
                asset_number = format_asset_number(asset_number_raw)
                category = clean_value(row.get('구분'))
                model_name = clean_value(row.get('모델 명'))
                
                if not category or not model_name:
                    continue
                
                equipment = Equipment.query.filter_by(asset_number=asset_number).first()
                
                acquisition_date = parse_date(row.get('취득일자'))
                if not acquisition_date:
                    acquisition_date = datetime.now().date()
                
                # 규격을 비고에 포함
                spec = clean_value(row.get('규격'))
                notes = clean_value(row.get('비고'))
                if spec:
                    notes = f"[규격: {spec}] {notes}" if notes else f"[규격: {spec}]"
                
                if equipment is None:
                    # 신규 장비 생성
                    equipment = Equipment(
                        asset_number=asset_number,
                        category=category,
                        model_name=model_name,
                        acquisition_date=acquisition_date,
                        ip_address=clean_value(row.get('IP')),
                        network_type=clean_value(row.get('망분리')),
                        windows_version=clean_value(row.get('win버전')),
                        status='사용가능',
                        notes=notes
                    )
                    db.session.add(equipment)
                    db.session.flush()
                    results['equipment_created'] += 1
                    
                    log_change('equipment', equipment.id, '엑셀 임포트', '신규 장비',
                               None, f"{asset_number} ({model_name})", changed_by, auto_commit=False)
                    
                elif overwrite:
                    # 기존 장비 업데이트
                    equipment.category = category
                    equipment.model_name = model_name
                    equipment.acquisition_date = acquisition_date
                    equipment.ip_address = clean_value(row.get('IP'))
                    equipment.network_type = clean_value(row.get('망분리'))
                    equipment.windows_version = clean_value(row.get('win버전'))
                    if notes:
                        equipment.notes = notes
                    results['equipment_updated'] += 1
                    
                    log_change('equipment', equipment.id, '엑셀 임포트', '장비 업데이트',
                               None, f"{asset_number} 업데이트", changed_by, auto_commit=False)
                
                # 보안씰 처리
                for seal_col in ['보안씰1', '보안씰2', '보안씰3']:
                    seal_val = clean_value(row.get(seal_col))
                    if seal_val:
                        seal_number = format_seal_number(seal_val)
                        existing_seal = SecuritySeal.query.filter_by(seal_number=seal_number).first()
                        
                        if existing_seal is None:
                            seal = SecuritySeal(
                                seal_number=seal_number,
                                equipment_id=equipment.id,
                                status='정상'
                            )
                            db.session.add(seal)
                            results['seals_created'] += 1
                        elif overwrite and existing_seal.equipment_id != equipment.id:
                            existing_seal.equipment_id = equipment.id
                
                # 사용자 처리
                user_name = clean_value(row.get('사용자'))
                department = clean_value(row.get('부서'))
                location = clean_value(row.get('위치'))
                
                if user_name and department:
                    user = User.query.filter_by(name=user_name, department=department).first()
                    
                    if user is None:
                        user = User(
                            name=user_name,
                            department=department,
                            location=location or ''
                        )
                        db.session.add(user)
                        db.session.flush()
                        results['users_created'] += 1
                        
                        log_change('user', user.id, '엑셀 임포트', '신규 사용자',
                                   None, f"{user_name} ({department})", changed_by, auto_commit=False)
                    elif location and user.location != location:
                        user.location = location
                    
                    # 현재 할당 확인
                    current_assignment = Assignment.query.filter_by(
                        equipment_id=equipment.id,
                        status='사용중'
                    ).first()
                    
                    if current_assignment is None:
                        assignment = Assignment(
                            equipment_id=equipment.id,
                            user_id=user.id,
                            assignment_date=datetime.now().date(),
                            status='사용중',
                            assigned_by=changed_by,
                            reason='엑셀 임포트'
                        )
                        db.session.add(assignment)
                        equipment.status = '사용중'
                        results['assignments_created'] += 1
                    elif current_assignment.user_id != user.id and overwrite:
                        current_assignment.status = '반납'
                        current_assignment.return_date = datetime.now().date()
                        
                        new_assignment = Assignment(
                            equipment_id=equipment.id,
                            user_id=user.id,
                            assignment_date=datetime.now().date(),
                            status='사용중',
                            assigned_by=changed_by,
                            reason='엑셀 임포트 (재할당)'
                        )
                        db.session.add(new_assignment)
                        results['assignments_created'] += 1
                
            except Exception as e:
                results['errors'].append(f'행 {row_num}: {str(e)}')
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'임포트 중 오류: {str(e)}'}), 500


@imports_bp.route('/import/template', methods=['GET'])
def download_import_template():
    """엑셀 임포트 템플릿 다운로드"""
    template_data = {
        '구분': ['데스크탑', '노트북'],
        '규격': ['일반사용자', '개발자용'],
        '모델 명': ['삼성 DB400T7B', 'LG gram 15'],
        '번호': ['0001', '0002'],
        '문서번호': ['-', '-'],
        '취득일자': ['2024-01-15', '2024-03-20'],
        'IP': ['10.4.12.53', '10.4.12.54'],
        '위치': ['15층', '16층'],
        '사용자': ['홍길동', '김철수'],
        '부서': ['운영실', '개발팀'],
        '보안씰1': ['0643', '0644'],
        '보안씰2': ['0136', '-'],
        '보안씰3': ['-', '-'],
        '사용월수': ['12', '6'],
        '사용년수': ['1.0', '0.5'],
        '망분리': ['업무망', '인터넷망'],
        'win버전': ['윈도우 10', '윈도우 11'],
        '비고': ['-', '신규 입사자']
    }
    
    df = pd.DataFrame(template_data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='장비목록')
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='장비임포트_템플릿.xlsx'
    )