from utils.risk_calculator import calculate_topic_risk

def get_study_next_recommendation(topics: list, exam_date_str: str) -> dict:
    if not topics:
        return None

    calculations = [calculate_topic_risk(t, exam_date_str, idx, len(topics)) for idx, t in enumerate(topics)]
    highest = max(calculations, key=lambda c: c['risk_score']) if calculations else None

    if not highest:
        return None

    return {
        'topic_id': highest['topic_id'],
        'topic_name': highest['topic_name'],
        'risk_score': highest['risk_score'],
        'risk_level': highest['risk_level'],
        'reason': highest['reason_summary'],
        'action': highest['recommended_action']
    }
