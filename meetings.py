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
    {"name": "Alice", "heartRate": 138, "zone": "Zone 2", "status": "active"},
    {"name": "Bob", "heartRate": 155, "zone": "Zone 3", "status": "active"},
    {"name": "Carol", "heartRate": 142, "zone": "Zone 2", "status": "active"},
    {"name": "David", "heartRate": 134, "zone": "Zone 2", "status": "active"}
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
        "participants": mock_participants
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
        "created_at": datetime.now().isoformat()
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

