import math
from datetime import datetime

def calculate_days_between(start_str: str, end_str: str) -> int:
    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        return (end_date - start_date).days
    except Exception:
        return 0

def get_days_until_exam(exam_date_str: str) -> int:
    today_str = datetime.now().strftime("%Y-%m-%d")
    return calculate_days_between(today_str, exam_date_str)

def get_days_since_review(last_reviewed_str: str) -> int:
    today_str = datetime.now().strftime("%Y-%m-%d")
    days = calculate_days_between(last_reviewed_str, today_str)
    return max(0, days)

def calculate_topic_risk(topic: dict, exam_date_str: str, topic_index: int = 0, total_topics: int = 1) -> dict:
    confidence = float(topic.get('confidence', 50))
    practice_score = float(topic.get('practice_score', 50))
    last_reviewed = topic.get('last_reviewed', datetime.now().strftime("%Y-%m-%d"))
    
    days_since_review = get_days_since_review(last_reviewed)
    days_until_exam = get_days_until_exam(exam_date_str)

    practice_gap = (100.0 - practice_score) / 100.0
    confidence_gap = (100.0 - confidence) / 100.0
    review_decay = min(1.0, days_since_review / 12.0)

    base_risk = (0.40 * practice_gap + 0.35 * confidence_gap + 0.25 * review_decay) * 100.0

    urgency_multiplier = 1.0
    if days_until_exam <= 14 and base_risk >= 25.0:
        proximity_ratio = max(0.0, 1.0 - (days_until_exam / 14.0))
        urgency_multiplier = 1.0 + 0.25 * proximity_ratio

    raw_risk = min(100.0, round(base_risk * urgency_multiplier))
    risk_score = int(max(0.0, raw_risk))

    if risk_score >= 75:
        risk_level = 'Critical'
    elif risk_score >= 50:
        risk_level = 'High'
    elif risk_score >= 25:
        risk_level = 'Moderate'
    else:
        risk_level = 'Safe'

    max_gap = max(practice_gap, confidence_gap, review_decay)
    topic_name = topic.get('name', 'Topic')

    if days_until_exam <= 5 and base_risk >= 40.0:
        primary_factor = 'exam_imminent'
        reason_summary = f"Exam is only {days_until_exam} day(s) away and performance is below target."
        recommended_action = f"Prioritize high-yield problem solving and formula memorization for {topic_name}."
    elif max_gap == practice_gap and practice_gap >= 0.4:
        primary_factor = 'low_practice'
        reason_summary = f"Practice score is low ({int(practice_score)}%)."
        recommended_action = f"Solve 5–10 practice questions focused on {topic_name} to build problem-solving accuracy."
    elif max_gap == confidence_gap and confidence_gap >= 0.4:
        primary_factor = 'low_confidence'
        reason_summary = f"Self-reported confidence is low ({int(confidence)}%)."
        recommended_action = f"Review core textbook concepts and step-by-step example solutions for {topic_name}."
    elif days_since_review >= 5:
        primary_factor = 'stale_review'
        reason_summary = f"Not reviewed for {days_since_review} days."
        recommended_action = f"Conduct a 15-minute rapid recall session to refresh {topic_name}."
    else:
        primary_factor = 'steady'
        reason_summary = f"Topic performance is steady with recent review ({days_since_review}d ago)."
        recommended_action = f"Maintain retention with periodic quick quizzes."

    # Polar Coordinates Mapping for Radar Scanner
    # Center (0) = Critical (100 risk), Outer edge (1.0) = Safe (0 risk)
    polar_radius = max(0.08, min(0.92, 1.0 - (risk_score / 100.0)))
    
    topic_id_str = str(topic.get('id', ''))
    str_hash = sum(ord(c) for c in topic_id_str) if topic_id_str else 0
    base_angle = (topic_index / float(total_topics)) * 360.0 if total_topics > 0 else 45.0
    polar_angle_deg = (base_angle + (str_hash % 30) - 15 + 360.0) % 360.0

    # Convert to Cartesian (cx=300, cy=300, maxR=240)
    cx, cy, max_r = 300.0, 300.0, 240.0
    angle_rad = math.radians(polar_angle_deg - 90.0) # 0 deg at top
    r = polar_radius * (max_r - 20.0)
    cartesian_x = round(cx + r * math.cos(angle_rad), 1)
    cartesian_y = round(cy + r * math.sin(angle_rad), 1)

    return {
        'topic_id': topic.get('id'),
        'topic_name': topic_name,
        'risk_score': risk_score,
        'risk_level': risk_level,
        'days_since_review': days_since_review,
        'days_until_exam': days_until_exam,
        'confidence_gap': round(confidence_gap * 100),
        'practice_gap': round(practice_gap * 100),
        'primary_factor': primary_factor,
        'reason_summary': reason_summary,
        'recommended_action': recommended_action,
        'polar_radius': polar_radius,
        'polar_angle_deg': round(polar_angle_deg, 1),
        'x': cartesian_x,
        'y': cartesian_y
    }

def calculate_readiness_overview(topics: list, exam_date_str: str) -> dict:
    if not topics:
        return {
            'readiness_score': 100,
            'total_topics': 0,
            'critical_count': 0,
            'high_count': 0,
            'moderate_count': 0,
            'safe_count': 0,
            'top_risk_topic': None,
            'top_risk_calc': None,
            'study_next_recommendation': None
        }

    calculations = [calculate_topic_risk(t, exam_date_str, idx, len(topics)) for idx, t in enumerate(topics)]

    total_risk_sum = sum(c['risk_score'] for c in calculations)
    avg_risk = total_risk_sum / float(len(topics))
    readiness_score = max(0, min(100, int(round(100.0 - avg_risk))))

    critical_count = sum(1 for c in calculations if c['risk_level'] == 'Critical')
    high_count = sum(1 for c in calculations if c['risk_level'] == 'High')
    moderate_count = sum(1 for c in calculations if c['risk_level'] == 'Moderate')
    safe_count = sum(1 for c in calculations if c['risk_level'] == 'Safe')

    max_risk = -1
    top_topic = None
    top_calc = None

    for idx, t in enumerate(topics):
        calc = calculations[idx]
        if calc['risk_score'] > max_risk:
            max_risk = calc['risk_score']
            top_topic = t
            top_calc = calc

    study_next_recommendation = None
    if top_topic and top_calc:
        study_next_recommendation = {
            'topic_name': top_topic['name'],
            'reason': top_calc['reason_summary'],
            'action': top_calc['recommended_action']
        }

    return {
        'readiness_score': readiness_score,
        'total_topics': len(topics),
        'critical_count': critical_count,
        'high_count': high_count,
        'moderate_count': moderate_count,
        'safe_count': safe_count,
        'top_risk_topic': top_topic,
        'top_risk_calc': top_calc,
        'study_next_recommendation': study_next_recommendation,
        'topic_calculations': calculations
    }
