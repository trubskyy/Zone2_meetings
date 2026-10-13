from flask import Blueprint, jsonify, request
from datetime import datetime
import random

biometrics_bp = Blueprint('biometrics', __name__)

def get_heart_rate_zone(heart_rate):
    """Calculate heart rate zone based on BPM"""
    if heart_rate < 120:
        return "Zone 1"
    elif heart_rate < 150:
        return "Zone 2"
    elif heart_rate < 170:
        return "Zone 3"
    elif heart_rate < 185:
        return "Zone 4"
    else:
        return "Zone 5"

@biometrics_bp.route('/biometrics/current', methods=['GET'])
def get_current_biometrics():
    """Get current biometric data (simulated)"""
    # Simulate real-time heart rate data
    heart_rate = random.randint(130, 160)
    zone = get_heart_rate_zone(heart_rate)
    
    return jsonify({
        "success": True,
        "data": {
            "heart_rate": heart_rate,
            "zone": zone,
            "timestamp": datetime.now().isoformat(),
            "speed": round(random.uniform(5.0, 8.0), 1),  # km/h
            "calories": random.randint(150, 300)
        }
    })

@biometrics_bp.route('/biometrics/history', methods=['GET'])
def get_biometrics_history():
    """Get historical biometric data"""
    # Generate mock historical data
    history = []
    for i in range(10):
        heart_rate = random.randint(125, 165)
        history.append({
            "heart_rate": heart_rate,
            "zone": get_heart_rate_zone(heart_rate),
            "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
            "speed": round(random.uniform(4.5, 8.5), 1),
            "calories": random.randint(100, 350)
        })
    
    return jsonify({
        "success": True,
        "data": history
    })

@biometrics_bp.route('/biometrics/sync', methods=['POST'])
def sync_biometrics():
    """Sync biometric data from wearable devices"""
    data = request.get_json()
    
    # Simulate processing data from Garmin/Apple Health
    processed_data = {
        "heart_rate": data.get("heart_rate", 140),
        "zone": get_heart_rate_zone(data.get("heart_rate", 140)),
        "speed": data.get("speed", 6.0),
        "calories": data.get("calories", 200),
        "timestamp": datetime.now().isoformat(),
        "device": data.get("device", "unknown")
    }
    
    return jsonify({
        "success": True,
        "message": "Biometric data synced successfully",
        "data": processed_data
    })

@biometrics_bp.route('/biometrics/zones/summary', methods=['GET'])
def get_zone_summary():
    """Get summary of time spent in each zone"""
    # Mock zone distribution data
    zone_summary = {
        "Zone 1": {"time_minutes": 15, "percentage": 25},
        "Zone 2": {"time_minutes": 30, "percentage": 50},
        "Zone 3": {"time_minutes": 12, "percentage": 20},
        "Zone 4": {"time_minutes": 3, "percentage": 5},
        "Zone 5": {"time_minutes": 0, "percentage": 0}
    }
    
    return jsonify({
        "success": True,
        "data": zone_summary,
        "total_time_minutes": 60
    })

