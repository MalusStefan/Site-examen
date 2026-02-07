from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .models import CalendarEvent, Note
from . import db
from datetime import datetime, date


calendar_bp = Blueprint('calendar', __name__)


@calendar_bp.route('/calendar')
@login_required
def calendar_page():
    """Render the calendar page"""
    return render_template("calendar.html", user=current_user)


# API ROUTES - UNIQUE NAMES FOR EACH ENDPOINT

@calendar_bp.route('/calendar/events', methods=['GET'])
@login_required
def get_all_events():
    """Get all events - FIXED VERSION"""
    try:
        events = CalendarEvent.query.filter_by(user_id=current_user.id).all()

        events_list = []
        for event in events:
            # Format basic event data
            event_data = {
                'id': event.id,
                'title': event.title or 'Untitled',
                'color': event.color or '#007bff',
                'extendedProps': {
                    'description': event.description or '',
                    'noteId': event.note_id or None,
                    'hasNote': bool(event.note_id)
                }
            }

            # Format start date/time
            start_date = event.event_date.strftime('%Y-%m-%d')
            if event.start_time:
                event_data['start'] = f"{start_date}T{event.start_time.strftime('%H:%M:%S')}"
                event_data['extendedProps']['startTime'] = event.start_time.strftime('%H:%M')
            else:
                event_data['start'] = start_date
                event_data['allDay'] = True

            # Format end date/time if exists
            if event.end_time:
                event_data['end'] = f"{start_date}T{event.end_time.strftime('%H:%M:%S')}"
                event_data['extendedProps']['endTime'] = event.end_time.strftime('%H:%M')

            # Add note content if exists
            if event.note_id and event.note:
                event_data['extendedProps']['noteContent'] = event.note.data[:200] + (
                    '...' if len(event.note.data) > 200 else '')

            events_list.append(event_data)

        return jsonify(events_list)

    except Exception as e:
        print(f"❌ ERROR in get_all_events: {str(e)}")
        # Return empty array on error to prevent calendar crash
        return jsonify([])


@calendar_bp.route('/calendar/events', methods=['POST'])
@login_required
def create_event():
    """Create new event - UNIQUE NAME"""
    try:
        data = request.json

        if not data.get('title') or not data.get('date'):
            return jsonify({'error': 'Title and date required'}), 400

        event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

        start_time = None
        end_time = None

        if data.get('startTime'):
            start_time = datetime.strptime(data['startTime'], '%H:%M').time()
        if data.get('endTime'):
            end_time = datetime.strptime(data['endTime'], '%H:%M').time()

        new_event = CalendarEvent(
            title=data['title'],
            description=data.get('description', ''),
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            color=data.get('color', '#007bff'),
            user_id=current_user.id,
            note_id=data.get('noteId')
        )

        db.session.add(new_event)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Event created',
            'eventId': new_event.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@calendar_bp.route('/calendar/events/<int:event_id>', methods=['GET'])
@login_required
def get_single_event(event_id):
    """Get single event - UNIQUE NAME"""
    try:
        event = CalendarEvent.query.get_or_404(event_id)

        if event.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        event_data = {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': event.event_date.strftime('%Y-%m-%d'),
            'startTime': event.start_time.strftime('%H:%M') if event.start_time else '',
            'endTime': event.end_time.strftime('%H:%M') if event.end_time else '',
            'color': event.color,
            'noteId': event.note_id
        }

        return jsonify(event_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 404


@calendar_bp.route('/calendar/events/<int:event_id>', methods=['PUT'])
@login_required
def update_single_event(event_id):
    """Update event - UNIQUE NAME"""
    try:
        event = CalendarEvent.query.get_or_404(event_id)

        if event.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.json

        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'date' in data:
            event.event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'startTime' in data:
            event.start_time = datetime.strptime(data['startTime'], '%H:%M').time() if data['startTime'] else None
        if 'endTime' in data:
            event.end_time = datetime.strptime(data['endTime'], '%H:%M').time() if data['endTime'] else None
        if 'color' in data:
            event.color = data['color']
        if 'noteId' in data:
            event.note_id = data['noteId']

        db.session.commit()

        return jsonify({'success': True, 'message': 'Event updated'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@calendar_bp.route('/calendar/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_single_event(event_id):
    """Delete event - UNIQUE NAME"""
    try:
        event = CalendarEvent.query.get_or_404(event_id)

        if event.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        db.session.delete(event)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Event deleted'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@calendar_bp.route('/calendar/notes', methods=['GET'])
@login_required
def get_user_notes():
    """Get user notes - UNIQUE NAME"""
    notes = Note.query.filter_by(user_id=current_user.id).all()

    notes_list = []
    for note in notes:
        notes_list.append({
            'id': note.id,
            'content': note.data[:100] + ('...' if len(note.data) > 100 else ''),
            'fullContent': note.data,
            'created_at': note.date.strftime('%Y-%m-%d %H:%M')
        })

    return jsonify(notes_list)


@calendar_bp.route('/calendar/stats', methods=['GET'])
@login_required
def get_calendar_statistics():
    """Get stats - UNIQUE NAME"""
    events = CalendarEvent.query.filter_by(user_id=current_user.id).all()

    today = date.today()

    today_count = len([e for e in events if e.event_date == today])
    month_count = len([e for e in events if e.event_date.month == today.month and e.event_date.year == today.year])

    return jsonify({
        'total': len(events),
        'today': today_count,
        'month': month_count
    })


# Test route
@calendar_bp.route('/calendar/test')
def test_calendar():
    return "✅ Calendar working! All endpoints have unique names."