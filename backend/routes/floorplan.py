from flask import request, jsonify
from . import floorplan_bp
from database_models import db, FloorplanSeat, FloorplanFacility
import json
import os

# 데이터 파일 경로
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
FLOORPLAN_FLOORS_FILE = os.path.join(DATA_DIR, 'floorplan_floors.json')


def ensure_data_dir():
    """데이터 디렉토리 확인 및 생성"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_floors_data():
    """층별 배치도 데이터 로드"""
    ensure_data_dir()
    if os.path.exists(FLOORPLAN_FLOORS_FILE):
        try:
            with open(FLOORPLAN_FLOORS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"층별 데이터 로드 오류: {e}")
    
    # 빈 데이터 반환
    return {
        "14": {"items": [], "itemIdCounter": 1},
        "15": {"items": [], "itemIdCounter": 1},
        "16": {"items": [], "itemIdCounter": 1}
    }


def save_floors_data(data):
    """층별 배치도 데이터 저장"""
    ensure_data_dir()
    try:
        with open(FLOORPLAN_FLOORS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"데이터 저장 오류: {e}")
        return False


# ========== 층별 API (신규) ==========

@floorplan_bp.route('/floorplan/all', methods=['GET'])
def get_all_floors():
    """모든 층의 배치도 데이터 조회"""
    try:
        data = load_floors_data()
        return jsonify({
            'success': True,
            'floors': data
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@floorplan_bp.route('/floorplan/all', methods=['POST'])
def save_all_floors():
    """모든 층의 배치도 데이터 저장"""
    try:
        data = request.json
        floors_data = data.get('floors', {})
        
        if save_floors_data(floors_data):
            return jsonify({'message': '저장되었습니다', 'success': True})
        else:
            return jsonify({'error': '저장 실패', 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@floorplan_bp.route('/floorplan/floor/<int:floor_id>', methods=['GET'])
def get_floor(floor_id):
    """특정 층의 배치도 데이터 조회"""
    try:
        data = load_floors_data()
        floor_data = data.get(str(floor_id), {"items": [], "itemIdCounter": 1})
        return jsonify({
            'success': True,
            'floor': floor_id,
            'data': floor_data
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@floorplan_bp.route('/floorplan/floor/<int:floor_id>', methods=['POST'])
def save_floor(floor_id):
    """특정 층의 배치도 데이터 저장"""
    try:
        data = load_floors_data()
        floor_data = request.json
        
        data[str(floor_id)] = {
            'items': floor_data.get('items', []),
            'itemIdCounter': floor_data.get('itemIdCounter', 1)
        }
        
        if save_floors_data(data):
            return jsonify({'message': f'{floor_id}층 저장되었습니다', 'success': True})
        else:
            return jsonify({'error': '저장 실패', 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@floorplan_bp.route('/floorplan/search', methods=['GET'])
def search_all_floors():
    """전체 층에서 검색"""
    try:
        query = request.args.get('q', '').strip().lower()
        if not query:
            return jsonify({'results': [], 'success': True})
        
        data = load_floors_data()
        results = []
        
        for floor_id, floor_data in data.items():
            items = floor_data.get('items', [])
            for item in items:
                if item.get('type') == 'seat':
                    name = (item.get('name') or '').lower()
                    code = (item.get('code') or '').lower()
                    if query in name or query in code:
                        results.append({
                            **item,
                            'floor': int(floor_id)
                        })
        
        return jsonify({
            'results': results,
            'count': len(results),
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@floorplan_bp.route('/floorplan/stats', methods=['GET'])
def get_floor_stats():
    """층별 통계 조회"""
    try:
        data = load_floors_data()
        stats = {}
        
        for floor_id, floor_data in data.items():
            items = floor_data.get('items', [])
            seats = [i for i in items if i.get('type') == 'seat']
            facilities = [i for i in items if i.get('type') == 'facility']
            occupied_seats = [s for s in seats if s.get('name')]
            
            stats[floor_id] = {
                'total_seats': len(seats),
                'occupied_seats': len(occupied_seats),
                'empty_seats': len(seats) - len(occupied_seats),
                'total_facilities': len(facilities),
                'occupancy_rate': round(len(occupied_seats) / len(seats) * 100, 1) if seats else 0
            }
        
        return jsonify({
            'stats': stats,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ========== 기존 API (하위 호환성 유지) ==========

@floorplan_bp.route('/floorplan', methods=['GET'])
def get_floorplan():
    """배치도 데이터 조회 (기존 API - 15층 반환)"""
    try:
        data = load_floors_data()
        floor_data = data.get("15", {"items": [], "itemIdCounter": 1})
        return jsonify(floor_data)
    except Exception as e:
        # 폴백: DB에서 직접 로드
        try:
            seats = FloorplanSeat.query.all()
            facilities = FloorplanFacility.query.all()
            
            items = [seat.to_dict() for seat in seats] + [facility.to_dict() for facility in facilities]
            max_seat_id = max([s.id for s in seats], default=0)
            max_facility_id = max([f.id for f in facilities], default=0)
            
            return jsonify({
                'items': items,
                'itemIdCounter': max(max_seat_id, max_facility_id) + 1
            })
        except Exception as e2:
            return jsonify({'error': str(e2)}), 500


@floorplan_bp.route('/floorplan', methods=['POST'])
def save_floorplan():
    """배치도 데이터 저장 (기존 API - 15층에 저장)"""
    try:
        data = load_floors_data()
        floor_data = request.json
        
        # 15층에 저장
        items = floor_data.get('items', [])
        for item in items:
            item['floor'] = 15
        
        data["15"] = {
            'items': items,
            'itemIdCounter': floor_data.get('itemIdCounter', 1)
        }
        
        if save_floors_data(data):
            return jsonify({'message': '저장되었습니다', 'success': True})
        else:
            return jsonify({'error': '저장 실패', 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ========== 개별 CRUD API ==========

@floorplan_bp.route('/floorplan/seats', methods=['GET'])
def get_seats():
    """좌석 목록 조회"""
    floor = request.args.get('floor', type=int)
    
    query = FloorplanSeat.query
    if floor:
        query = query.filter_by(floor=floor)
    
    seats = query.all()
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
    floor = request.args.get('floor', type=int)
    
    query = FloorplanFacility.query
    if floor:
        query = query.filter_by(floor=floor)
    
    facilities = query.all()
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
    """배치도 데이터 JSON으로 내보내기"""
    try:
        data = load_floors_data()
        return jsonify({
            'floors': data,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500