from flask import request, jsonify
import json
import os
from . import floorplan_bp

# 배치도 데이터 저장 경로 (backend 폴더 내)
FLOORPLAN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'floorplan.json')


def ensure_data_dir():
    """data 디렉토리가 없으면 생성"""
    data_dir = os.path.dirname(FLOORPLAN_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)


@floorplan_bp.route('/floorplan', methods=['GET'])
def get_floorplan():
    """배치도 데이터 조회"""
    try:
        if os.path.exists(FLOORPLAN_FILE):
            with open(FLOORPLAN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            # 기본 데이터 반환
            return jsonify({'items': [], 'itemIdCounter': 1})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@floorplan_bp.route('/floorplan', methods=['POST'])
def save_floorplan():
    """배치도 데이터 저장"""
    try:
        ensure_data_dir()
        data = request.json
        
        with open(FLOORPLAN_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'message': '저장되었습니다.', 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@floorplan_bp.route('/floorplan/export', methods=['GET'])
def export_floorplan():
    """배치도 데이터 JSON 파일로 내보내기"""
    try:
        if os.path.exists(FLOORPLAN_FILE):
            with open(FLOORPLAN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({'items': [], 'itemIdCounter': 1})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
