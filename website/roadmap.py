from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .models import RoadmapGoal
from . import db
from datetime import datetime, date
import json

roadmap_bp = Blueprint('roadmap', __name__)


@roadmap_bp.route('/roadmap')
@login_required
def roadmap_page():
    """Render the roadmap page"""
    goals = RoadmapGoal.query.filter_by(user_id=current_user.id).order_by(RoadmapGoal.position).all()
    return render_template("roadmap.html", user=current_user, goals=goals)


@roadmap_bp.route('/roadmap/goals', methods=['GET'])
@login_required
def get_goals():
    """Get all roadmap goals"""
    goals = RoadmapGoal.query.filter_by(user_id=current_user.id).order_by(RoadmapGoal.position).all()

    goals_list = []
    for goal in goals:
        days_remaining = 0
        is_overdue = False

        if goal.deadline:
            days_remaining = (goal.deadline - date.today()).days
            is_overdue = days_remaining < 0 and not goal.is_completed

        goals_list.append({
            'id': goal.id,
            'title': goal.title,
            'description': goal.description or '',
            'position': goal.position,
            'deadline': goal.deadline.strftime('%Y-%m-%d') if goal.deadline else None,
            'is_completed': goal.is_completed,
            'created_at': goal.created_at.strftime('%Y-%m-%d %H:%M'),
            'completed_at': goal.completed_at.strftime('%Y-%m-%d %H:%M') if goal.completed_at else None,
            'days_remaining': days_remaining if days_remaining > 0 else 0,
            'is_overdue': is_overdue
        })

    return jsonify(goals_list)


@roadmap_bp.route('/roadmap/goals', methods=['POST'])
@login_required
def create_goal():
    """Create a new roadmap goal"""
    try:
        data = request.json

        # Get max position to add at the end
        max_position = db.session.query(db.func.max(RoadmapGoal.position)).filter_by(
            user_id=current_user.id).scalar() or 0

        deadline = None
        if data.get('deadline'):
            try:
                deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        new_goal = RoadmapGoal(
            title=data['title'],
            description=data.get('description', ''),
            position=max_position + 1,
            deadline=deadline,
            is_completed=False,
            user_id=current_user.id
        )

        db.session.add(new_goal)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Goal created successfully',
            'goalId': new_goal.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@roadmap_bp.route('/roadmap/goals/<int:goal_id>', methods=['PUT'])
@login_required
def update_goal(goal_id):
    """Update a roadmap goal"""
    try:
        goal = RoadmapGoal.query.get_or_404(goal_id)

        if goal.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.json

        if 'title' in data:
            goal.title = data['title']
        if 'description' in data:
            goal.description = data['description']
        if 'deadline' in data:
            goal.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date() if data['deadline'] else None
        if 'is_completed' in data:
            goal.is_completed = data['is_completed']
            goal.completed_at = datetime.now() if data['is_completed'] else None
        if 'position' in data:
            goal.position = data['position']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Goal updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@roadmap_bp.route('/roadmap/goals/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    """Delete a roadmap goal"""
    try:
        goal = RoadmapGoal.query.get_or_404(goal_id)

        if goal.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        db.session.delete(goal)
        db.session.commit()

        # Reorder remaining goals
        goals = RoadmapGoal.query.filter_by(user_id=current_user.id).order_by(RoadmapGoal.position).all()
        for index, goal in enumerate(goals):
            goal.position = index + 1
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Goal deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@roadmap_bp.route('/roadmap/goals/reorder', methods=['POST'])
@login_required
def reorder_goals():
    """Reorder goals"""
    try:
        data = request.json
        order = data.get('order', [])

        for index, goal_id in enumerate(order):
            goal = RoadmapGoal.query.get(goal_id)
            if goal and goal.user_id == current_user.id:
                goal.position = index + 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Goals reordered successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@roadmap_bp.route('/roadmap/stats', methods=['GET'])
@login_required
def get_roadmap_stats():
    """Get roadmap statistics"""
    goals = RoadmapGoal.query.filter_by(user_id=current_user.id).all()

    total = len(goals)
    completed = len([g for g in goals if g.is_completed])
    pending = total - completed
    overdue = len([g for g in goals if g.deadline and g.deadline < date.today() and not g.is_completed])

    completion_rate = 0
    if total > 0:
        completion_rate = round((completed / total * 100), 1)

    return jsonify({
        'total': total,
        'completed': completed,
        'pending': pending,
        'overdue': overdue,
        'completion_rate': completion_rate
    })