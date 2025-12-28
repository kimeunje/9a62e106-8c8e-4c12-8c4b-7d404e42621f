from flask import request, jsonify
from . import floorplan_bp
from database_models import db, FloorplanSeat, FloorplanFacility


@floorplan_bp.route('/floorplan', methods=['GET'])
def get_floorplan():
    """배치도 데이터 조회"""
    try:
        seats = FloorplanSeat.query.all()
        facilities = FloorplanFacility.query.all()
        
        items = [seat.to_dict() for seat in seats] + [facility.to_dict() for facility in facilities]
        
        # 프론트엔드 호환성을 위해 itemIdCounter 계산
        max_seat_id = max([s.id for s in seats], default=0)
        max_facility_id = max([f.id for f in facilities], default=0)
        
        return jsonify({
            'items': items,
            'itemIdCounter': max(max_seat_id, max_facility_id) + 1
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@floorplan_bp.route('/floorplan', methods=['POST'])
def save_floorplan():
    """배치도 데이터 저장 (전체 덮어쓰기)"""
    try:
        data = request.json
        items = data.get('items', [])
        
        # 기존 데이터 삭제
        FloorplanSeat.query.delete()
        FloorplanFacility.query.delete()
        
        # 새 데이터 저장
        for item in items:
            if item.get('type') == 'seat':
                seat = FloorplanSeat(
                    id=item.get('id'),
                    code=item.get('code'),
                    name=item.get('name'),
                    x=item.get('x', 0),
                    y=item.get('y', 0),
                    width=item.get('width', 70),
                    height=item.get('height', 50),
                    user_id=item.get('user_id')
                )
                db.session.add(seat)
            else:
                facility = FloorplanFacility(
                    id=item.get('id'),
                    name=item.get('name', ''),
                    facility_type=item.get('facilityType', 'facility'),
                    x=item.get('x', 0),
                    y=item.get('y', 0),
                    width=item.get('width', 100),
                    height=item.get('height', 80)
                )
                db.session.add(facility)
        
        db.session.commit()
        return jsonify({'message': '저장되었습니다.', 'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


# ========== 개별 CRUD API (선택적 - 나중에 활용 가능) ==========

@floorplan_bp.route('/floorplan/seats', methods=['GET'])
def get_seats():
    """좌석 목록 조회"""
    seats = FloorplanSeat.query.all()
    return jsonify([seat.to_dict() for seat in seats])


@floorplan_bp.route('/floorplan/seats/<int:id>', methods=['PUT'])
def update_seat(id):
    """좌석 수정"""
    seat = FloorplanSeat.query.get_or_404(id)
    data = request.json
    
    if 'code' in data:
        seat.code = data['code']
    if 'name' in data:
        seat.name = data['name']
    if 'x' in data:
        seat.x = data['x']
    if 'y' in data:
        seat.y = data['y']
    if 'width' in data:
        seat.width = data['width']
    if 'height' in data:
        seat.height = data['height']
    if 'user_id' in data:
        seat.user_id = data['user_id']
    
    db.session.commit()
    return jsonify(seat.to_dict())


@floorplan_bp.route('/floorplan/seats/<int:id>', methods=['DELETE'])
def delete_seat(id):
    """좌석 삭제"""
    seat = FloorplanSeat.query.get_or_404(id)
    db.session.delete(seat)
    db.session.commit()
    return jsonify({'message': '삭제되었습니다'}), 200


@floorplan_bp.route('/floorplan/facilities', methods=['GET'])
def get_facilities():
    """시설 목록 조회"""
    facilities = FloorplanFacility.query.all()
    return jsonify([facility.to_dict() for facility in facilities])


@floorplan_bp.route('/floorplan/facilities/<int:id>', methods=['PUT'])
def update_facility(id):
    """시설 수정"""
    facility = FloorplanFacility.query.get_or_404(id)
    data = request.json
    
    if 'name' in data:
        facility.name = data['name']
    if 'facilityType' in data:
        facility.facility_type = data['facilityType']
    if 'x' in data:
        facility.x = data['x']
    if 'y' in data:
        facility.y = data['y']
    if 'width' in data:
        facility.width = data['width']
    if 'height' in data:
        facility.height = data['height']
    
    db.session.commit()
    return jsonify(facility.to_dict())


@floorplan_bp.route('/floorplan/facilities/<int:id>', methods=['DELETE'])
def delete_facility(id):
    """시설 삭제"""
    facility = FloorplanFacility.query.get_or_404(id)
    db.session.delete(facility)
    db.session.commit()
    return jsonify({'message': '삭제되었습니다'}), 200


@floorplan_bp.route('/floorplan/export', methods=['GET'])
def export_floorplan():
    """배치도 데이터 JSON으로 내보내기 (백업용)"""
    try:
        seats = FloorplanSeat.query.all()
        facilities = FloorplanFacility.query.all()
        
        items = [seat.to_dict() for seat in seats] + [facility.to_dict() for facility in facilities]
        
        return jsonify({
            'items': items,
            'itemIdCounter': max([item['id'] for item in items], default=0) + 1
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500