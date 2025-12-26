import re
import pandas as pd
from datetime import datetime
from database_models import db, ChangeLog


def format_padded_number(value, length=4):
    """숫자를 지정된 길이로 0 패딩하여 반환"""
    if not value:
        return value
    
    value = str(value).strip()
    
    if value.isdigit():
        return value.zfill(length)
    
    match = re.match(r'^([A-Za-z가-힣]+-?)(\d+)$', value)
    if match:
        prefix = match.group(1)
        number = match.group(2)
        return f"{prefix}{number.zfill(length)}"
    
    return value


def format_asset_number(asset_number):
    """자산번호 포맷팅"""
    return format_padded_number(asset_number, 4)


def format_seal_number(seal_number):
    """보안씰 번호 포맷팅"""
    return format_padded_number(seal_number, 4)


def clean_value(value):
    """엑셀 값 정리 - 빈값, '-', NaN 처리"""
    if value is None:
        return None
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value in ['-', '', 'nan', 'None', 'NaN']:
        return None
    return value


def parse_date(value):
    """날짜 파싱"""
    if not value:
        return None
    
    cleaned = clean_value(value)
    if not cleaned:
        return None
    
    if isinstance(value, pd.Timestamp):
        return value.date()
    
    if isinstance(value, datetime):
        return value.date()
    
    date_formats = ['%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d', '%d-%m-%Y', '%d.%m.%Y']
    for fmt in date_formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    
    return None


def log_change(entity_type, entity_id, change_type, field_name, old_value, new_value, 
               changed_by=None, reason=None, auto_commit=True):
    """변경 이력 기록"""
    log = ChangeLog(
        entity_type=entity_type,
        entity_id=entity_id,
        change_type=change_type,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        changed_by=changed_by,
        reason=reason
    )
    db.session.add(log)
    if auto_commit:
        db.session.commit()


def check_seal_duplicate(seal_number, exclude_seal_id=None, exclude_equipment_id=None):
    """보안씰 중복 체크"""
    from database_models import SecuritySeal
    
    query = SecuritySeal.query.filter_by(seal_number=seal_number)
    
    if exclude_seal_id:
        query = query.filter(SecuritySeal.id != exclude_seal_id)
    
    if exclude_equipment_id:
        query = query.filter(SecuritySeal.equipment_id != exclude_equipment_id)
    
    return query.first()