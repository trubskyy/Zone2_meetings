from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import random

meetings_bp = Blueprint('meetings', __name__)

# Mock data for meetings
mock_meetings = [
    {
        "id": 1,
        "title": "Team Standup",
        "time": "9:00 AM",
        "participants": 5,
        "status": "upcoming",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": 2,
        "title": "Product Review",
        "time": "11:30 AM",
        "participants": 8,
        "status": "upcoming",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": 3,
        "title": "Client Check-in",
        "time": "1:00 PM",
        "participants": 3,
        "status": "upcoming",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": 4,
        "title": "Sprint Planning",
        "time": "3:00 PM",
        "participants": 6,
        "status": "upcoming",
        "created_at": datetime.now().isoformat()
    }
]

# Mock participants data
mock_participants = [
    {"name": "Alice", "heartRate": 138, "zone": "Zone 2", "status": "active", "telegram_id": None},
    {"name": "Bob", "heartRate": 155, "zone": "Zone 3", "status": "active", "telegram_id": None},
    {"name": "Carol", "heartRate": 142, "zone": "Zone 2", "status": "active", "telegram_id": None},
    {"name": "David", "heartRate": 134, "zone": "Zone 2", "status": "active", "telegram_id": None}
]

@meetings_bp.route('/meetings', methods=['GET'])
def get_meetings():
    """Get all meetings"""
    return jsonify({
        "success": True,
        "meetings": mock_meetings
    })

@meetings_bp.route('/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    """Get specific meeting details"""
    meeting = next((m for m in mock_meetings if m["id"] == meeting_id), None)
    if not meeting:
        return jsonify({"success": False, "error": "Meeting not found"}), 404
    
    return jsonify({
        "success": True,
        "meeting": meeting,
        "participants": meeting.get('participants', mock_participants),
        "messages": meeting.get('messages', [])
    })

@meetings_bp.route('/meetings', methods=['POST'])
def create_meeting():
    """Create a new meeting"""
    data = request.get_json()
    
    new_meeting = {
        "id": len(mock_meetings) + 1,
        "title": data.get("title", "New Meeting"),
        "time": data.get("time", "TBD"),
        "participants": data.get("participants", 1),
        "status": "upcoming",
        "created_at": datetime.now().isoformat(),
        "participants": [],
        "messages": []
    }
    
    mock_meetings.append(new_meeting)
    
    return jsonify({
        "success": True,
        "meeting": new_meeting
    }), 201

@meetings_bp.route('/meetings/<int:meeting_id>/join', methods=['POST'])
def join_meeting(meeting_id):
    """Join a meeting"""
    meeting = next((m for m in mock_meetings if m["id"] == meeting_id), None)
    if not meeting:
        return jsonify({"success": False, "error": "Meeting not found"}), 404
    
    # Simulate joining the meeting
    meeting["status"] = "active"
    # Add a generic participant if no specific user provided
    return jsonify({
        "success": True,
        "message": "Successfully joined meeting",
        "meeting": meeting,
        "participants": meeting.get('participants', mock_participants)
    })
    
    return jsonify({
        "success": True,
        "message": "Successfully joined meeting",
        "meeting": meeting,
        "participants": mock_participants
    })

@meetings_bp.route('/meetings/<int:meeting_id>/leave', methods=['POST'])
def leave_meeting(meeting_id):
    """Leave a meeting"""
    meeting = next((m for m in mock_meetings if m["id"] == meeting_id), None)
    if not meeting:
        return jsonify({"success": False, "error": "Meeting not found"}), 404
    
    return jsonify({
        "success": True,
        "message": "Successfully left meeting"
    })

@meetings_bp.route('/meetings/<int:meeting_id>/voice-note', methods=['POST'])
def save_voice_note(meeting_id):
    """Save a voice note for a meeting"""
    data = request.get_json()
    
    voice_note = {
        "id": random.randint(1000, 9999),
        "meeting_id": meeting_id,
        "transcript": data.get("transcript", ""),
        "timestamp": datetime.now().isoformat(),
        "duration": data.get("duration", 0)
    }
    
    return jsonify({
        "success": True,
        "voice_note": voice_note
    }), 201


@meetings_bp.route('/meetings/<int:meeting_id>/telegram-join', methods=['POST'])
def telegram_join(meeting_id):
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    name = data.get('name', 'TelegramUser')
    meeting = next((m for m in mock_meetings if m['id'] == meeting_id), None)
    if not meeting:
        return jsonify({"success": False, "error": "Meeting not found"}), 404
    participants = meeting.get('participants', [])
    # if participants is numeric (initial mock data is a count), convert to list
    if isinstance(participants, int):
        participants = []
        meeting['participants'] = participants
    # ensure participant not already in list
    if any(p.get('telegram_id') == telegram_id for p in participants):
        return jsonify({"success": True, "message": "Already joined", "meeting": meeting, "participants": participants})
    participant = {"name": name, "heartRate": random.randint(120,160), "zone": "Zone 2", "status": "active", "telegram_id": telegram_id}
    participants.append(participant)
    meeting['participants'] = participants
    meeting['participants_count'] = len(participants)
    return jsonify({"success": True, "message": "Joined via Telegram", "meeting": meeting, "participants": participants}), 200


@meetings_bp.route('/meetings/<int:meeting_id>/telegram-leave', methods=['POST'])
def telegram_leave(meeting_id):
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    meeting = next((m for m in mock_meetings if m['id'] == meeting_id), None)
    if not meeting:
        return jsonify({"success": False, "error": "Meeting not found"}), 404
    participants = meeting.get('participants', [])
    if isinstance(participants, int):
        participants = []
        meeting['participants'] = participants
    new_parts = [p for p in participants if p.get('telegram_id') != telegram_id]
    meeting['participants'] = new_parts
    meeting['participants_count'] = len(new_parts)
    return jsonify({"success": True, "message": "Left meeting", "meeting": meeting, "participants": new_parts})


@meetings_bp.route('/meetings/<int:meeting_id>/messages', methods=['GET'])
def get_messages(meeting_id):
    meeting = next((m for m in mock_meetings if m['id'] == meeting_id), None)
    if not meeting:
        return jsonify({"success": False, "error": "Meeting not found"}), 404
    return jsonify({"success": True, "messages": meeting.get('messages', [])})


@meetings_bp.route('/meetings/<int:meeting_id>/messages', methods=['POST'])
def post_message(meeting_id):
    data = request.get_json()
    meeting = next((m for m in mock_meetings if m['id'] == meeting_id), None)
    if not meeting:
        return jsonify({"success": False, "error": "Meeting not found"}), 404
    messages = meeting.get('messages', [])
    message = {"id": random.randint(10000,99999), "sender": data.get('sender', 'Unknown'), "text": data.get('text', ''), "timestamp": datetime.now().isoformat()}
    messages.append(message)
    meeting['messages'] = messages
    return jsonify({"success": True, "message": message}), 201

