from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """사용자 테이블"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, index=True)
    department = db.Column(db.String(50), nullable=False, index=True)
    location = db.Column(db.String(50), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계
    assignments = db.relationship('Assignment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'department': self.department,
            'location': self.location,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Equipment(db.Model):
    """장비 테이블"""
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    model_name = db.Column(db.String(100), nullable=False)
    acquisition_date = db.Column(db.Date, nullable=False)
    ip_address = db.Column(db.String(15), nullable=True)
    network_type = db.Column(db.String(20), nullable=True)
    windows_version = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default='사용가능', nullable=False, index=True)  # 사용가능, 사용중, 수리중, 폐기
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계
    security_seals = db.relationship('SecuritySeal', backref='equipment', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='equipment', lazy=True, cascade='all, delete-orphan')
    maintenance_logs = db.relationship('MaintenanceLog', backref='equipment', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_current_user=False):
        data = {
            'id': self.id,
            'asset_number': self.asset_number,
            'category': self.category,
            'model_name': self.model_name,
            'acquisition_date': self.acquisition_date.isoformat() if self.acquisition_date else None,
            'ip_address': self.ip_address,
            'network_type': self.network_type,
            'windows_version': self.windows_version,
            'status': self.status,
            'notes': self.notes,
            'usage_months': self.calculate_usage_months(),
            'usage_years': self.calculate_usage_years(),
            'security_seals': [seal.to_dict() for seal in self.security_seals],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_current_user:
            current_assignment = Assignment.query.filter_by(
                equipment_id=self.id,
                status='사용중'
            ).first()
            
            if current_assignment:
                data['current_user'] = current_assignment.user.to_dict()
                data['assignment_date'] = current_assignment.assignment_date.isoformat()
        
        return data
    
    def calculate_usage_months(self):
        if not self.acquisition_date:
            return 0
        delta = datetime.now().date() - self.acquisition_date
        return int(delta.days / 30)
    
    def calculate_usage_years(self):
        return int(self.calculate_usage_months() / 12)


class SecuritySeal(db.Model):
    """보안씰 테이블"""
    __tablename__ = 'security_seal'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seal_number = db.Column(db.String(50), nullable=False, index=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE'), nullable=False, index=True)
    attached_date = db.Column(db.Date, default=datetime.utcnow)
    attached_location = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='정상')
    inspection_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'seal_number': self.seal_number,
            'equipment_id': self.equipment_id,
            'attached_date': self.attached_date.isoformat() if self.attached_date else None,
            'attached_location': self.attached_location,
            'status': self.status,
            'inspection_date': self.inspection_date.isoformat() if self.inspection_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Assignment(db.Model):
    """장비 할당 테이블 - 사용자와 장비를 연결"""
    __tablename__ = 'assignment'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    assignment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    return_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='사용중', nullable=False, index=True)  # 사용중, 반납
    reason = db.Column(db.Text, nullable=True)
    assigned_by = db.Column(db.String(50), nullable=True)  # 할당 담당자
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self, include_details=False):
        data = {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'user_id': self.user_id,
            'assignment_date': self.assignment_date.isoformat() if self.assignment_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'status': self.status,
            'reason': self.reason,
            'assigned_by': self.assigned_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_details:
            data['equipment'] = self.equipment.to_dict()
            data['user'] = self.user.to_dict()
        
        return data


class MaintenanceLog(db.Model):
    """수리/점검 이력 테이블"""
    __tablename__ = 'maintenance_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE'), nullable=False, index=True)
    maintenance_date = db.Column(db.Date, nullable=False, index=True)
    maintenance_type = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    technician = db.Column(db.String(50), nullable=True)
    cost = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='완료', index=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(50), nullable=True)
    
    def to_dict(self, include_equipment=False):
        data = {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'maintenance_date': self.maintenance_date.isoformat() if self.maintenance_date else None,
            'maintenance_type': self.maintenance_type,
            'description': self.description,
            'technician': self.technician,
            'cost': self.cost,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
        
        if include_equipment:
            data['equipment'] = {
                'asset_number': self.equipment.asset_number,
                'model_name': self.equipment.model_name,
                'category': self.equipment.category
            }
        
        return data


class ChangeLog(db.Model):
    """변경 이력 테이블"""
    __tablename__ = 'change_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entity_type = db.Column(db.String(20), nullable=False, index=True)  # equipment, user, assignment
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    change_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    change_type = db.Column(db.String(50), nullable=False, index=True)
    field_name = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.String(200), nullable=True)
    new_value = db.Column(db.String(200), nullable=True)
    changed_by = db.Column(db.String(50), nullable=True, index=True)
    reason = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'change_date': self.change_date.isoformat() if self.change_date else None,
            'change_type': self.change_type,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_by': self.changed_by,
            'reason': self.reason
        }
        
        
class FloorplanSeat(db.Model):
    '''좌석 배치도 - 좌석'''
    __tablename__ = 'floorplan_seat'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), nullable=True, index=True)  # 좌석 번호 (예: C-1)
    name = db.Column(db.String(50), nullable=True, index=True)  # 사용자명
    floor = db.Column(db.Integer, nullable=False, default=15, index=True)  # 층 (14, 15, 16)
    x = db.Column(db.Integer, nullable=False, default=0)
    y = db.Column(db.Integer, nullable=False, default=0)
    width = db.Column(db.Integer, nullable=False, default=70)
    height = db.Column(db.Integer, nullable=False, default=50)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # User와 연결 (선택적)
    user = db.relationship('User', backref='seat', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': 'seat',
            'code': self.code,
            'name': self.name,
            'floor': self.floor,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'user_id': self.user_id
        }


class FloorplanFacility(db.Model):
    '''좌석 배치도 - 시설'''
    __tablename__ = 'floorplan_facility'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    facility_type = db.Column(db.String(30), nullable=False, default='facility')  # facility, facility-room, facility-equip
    floor = db.Column(db.Integer, nullable=False, default=15, index=True)  # 층 (14, 15, 16)
    x = db.Column(db.Integer, nullable=False, default=0)
    y = db.Column(db.Integer, nullable=False, default=0)
    width = db.Column(db.Integer, nullable=False, default=100)
    height = db.Column(db.Integer, nullable=False, default=80)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': 'facility',
            'name': self.name,
            'facilityType': self.facility_type,
            'floor': self.floor,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }