from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, time
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)

class GeofenceValidator:
    """
    Validate employee access based on geofencing, WiFi, and time conditions
    """
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        Returns distance in meters
        """
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        distance = R * c
        return distance
    
    @staticmethod
    def validate_location(employee_lat: float, employee_lon: float, 
                         config_lat: float, config_lon: float, radius: float) -> Tuple[bool, str]:
        """
        Validate if employee is within allowed geofence
        """
        distance = GeofenceValidator.calculate_distance(
            employee_lat, employee_lon, config_lat, config_lon
        )
        
        if distance <= radius:
            return True, f"Location validated (distance: {distance:.2f}m)"
        else:
            return False, f"Outside allowed area (distance: {distance:.2f}m, max: {radius}m)"
    
    @staticmethod
    def validate_wifi(employee_ssid: str, allowed_ssid: str) -> Tuple[bool, str]:
        """
        Validate if employee is connected to allowed WiFi
        """
        if not employee_ssid:
            return False, "WiFi SSID not provided"
        
        # Accept case-insensitive and substring matches to handle SSID variations
        emp = employee_ssid.lower() if employee_ssid else ''
        allowed = allowed_ssid.lower() if allowed_ssid else ''
        if emp == allowed or emp in allowed or allowed in emp:
            return True, f"WiFi validated ({employee_ssid})"
        else:
            return False, f"Unauthorized WiFi network ({employee_ssid})"
    
    @staticmethod
    def validate_time(start_time: str, end_time: str) -> Tuple[bool, str]:
        """
        Validate if current time is within allowed hours
        start_time and end_time format: HH:MM
        """
        # Parse HH:MM into time objects and compare current local time
        try:
            start_obj = datetime.strptime(start_time, "%H:%M").time()
            end_obj = datetime.strptime(end_time, "%H:%M").time()
        except Exception as e:
            logger.error(f"Invalid time format in geofence config: {e}")
            return False, f"Invalid time format in config: {start_time}-{end_time}"

        now = datetime.now()
        current = now.time()

        # Handle window that does not wrap midnight
        if start_obj <= end_obj:
            if start_obj <= current <= end_obj:
                return True, f"Time validated ({current.strftime('%H:%M')})"
            else:
                return False, f"Outside allowed hours (current: {current.strftime('%H:%M')}, allowed: {start_time}-{end_time})"
        else:
            # Window wraps midnight (e.g., 22:00 - 06:00)
            if current >= start_obj or current <= end_obj:
                return True, f"Time validated ({current.strftime('%H:%M')})"
            else:
                return False, f"Outside allowed hours (current: {current.strftime('%H:%M')}, allowed: {start_time}-{end_time})"
    
    @staticmethod
    def validate_access(request: Dict, config: Dict, wfh_approved: bool = False) -> Dict:
        """
        Complete validation of access request
        Returns dict with validation results
        """
        if wfh_approved:
            return {
                "allowed": True,
                "reason": "Work from home approved",
                "validations": {
                    "location": "bypassed",
                    "wifi": "bypassed",
                    "time": "bypassed"
                }
            }
        
        validations = {}
        reasons = []
        
        # Validate location
        lat = request.get('latitude', None)
        lon = request.get('longitude', None)
        if lat is None or lon is None:
            location_valid = False
            location_msg = "Location not provided"
        else:
            location_valid, location_msg = GeofenceValidator.validate_location(
                lat,
                lon,
                config.get('latitude', 0),
                config.get('longitude', 0),
                config.get('radius', 100)
            )
        validations['location'] = location_msg
        if not location_valid:
            reasons.append(location_msg)
        
        # Validate WiFi
        wifi_valid, wifi_msg = GeofenceValidator.validate_wifi(
            request.get('wifi_ssid', ''),
            config.get('allowed_ssid', '')
        )
        validations['wifi'] = wifi_msg
        if not wifi_valid:
            reasons.append(wifi_msg)
        
        # Validate time
        time_valid, time_msg = GeofenceValidator.validate_time(
            config.get('start_time', '09:00'),
            config.get('end_time', '17:00')
        )
        validations['time'] = time_msg
        if not time_valid:
            reasons.append(time_msg)
        
        allowed = location_valid and wifi_valid and time_valid
        
        return {
            "allowed": allowed,
            "reason": "Access granted" if allowed else "; ".join(reasons),
            "validations": validations
        }
