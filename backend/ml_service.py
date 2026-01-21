from sklearn.ensemble import IsolationForest
from collections import defaultdict, Counter
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    ML-based anomaly detection for employee behavior and access patterns
    Uses multiple detection methods:
    1. Isolation Forest for statistical anomalies
    2. Rule-based detection for suspicious patterns
    3. Behavioral analysis for unusual activities
    """
    
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.is_trained = False
        self.employee_profiles = {}  # Store normal patterns per employee
    
    def extract_features(self, activities: List[Dict]) -> np.ndarray:
        """
        Extract advanced features from activity logs
        Features:
        - Hour of day (0-23)
        - Day of week (0-6)
        - Failed access attempts (0 or 1)
        - Access frequency
        - Time since last access
        """
        if not activities:
            return np.array([])
        
        features = []
        for i, activity in enumerate(activities):
            timestamp = activity.get('timestamp')
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now(timezone.utc)
            elif isinstance(timestamp, datetime) and timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            is_failed = 0 if activity.get('success', True) else 1
            
            # Time since last access (normalized to hours)
            time_since_last = 0
            if i > 0:
                prev_timestamp = activities[i-1].get('timestamp')
                if isinstance(prev_timestamp, str):
                    try:
                        prev_timestamp = datetime.fromisoformat(prev_timestamp.replace('Z', '+00:00'))
                    except:
                        prev_timestamp = timestamp
                if isinstance(prev_timestamp, datetime) and prev_timestamp.tzinfo is None:
                    prev_timestamp = prev_timestamp.replace(tzinfo=timezone.utc)
                
                time_diff = (timestamp - prev_timestamp).total_seconds() / 3600
                time_since_last = min(time_diff, 24)  # Cap at 24 hours
            
            features.append([
                hour,
                day_of_week,
                is_failed,
                time_since_last,
                1  # access count
            ])
        
        return np.array(features) if features else np.array([]).reshape(0, 5)
    
    def train(self, activities: List[Dict]) -> bool:
        """
        Train the anomaly detection model on historical data
        """
        if len(activities) < 10:
            logger.warning(f"Insufficient data for training: {len(activities)} activities")
            return False
        
        features = self.extract_features(activities)
        
        if len(features) == 0:
            return False
        
        try:
            self.model.fit(features)
            self.is_trained = True
            logger.info(f"Model trained with {len(features)} samples")
            return True
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    def detect_statistical_anomalies(self, activities: List[Dict]) -> Dict[str, any]:
        """
        Detect statistical anomalies using Isolation Forest
        """
        if not self.is_trained or len(activities) == 0:
            return {"anomalies": [], "scores": []}
        
        features = self.extract_features(activities)
        
        if len(features) == 0:
            return {"anomalies": [], "scores": []}
        
        try:
            predictions = self.model.predict(features)
            scores = self.model.score_samples(features)
            
            anomalies = [
                {
                    "index": i,
                    "activity": activities[i],
                    "anomaly_score": float(scores[i]),
                    "is_anomaly": bool(pred == -1)
                }
                for i, pred in enumerate(predictions)
            ]
            
            return {
                "anomalies": anomalies,
                "count": sum(1 for a in anomalies if a["is_anomaly"])
            }
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {"anomalies": [], "scores": []}
    
    def detect_rule_based_suspicious_activities(self, activities: List[Dict]) -> List[Dict]:
        """
        Rule-based detection for known suspicious patterns
        """
        suspicious = []
        
        if not activities:
            return suspicious
        
        # Rule 1: Multiple failed login attempts in short time
        failed_logins = [a for a in activities if a.get('action') == 'login_failed']
        for i, login in enumerate(failed_logins):
            if i >= 2:
                prev_time = datetime.fromisoformat(failed_logins[i-2].get('timestamp', '').replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(login.get('timestamp', '').replace('Z', '+00:00'))
                
                if (curr_time - prev_time).total_seconds() < 600:  # 10 minutes
                    suspicious.append({
                        "activity": login,
                        "type": "brute_force_login",
                        "severity": "high",
                        "description": f"Multiple failed login attempts within 10 minutes for {login.get('employee_username')}"
                    })
        
        # Rule 2: Access from unusual locations
        file_accesses = [a for a in activities if a.get('log_type') == 'file_access']
        location_patterns = defaultdict(list)
        for access in file_accesses:
            username = access.get('employee_username')
            location_patterns[username].append(access.get('location', {}))
        
        for username, locations in location_patterns.items():
            if len(locations) > 2:
                # Calculate location variance
                lats = [loc.get('lat', 0) for loc in locations if loc and 'lat' in loc]
                lons = [loc.get('lon', 0) for loc in locations if loc and 'lon' in loc]
                
                if lats and lons:
                    lat_variance = np.var(lats) if len(lats) > 1 else 0
                    lon_variance = np.var(lons) if len(lons) > 1 else 0
                    
                    if (lat_variance > 0.01 or lon_variance > 0.01) and len(locations) > 3:
                        suspicious.append({
                            "activity": file_accesses[-1],
                            "type": "unusual_location_pattern",
                            "severity": "medium",
                            "description": f"Large geographic variance detected for {username}"
                        })
        
        # Rule 3: Rapid file access
        for username in set(a.get('employee_username') for a in file_accesses):
            user_accesses = [a for a in file_accesses if a.get('employee_username') == username]
            if len(user_accesses) >= 5:
                for i in range(4, len(user_accesses)):
                    # Check last 5 accesses
                    five_accesses = user_accesses[i-4:i+1]
                    timestamps = []
                    for access in five_accesses:
                        try:
                            ts = datetime.fromisoformat(access.get('timestamp', '').replace('Z', '+00:00'))
                            timestamps.append(ts)
                        except:
                            pass
                    
                    if len(timestamps) == 5:
                        time_span = (timestamps[-1] - timestamps[0]).total_seconds()
                        if time_span < 60 and time_span > 0:  # 5 accesses in less than 1 minute
                            suspicious.append({
                                "activity": user_accesses[-1],
                                "type": "rapid_access",
                                "severity": "medium",
                                "description": f"Rapid file access detected: {5} files in {time_span:.0f} seconds"
                            })
                            break
        
        # Rule 4: Off-hours access
        for activity in activities:
            timestamp = activity.get('timestamp')
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    continue
            
            if activity.get('log_type') == 'file_access':
                hour = timestamp.hour
                day = timestamp.weekday()
                
                # Off-hours: weekday before 7 AM or after 10 PM, or weekend
                if (hour < 7 or hour > 22) or (day >= 5):
                    suspicious.append({
                        "activity": activity,
                        "type": "off_hours_access",
                        "severity": "low",
                        "description": f"File access outside normal business hours (${hour}:00)"
                    })
        
        return suspicious
    
    def detect_failed_access_patterns(self, activities: List[Dict]) -> List[Dict]:
        """
        Detect patterns in failed access attempts
        """
        patterns = []
        
        failed_attempts = [a for a in activities if not a.get('success', True)]
        if not failed_attempts:
            return patterns
        
        # Group by employee
        by_employee = defaultdict(list)
        for attempt in failed_attempts:
            by_employee[attempt.get('employee_username')].append(attempt)
        
        for username, attempts in by_employee.items():
            if len(attempts) > 2:
                # High failure rate
                recent_activities = [a for a in activities if a.get('employee_username') == username]
                if recent_activities:
                    failure_rate = len(attempts) / len(recent_activities)
                    
                    patterns.append({
                        "username": username,
                        "metric": "failure_rate",
                        "value": failure_rate,
                        "threshold": 0.3,
                        "status": "anomaly" if failure_rate > 0.3 else "warning" if failure_rate > 0.15 else "normal",
                        "description": f"{username} has {failure_rate*100:.1f}% failed access rate ({len(attempts)}/{len(recent_activities)})"
                    })
        
        return patterns
    
    def analyze_suspicious_activities(self, activities: List[Dict]) -> Dict:
        """
        Comprehensive analysis of all suspicious activities
        Combines statistical and rule-based detection
        """
        if not activities:
            return {
                "total_activities": 0,
                "suspicious_count": 0,
                "risk_level": "low",
                "findings": [],
                "high_risk_employees": [],
                "patterns": [],
                "recommendations": []
            }
        
        # Statistical anomalies
        stat_results = self.detect_statistical_anomalies(activities)
        stat_anomalies = [a for a in stat_results.get("anomalies", []) if a.get("is_anomaly")]
        
        # Rule-based detection
        rule_anomalies = self.detect_rule_based_suspicious_activities(activities)
        
        # Failed access patterns
        failure_patterns = self.detect_failed_access_patterns(activities)
        
        # Calculate risk level
        total_suspicious = len(stat_anomalies) + len(rule_anomalies)
        risk_ratio = total_suspicious / len(activities) if activities else 0
        
        if risk_ratio > 0.2:
            risk_level = "high"
        elif risk_ratio > 0.1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Identify high-risk employees
        high_risk_employees = {}
        for employee in set(a.get('employee_username') for a in activities):
            emp_activities = [a for a in activities if a.get('employee_username') == employee]
            emp_suspicious = [s for s in rule_anomalies if s.get('activity', {}).get('employee_username') == employee]
            emp_failed = len([a for a in emp_activities if not a.get('success', True)])
            
            if emp_suspicious or (emp_failed > 2):
                high_risk_employees[employee] = {
                    "suspicious_count": len(emp_suspicious),
                    "failed_count": emp_failed,
                    "total_activities": len(emp_activities),
                    "risk_score": (len(emp_suspicious) + emp_failed) / len(emp_activities) if emp_activities else 0
                }
        
        # Sort by risk score
        high_risk_employees = dict(sorted(
            high_risk_employees.items(),
            key=lambda x: x[1]['risk_score'],
            reverse=True
        )[:10])  # Top 10
        
        # Generate recommendations
        recommendations = []
        if total_suspicious > 0:
            recommendations.append("Review flagged activities in detail")
        if any(emp['failed_count'] > 5 for emp in high_risk_employees.values()):
            recommendations.append("Consider implementing account lockout after repeated failed attempts")
        if any(s.get('type') == 'brute_force_login' for s in rule_anomalies):
            recommendations.append("Possible brute force attack detected - review authentication logs")
        if any(s.get('type') == 'rapid_access' for s in rule_anomalies):
            recommendations.append("Investigate rapid file access patterns")
        
        return {
            "total_activities": len(activities),
            "suspicious_count": total_suspicious,
            "risk_level": risk_level,
            "findings": stat_anomalies[:10],  # Top 10 statistical anomalies
            "rule_based_anomalies": rule_anomalies[:20],  # Top 20 rule-based detections
            "high_risk_employees": high_risk_employees,
            "patterns": failure_patterns,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
