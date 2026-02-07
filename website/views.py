from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note
from . import db
from datetime import datetime
import json

# blueprint for notes section
views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')  # Get note from HTML

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)  # provide schema for note
            db.session.add(new_note)  # add note to database
            db.session.commit()
            flash('Note added!', category='success')

    # Pass today's date to template for calendar feature
    return render_template("home.html", user=current_user, today=datetime.now().strftime('%Y-%m-%d'))


@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)  # This function expects a JSON from INDEX.js file
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})


# NEW: Edit note functionality
@views.route('/edit-note', methods=['POST'])
@login_required
def edit_note():
    try:
        note_data = request.json
        note_id = note_data.get('noteId')
        new_data = note_data.get('newData')

        if not note_id or not new_data:
            return jsonify({'error': 'Incomplete data'}), 400

        note = Note.query.get(note_id)

        if not note:
            return jsonify({'error': 'Note not found'}), 404

        if note.user_id != current_user.id:
            return jsonify({'error': 'You do not have permission to edit this note'}), 403

        # Update note content
        from sqlalchemy.sql import func  # Import here to avoid circular imports
        note.data = new_data
        note.date = func.now()  # Update date to current time

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Note updated successfully',
            'noteId': note.id,
            'newData': note.data,
            'newDate': note.date.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Edit error: {str(e)}'}), 500