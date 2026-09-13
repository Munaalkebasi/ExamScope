from datetime import datetime
from utils.db import query_db, execute_db

def record_progress_snapshot(exam_id: str, readiness_overview: dict):
    if not exam_id or readiness_overview['total_topics'] == 0:
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Check if snapshot recorded today
    existing = query_db("SELECT id FROM progress_history WHERE exam_id = ? AND recorded_at = ?;", (exam_id, today_str), one=True)
    if existing:
        execute_db("""
            UPDATE progress_history 
            SET readiness_score = ?, critical_count = ?, high_count = ?, moderate_count = ?, safe_count = ?
            WHERE id = ?;
        """, (
            readiness_overview['readiness_score'],
            readiness_overview['critical_count'],
            readiness_overview['high_count'],
            readiness_overview['moderate_count'],
            readiness_overview['safe_count'],
            existing['id']
        ))
    else:
        snapshot_id = f"snap-{int(datetime.now().timestamp()*1000)}"
        execute_db("""
            INSERT INTO progress_history (id, exam_id, readiness_score, critical_count, high_count, moderate_count, safe_count, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            snapshot_id,
            exam_id,
            readiness_overview['readiness_score'],
            readiness_overview['critical_count'],
            readiness_overview['high_count'],
            readiness_overview['moderate_count'],
            readiness_overview['safe_count'],
            today_str
        ))

def log_activity(exam_id: str, topic_name: str, action: str):
    if not exam_id:
        return
    log_id = f"log-{int(datetime.now().timestamp()*1000)}"
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    execute_db("""
        INSERT INTO activity_logs (id, exam_id, topic_name, action, timestamp)
        VALUES (?, ?, ?, ?, ?);
    """, (log_id, exam_id, topic_name, action, timestamp_str))
