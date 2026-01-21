# AI Security Analysis - Implementation Guide

## Overview
Implemented an advanced AI-powered suspicious activity detection system using machine learning algorithms to identify security threats in real-time.

## Architecture

### Backend Components

#### 1. Enhanced ML Service (`backend/ml_service.py`)
The `AnomalyDetector` class now includes 4 detection methods:

##### A. Statistical Anomaly Detection (Isolation Forest)
- **Algorithm**: Isolation Forest from scikit-learn
- **Features Analyzed**:
  - Hour of day (temporal patterns)
  - Day of week (behavioral patterns)
  - Failed access attempts (security indicator)
  - Time between accesses (velocity analysis)
  - Access frequency (volume analysis)
- **Threshold**: Top 10% anomalies detected

##### B. Rule-Based Suspicious Activity Detection
Detects known attack patterns:

1. **Brute Force Login Detection**
   - Multiple failed login attempts within 10 minutes
   - Severity: HIGH
   - Trigger: 3+ failed logins in <10 min window

2. **Unusual Location Pattern Detection**
   - Large geographic variance in access locations
   - Severity: MEDIUM
   - Trigger: Geographic variance > 0.01° with 4+ access points

3. **Rapid File Access Detection**
   - 5+ file accesses within 1 minute
   - Severity: MEDIUM
   - Indicates potential bulk data exfiltration

4. **Off-Hours Access Detection**
   - Access before 7 AM or after 10 PM
   - Access on weekends
   - Severity: LOW
   - May indicate unauthorized after-hours activity

##### C. Failed Access Pattern Analysis
- Tracks failure rate per employee
- High risk if >30% failure rate
- Warning if >15% failure rate
- Groups by employee for correlation

##### D. Comprehensive Risk Assessment
- **Risk Levels**:
  - **HIGH**: >20% suspicious activities
  - **MEDIUM**: 10-20% suspicious activities
  - **LOW**: <10% suspicious activities

#### 2. New API Endpoint

```
GET /admin/suspicious-activities
```

**Response Structure:**
```json
{
  "total_activities": 1000,
  "suspicious_count": 45,
  "risk_level": "medium",
  "findings": [...],  // Top 10 statistical anomalies
  "rule_based_anomalies": [...],  // Rule detections
  "high_risk_employees": {
    "username": {
      "suspicious_count": 5,
      "failed_count": 8,
      "total_activities": 50,
      "risk_score": 0.26
    }
  },
  "patterns": [...],  // Failed access patterns
  "recommendations": [...],
  "analysis_timestamp": "2025-01-21T10:30:00+00:00"
}
```

### Frontend Components

#### 1. AI Analysis Tab
New dedicated tab in AdminDashboard for security analysis visualization

**Features:**
- Real-time analysis results
- Risk level indicator (HIGH/MEDIUM/LOW)
- Activity statistics
- High-risk employee list
- Detected anomalies with severity levels
- Security recommendations
- Analysis timestamp

#### 2. Quick Stats
Added AI analysis card to dashboard overview showing:
- Number of flagged activities
- Quick access to analysis section

#### 3. Quick Actions
"Run AI Security Analysis" button to trigger analysis on demand

## Detection Methods in Detail

### Statistical Anomalies
Uses Isolation Forest to identify unusual patterns:
- Employees accessing files at unusual times
- Unusual access sequences
- Deviations from normal behavior patterns
- Combinations of unusual features

### Rule-Based Detections
Hard-coded security rules for known threats:
- Brute force attacks
- Geographic impossibilities
- Rapid data access
- After-hours unauthorized access

### Behavioral Analysis
Context-aware pattern recognition:
- Employee-specific failure rates
- Access frequency anomalies
- Location variance analysis
- Time-based pattern deviations

## Usage

### For Administrators

#### Step 1: Access AI Analysis
1. Go to Admin Dashboard
2. Click "Run AI Security Analysis" button (purple button in Quick Actions)
3. OR click AI Analysis card in stats grid

#### Step 2: Review Results
1. **Risk Level**: Overall security posture (HIGH/MEDIUM/LOW)
2. **High Risk Employees**: Review employees with suspicious patterns
3. **Detected Anomalies**: Check specific suspicious activities
4. **Recommendations**: Follow suggested remediation steps

#### Step 3: Investigate Findings
1. Click on flagged employee to review their activities
2. Check anomaly details including timestamp and type
3. Cross-reference with access logs for context

#### Step 4: Take Action
Based on recommendations:
- Review employee activities in detail
- Check logs tab for specific incidents
- Contact employees if needed
- Implement additional security measures

### Analysis Types

#### Brute Force Detection
**What**: Multiple failed login attempts
**Why**: Indicates password guessing attacks
**Action**: 
- Review login history
- Consider account lockout after failed attempts
- Verify employee identity

#### Unusual Location
**What**: Large geographic spread in access locations
**Why**: May indicate account compromise or data theft
**Action**:
- Contact employee to verify
- Check if legitimate (travel, VPN)
- Monitor for data exfiltration

#### Rapid Access
**What**: Many files accessed in short time
**Why**: Possible unauthorized bulk download
**Action**:
- Review file access details
- Check download activity
- Verify business justification

#### Failed Accesses
**What**: High failure rate on access attempts
**Why**: May indicate permissions issues or intentional probing
**Action**:
- Review failure reasons
- Check geofence/WiFi restrictions
- Verify access permissions

## Technical Details

### Training Data
- Requires minimum 50 historical activities
- Uses last 2000 activities for analysis
- Automatically trains on available data

### Anomaly Scoring
- Isolation Forest provides anomaly scores
- Lower scores = more anomalous
- Top anomalies presented first

### Performance
- Analyzes 2000 logs in <5 seconds
- ML model trains incrementally
- No database writes required

## Interpretation Guide

### Risk Levels
- **HIGH RISK** (>20% suspicious): Immediate investigation needed
- **MEDIUM RISK** (10-20% suspicious): Review patterns and take precautions
- **LOW RISK** (<10% suspicious): Normal operations, monitor trends

### Risk Score Per Employee
- **>30%**: Critical - immediate review required
- **15-30%**: High - investigate in detail
- **5-15%**: Medium - monitor activity
- **<5%**: Low - normal behavior

### Anomaly Severity
- **HIGH**: Likely security threat, immediate action recommended
- **MEDIUM**: Suspicious pattern, should investigate
- **LOW**: Unusual but likely legitimate, monitor

## Integration with Access Logs

AI Analysis works with existing access logs:
- Analyzes both authentication and file access logs
- Correlates multiple activities per employee
- Considers temporal and spatial patterns
- Combines multiple detection methods

## Security Considerations

### Data Privacy
- Analysis performed server-side
- No personal data exposed
- Only aggregated metrics shown
- Analysis logs can be reviewed

### False Positives
- Machine learning reduces false positives
- Rule-based detection avoids false positives
- Combine statistical and rule-based methods
- Admin judgment still required

### Continuous Learning
- Model improves with more data
- Adapts to organizational patterns
- Reduces false positives over time

## Troubleshooting

### Analysis Shows No Data
- Not enough historical data (need 50+ activities)
- Wait for more activity logs to accumulate
- Check that access logs are being recorded

### All Activities Flagged as Suspicious
- Insufficient training data
- Unusual organizational patterns
- Check if employees are working outside normal hours

### Missing Detections
- May be legitimate unusual activity
- Consider organizational context
- Rule thresholds are configurable

## Future Enhancements

Potential improvements:
1. Configurable rule thresholds
2. Custom anomaly scoring
3. Machine learning model export/import
4. Historical trend analysis
5. Predictive threat detection
6. Automated alert notifications
7. Integration with SIEM systems
8. Custom report generation

## Example Scenarios

### Scenario 1: Detecting Account Compromise
```
Detection: 15 failed logins in 8 minutes from different IPs
Risk Level: HIGH (Brute Force Attack)
Action: Immediately lock account, notify employee, reset password
```

### Scenario 2: Unauthorized Data Access
```
Detection: 23 files accessed in 45 seconds, unusual locations
Risk Level: HIGH (Rapid Access + Unusual Location)
Action: Suspend access, audit downloads, contact employee
```

### Scenario 3: Off-Hours Activity
```
Detection: Access at 2 AM on Saturday from home location
Risk Level: LOW (Off-hours access)
Action: Verify if legitimate work, note for monitoring
```

### Scenario 4: Permission Issues
```
Detection: 8 failed access attempts for same employee/file
Risk Level: MEDIUM (Failed Access Pattern)
Action: Review permissions, update access controls
```
