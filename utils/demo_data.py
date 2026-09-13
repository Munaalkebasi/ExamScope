from datetime import datetime, timedelta
from utils.db import get_db_connection, execute_db

def get_days_ago_str(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

def get_days_ahead_str(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

def load_demo_data(force: bool = True):
    conn = get_db_connection()
    cursor = conn.cursor()

    if force:
        cursor.execute("DELETE FROM topics;")
        cursor.execute("DELETE FROM progress_history;")
        cursor.execute("DELETE FROM activity_logs;")
        cursor.execute("DELETE FROM exams;")

    today_str = datetime.now().strftime("%Y-%m-%d")

    # MATH 232 Midterm 1
    exam_math_id = 'exam-math232-m1'
    cursor.execute("""
        INSERT OR REPLACE INTO exams (id, course_code, exam_name, exam_date, created_at)
        VALUES (?, ?, ?, ?, ?);
    """, (exam_math_id, 'MATH 232', 'Midterm 1', get_days_ahead_str(6), get_days_ago_str(14)))

    # PHYS 101 Final Exam
    exam_phys_id = 'exam-phys101-final'
    cursor.execute("""
        INSERT OR REPLACE INTO exams (id, course_code, exam_name, exam_date, created_at)
        VALUES (?, ?, ?, ?, ?);
    """, (exam_phys_id, 'PHYS 101', 'Final Exam', get_days_ahead_str(14), get_days_ago_str(10)))

    # Topics for MATH 232
    math_topics = [
        ('topic-eigenvalues', exam_math_id, 'Eigenvalues', 35, 42, get_days_ago_str(8), 'Struggling with characteristic equations det(A - λI) = 0 and complex roots.'),
        ('topic-vector-spaces', exam_math_id, 'Vector Spaces', 55, 63, get_days_ago_str(4), 'Subspace proofs and linear independence concept check.'),
        ('topic-matrix-ops', exam_math_id, 'Matrix Operations', 90, 94, get_days_ago_str(1), 'Solid on matrix multiplication, transpose rules, and inverses.'),
        ('topic-linear-trans', exam_math_id, 'Linear Transformations', 48, 56, get_days_ago_str(6), 'Kernel, range, and change of basis matrix transformations.'),
        ('topic-determinants', exam_math_id, 'Determinants', 72, 81, get_days_ago_str(3), 'Cramer rule and cofactor expansion.'),
        ('topic-series-convergence', exam_math_id, 'Series Convergence', 45, 52, get_days_ago_str(8), 'Ratio test vs comparison test formulas.')
    ]

    for t in math_topics:
        cursor.execute("""
            INSERT OR REPLACE INTO topics (id, exam_id, name, confidence, practice_score, last_reviewed, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (t[0], t[1], t[2], t[3], t[4], t[5], t[6], get_days_ago_str(12), t[5]))

    # Topics for PHYS 101
    phys_topics = [
        ('topic-rotational-dyn', exam_phys_id, 'Rotational Dynamics', 40, 48, get_days_ago_str(5), 'Torque and moment of inertia calculations.'),
        ('topic-thermo', exam_phys_id, 'Thermodynamics', 85, 88, get_days_ago_str(2), 'First and second laws, Carnot cycles.'),
        ('topic-shm', exam_phys_id, 'Simple Harmonic Motion', 75, 78, get_days_ago_str(3), 'Pendulums and spring oscillation equations.')
    ]

    for t in phys_topics:
        cursor.execute("""
            INSERT OR REPLACE INTO topics (id, exam_id, name, confidence, practice_score, last_reviewed, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (t[0], t[1], t[2], t[3], t[4], t[5], t[6], get_days_ago_str(8), t[5]))

    # Progress History snapshots for MATH 232
    snapshots = [
        ('snap-1', exam_math_id, 52, 3, 2, 1, 0, get_days_ago_str(12)),
        ('snap-2', exam_math_id, 58, 2, 2, 1, 1, get_days_ago_str(8)),
        ('snap-3', exam_math_id, 63, 1, 3, 1, 1, get_days_ago_str(4)),
        ('snap-4', exam_math_id, 68, 1, 2, 2, 1, today_str)
    ]

    for s in snapshots:
        cursor.execute("""
            INSERT OR REPLACE INTO progress_history (id, exam_id, readiness_score, critical_count, high_count, moderate_count, safe_count, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, s)

    # Activity Logs for MATH 232
    logs = [
        ('act-1', exam_math_id, 'Matrix Operations', 'Reviewed topic and completed quiz (Practice score 94%)', get_days_ago_str(1) + ' 14:30'),
        ('act-2', exam_math_id, 'Determinants', 'Updated practice score from 68% to 81%', get_days_ago_str(3) + ' 11:15'),
        ('act-3', exam_math_id, 'Vector Spaces', 'Marked topic reviewed today', get_days_ago_str(4) + ' 16:45'),
        ('act-4', exam_math_id, 'Eigenvalues', 'Logged initial confidence score (35%)', get_days_ago_str(8) + ' 09:20')
    ]

    for l in logs:
        cursor.execute("""
            INSERT OR REPLACE INTO activity_logs (id, exam_id, topic_name, action, timestamp)
            VALUES (?, ?, ?, ?, ?);
        """, l)

    # Update active exam to MATH 232
    cursor.execute("UPDATE settings SET active_exam_id = ? WHERE id = 1;", (exam_math_id,))

    conn.commit()
    conn.close()
