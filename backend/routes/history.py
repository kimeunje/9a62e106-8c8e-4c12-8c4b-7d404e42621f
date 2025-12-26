from flask import request, jsonify
from datetime import datetime
from . import history_bp
from database_models import db, ChangeLog


@history_bp.route('/change-logs', methods=['GET'])
def get_all_change_logs():
    """전체 변경 이력 조회"""
    query = ChangeLog.query
    
    entity_type = request.args.get('entity_type')
    change_type = request.args.get('change_type')
    changed_by = request.args.get('changed_by')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if entity_type:
        query = query.filter(ChangeLog.entity_type == entity_type)
    if change_type:
        query = query.filter(ChangeLog.change_type == change_type)
    if changed_by:
        query = query.filter(ChangeLog.changed_by.like(f'%{changed_by}%'))
    if start_date:
        query = query.filter(ChangeLog.change_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(ChangeLog.change_date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    logs = query.order_by(ChangeLog.change_date.desc()).limit(500).all()
    return jsonify([log.to_dict() for log in logs])


@history_bp.route('/change-logs/entity/<string:entity_type>/<int:entity_id>', methods=['GET'])
def get_entity_change_logs(entity_type, entity_id):
    """특정 엔티티의 변경 이력"""
    logs = ChangeLog.query.filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(ChangeLog.change_date.desc()).all()
    return jsonify([log.to_dict() for log in logs])


@history_bp.route('/change-logs/recent', methods=['GET'])
def get_recent_change_logs():
    """최근 변경 이력 (대시보드용)"""
    limit = request.args.get('limit', 20, type=int)
    logs = ChangeLog.query.order_by(ChangeLog.change_date.desc()).limit(limit).all()
    return jsonify([log.to_dict() for log in logs])