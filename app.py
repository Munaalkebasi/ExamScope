import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response

from utils.db import init_db, query_db, execute_db
from utils.risk_calculator import calculate_readiness_overview, get_days_until_exam, calculate_topic_risk
from utils.analytics import record_progress_snapshot, log_activity
from utils.demo_data import load_demo_data

app = Flask(__name__)

# Initialize SQLite database on startup
init_db()

# Auto-seed demo data if database is empty on start
exams_check = query_db("SELECT COUNT(*) as count FROM exams;", one=True)
if not exams_check or exams_check['count'] == 0:
    load_demo_data(force=True)

def get_app_context():
    """Helper to fetch common app context (settings, active_exam, exams_list, days_remaining)."""
    settings = query_db("SELECT * FROM settings WHERE id = 1;", one=True) or {'theme': 'dark', 'active_exam_id': None}
    exams = query_db("SELECT * FROM exams ORDER BY created_at DESC;")
    
    active_exam_id = settings.get('active_exam_id')
    active_exam = None
    
    if active_exam_id:
        active_exam = query_db("SELECT * FROM exams WHERE id = ?;", (active_exam_id,), one=True)
    
    if not active_exam and exams:
        active_exam = exams[0]
        execute_db("UPDATE settings SET active_exam_id = ? WHERE id = 1;", (active_exam['id'],))
        settings['active_exam_id'] = active_exam['id']

    days_remaining = get_days_until_exam(active_exam['exam_date']) if active_exam else 0

    return {
        'settings': settings,
        'exams': exams,
        'active_exam': active_exam,
        'days_remaining': days_remaining
    }

@app.route('/')
def index():
    ctx = get_app_context()
    active_exam = ctx['active_exam']
    
    topics = []
    readiness_overview = None
    top_risk_topics = []

    if active_exam:
        topics = query_db("SELECT * FROM topics WHERE exam_id = ? ORDER BY created_at DESC;", (active_exam['id'],))
        readiness_overview = calculate_readiness_overview(topics, active_exam['exam_date'])

        # Record progress snapshot for today
        if topics:
            record_progress_snapshot(active_exam['id'], readiness_overview)

        # Top 3 risk topics
        if readiness_overview.get('topic_calculations'):
            sorted_calcs = sorted(readiness_overview['topic_calculations'], key=lambda x: x['risk_score'], reverse=True)
            top_risk_topics = sorted_calcs[:3]

    return render_template(
        'radar.html',
        active_tab='radar',
        settings=ctx['settings'],
        exams=ctx['exams'],
        active_exam=active_exam,
        topics=topics,
        readiness=readiness_overview,
        days_remaining=ctx['days_remaining'],
        top_risk_topics=top_risk_topics
    )

@app.route('/topics')
def topics_page():
    ctx = get_app_context()
    active_exam = ctx['active_exam']
    
    search_query = request.args.get('search', '').strip().lower()
    sort_by = request.args.get('sort', 'highest_risk')
    filter_level = request.args.get('filter', 'all').lower()

    topics = []
    processed_topics = []
    readiness_overview = None

    if active_exam:
        topics = query_db("SELECT * FROM topics WHERE exam_id = ?;", (active_exam['id'],))
        readiness_overview = calculate_readiness_overview(topics, active_exam['exam_date'])
        
        calcs = readiness_overview.get('topic_calculations', [])
        
        for idx, t in enumerate(topics):
            calc = calcs[idx] if idx < len(calcs) else calculate_topic_risk(t, active_exam['exam_date'])
            
            # Filtering
            matches_search = (search_query in t['name'].lower()) or (t['notes'] and search_query in t['notes'].lower())
            matches_filter = (filter_level == 'all') or (calc['risk_level'].lower() == filter_level)

            if matches_search and matches_filter:
                processed_topics.append({
                    'topic': t,
                    'calc': calc
                })

        # Sorting
        if sort_by == 'highest_risk':
            processed_topics.sort(key=lambda x: x['calc']['risk_score'], reverse=True)
        elif sort_by == 'lowest_risk':
            processed_topics.sort(key=lambda x: x['calc']['risk_score'])
        elif sort_by == 'lowest_confidence':
            processed_topics.sort(key=lambda x: x['topic']['confidence'])
        elif sort_by == 'lowest_practice':
            processed_topics.sort(key=lambda x: x['topic']['practice_score'])
        elif sort_by == 'least_reviewed':
            processed_topics.sort(key=lambda x: x['calc']['days_since_review'], reverse=True)
        elif sort_by == 'name':
            processed_topics.sort(key=lambda x: x['topic']['name'].lower())

    return render_template(
        'topics.html',
        active_tab='topics',
        settings=ctx['settings'],
        exams=ctx['exams'],
        active_exam=active_exam,
        topics=processed_topics,
        search_query=search_query,
        sort_by=sort_by,
        filter_level=filter_level,
        days_remaining=ctx['days_remaining'],
        readiness=readiness_overview
    )

@app.route('/progress')
def progress_page():
    ctx = get_app_context()
    active_exam = ctx['active_exam']

    snapshots = []
    activity_logs = []
    readiness_overview = None

    if active_exam:
        topics = query_db("SELECT * FROM topics WHERE exam_id = ?;", (active_exam['id'],))
        readiness_overview = calculate_readiness_overview(topics, active_exam['exam_date'])
        snapshots = query_db("SELECT * FROM progress_history WHERE exam_id = ? ORDER BY recorded_at ASC;", (active_exam['id'],))
        activity_logs = query_db("SELECT * FROM activity_logs WHERE exam_id = ? ORDER BY timestamp DESC LIMIT 20;", (active_exam['id'],))

    return render_template(
        'progress.html',
        active_tab='progress',
        settings=ctx['settings'],
        exams=ctx['exams'],
        active_exam=active_exam,
        snapshots=snapshots,
        activity_logs=activity_logs,
        days_remaining=ctx['days_remaining'],
        readiness=readiness_overview
    )

@app.route('/settings')
def settings_page():
    ctx = get_app_context()
    return render_template(
        'settings.html',
        active_tab='settings',
        settings=ctx['settings'],
        exams=ctx['exams'],
        days_remaining=ctx['days_remaining'],
        active_exam=ctx['active_exam']
    )

# --------------------------
# API & ACTION ENDPOINTS
# --------------------------

@app.route('/exams/select/<exam_id>', methods=['POST'])
def select_exam(exam_id):
    execute_db("UPDATE settings SET active_exam_id = ? WHERE id = 1;", (exam_id,))
    return redirect(request.referrer or url_for('index'))

@app.route('/exams/create', methods=['POST'])
def create_exam():
    course_code = request.form.get('course_code', '').strip().upper()
    exam_name = request.form.get('exam_name', '').strip()
    exam_date = request.form.get('exam_date', '').strip()

    if course_code and exam_name and exam_date:
        exam_id = f"exam-{int(datetime.now().timestamp()*1000)}"
        created_at = datetime.now().strftime("%Y-%m-%d")
        execute_db("""
            INSERT INTO exams (id, course_code, exam_name, exam_date, created_at)
            VALUES (?, ?, ?, ?, ?);
        """, (exam_id, course_code, exam_name, exam_date, created_at))
        execute_db("UPDATE settings SET active_exam_id = ? WHERE id = 1;", (exam_id,))

    return redirect(request.referrer or url_for('index'))

@app.route('/exams/edit/<exam_id>', methods=['POST'])
def edit_exam(exam_id):
    course_code = request.form.get('course_code', '').strip().upper()
    exam_name = request.form.get('exam_name', '').strip()
    exam_date = request.form.get('exam_date', '').strip()

    if course_code and exam_name and exam_date:
        execute_db("""
            UPDATE exams
            SET course_code = ?, exam_name = ?, exam_date = ?
            WHERE id = ?;
        """, (course_code, exam_name, exam_date, exam_id))

    return redirect(request.referrer or url_for('index'))

@app.route('/exams/delete/<exam_id>', methods=['POST'])
def delete_exam(exam_id):
    execute_db("DELETE FROM exams WHERE id = ?;", (exam_id,))
    
    ctx = get_app_context()
    if ctx['exams']:
        execute_db("UPDATE settings SET active_exam_id = ? WHERE id = 1;", (ctx['exams'][0]['id'],))
    else:
        execute_db("UPDATE settings SET active_exam_id = NULL WHERE id = 1;")

    return redirect(url_for('index'))

@app.route('/topics/create', methods=['POST'])
def create_topic():
    ctx = get_app_context()
    active_exam = ctx['active_exam']
    if not active_exam:
        return redirect(url_for('index'))

    name = request.form.get('name', '').strip()
    confidence = int(request.form.get('confidence', 50))
    practice_score = int(request.form.get('practice_score', 50))
    last_reviewed = request.form.get('last_reviewed', datetime.now().strftime("%Y-%m-%d"))
    notes = request.form.get('notes', '').strip()

    if name:
        topic_id = f"topic-{int(datetime.now().timestamp()*1000)}"
        today_str = datetime.now().strftime("%Y-%m-%d")
        execute_db("""
            INSERT INTO topics (id, exam_id, name, confidence, practice_score, last_reviewed, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (topic_id, active_exam['id'], name, confidence, practice_score, last_reviewed, notes, today_str, today_str))
        
        log_activity(active_exam['id'], name, "Added topic to exam radar")

    return redirect(request.referrer or url_for('index'))

@app.route('/topics/edit/<topic_id>', methods=['POST'])
def edit_topic(topic_id):
    topic = query_db("SELECT * FROM topics WHERE id = ?;", (topic_id,), one=True)
    if not topic:
        return redirect(request.referrer or url_for('index'))

    name = request.form.get('name', topic['name']).strip()
    confidence = int(request.form.get('confidence', topic['confidence']))
    practice_score = int(request.form.get('practice_score', topic['practice_score']))
    last_reviewed = request.form.get('last_reviewed', topic['last_reviewed'])
    notes = request.form.get('notes', topic['notes']).strip()

    today_str = datetime.now().strftime("%Y-%m-%d")

    execute_db("""
        UPDATE topics
        SET name = ?, confidence = ?, practice_score = ?, last_reviewed = ?, notes = ?, updated_at = ?
        WHERE id = ?;
    """, (name, confidence, practice_score, last_reviewed, notes, today_str, topic_id))

    log_activity(topic['exam_id'], name, f"Updated parameters (Confidence: {confidence}%, Practice: {practice_score}%)")

    return redirect(request.referrer or url_for('index'))

@app.route('/topics/delete/<topic_id>', methods=['POST'])
def delete_topic(topic_id):
    execute_db("DELETE FROM topics WHERE id = ?;", (topic_id,))
    return redirect(request.referrer or url_for('index'))

@app.route('/topics/review/<topic_id>', methods=['POST'])
def review_topic(topic_id):
    topic = query_db("SELECT * FROM topics WHERE id = ?;", (topic_id,), one=True)
    if topic:
        today_str = datetime.now().strftime("%Y-%m-%d")
        execute_db("UPDATE topics SET last_reviewed = ?, updated_at = ? WHERE id = ?;", (today_str, today_str, topic_id))
        log_activity(topic['exam_id'], topic['name'], "Marked reviewed today")
    return redirect(request.referrer or url_for('index'))

@app.route('/settings/theme', methods=['POST'])
def update_theme():
    theme = request.form.get('theme', 'dark')
    if theme in ['dark', 'light', 'system']:
        execute_db("UPDATE settings SET theme = ? WHERE id = 1;", (theme,))
    return redirect(request.referrer or url_for('settings_page'))

@app.route('/demo/load', methods=['POST'])
def load_demo():
    load_demo_data(force=True)
    return redirect(url_for('index'))

@app.route('/data/clear', methods=['POST'])
def clear_data():
    execute_db("DELETE FROM topics;")
    execute_db("DELETE FROM progress_history;")
    execute_db("DELETE FROM activity_logs;")
    execute_db("DELETE FROM exams;")
    execute_db("UPDATE settings SET active_exam_id = NULL WHERE id = 1;")
    return redirect(url_for('index'))

@app.route('/data/export')
def export_data():
    exams = query_db("SELECT * FROM exams;")
    topics = query_db("SELECT * FROM topics;")
    progress = query_db("SELECT * FROM progress_history;")
    logs = query_db("SELECT * FROM activity_logs;")
    settings = query_db("SELECT * FROM settings WHERE id = 1;", one=True)

    data = {
        'exams': exams,
        'topics': topics,
        'progress_history': progress,
        'activity_logs': logs,
        'settings': settings,
        'exported_at': datetime.now().isoformat()
    }
    
    json_str = json.dumps(data, indent=2)
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename=ExamScope_Backup_{datetime.now().strftime('%Y-%m-%d')}.json"}
    )

@app.route('/data/import', methods=['POST'])
def import_data():
    file = request.files.get('file')
    if file and file.filename:
        try:
            content = json.load(file)

            # Strict validation: content must contain exams and topics keys
            if not isinstance(content, dict) or 'exams' not in content or 'topics' not in content:
                return redirect(url_for('settings_page'))

            exams = content.get('exams')
            topics = content.get('topics')
            progress = content.get('progress_history', [])
            logs = content.get('activity_logs', [])

            if not isinstance(exams, list) or not isinstance(topics, list):
                return redirect(url_for('settings_page'))

            # Validate exams schema
            for e in exams:
                if not all(k in e for k in ('id', 'course_code', 'exam_name', 'exam_date', 'created_at')):
                    return redirect(url_for('settings_page'))

            # Validate topics schema
            for t in topics:
                if not all(k in t for k in ('id', 'exam_id', 'name', 'confidence', 'practice_score', 'last_reviewed')):
                    return redirect(url_for('settings_page'))

            # Clear current data only if validation passed
            execute_db("DELETE FROM topics;")
            execute_db("DELETE FROM progress_history;")
            execute_db("DELETE FROM activity_logs;")
            execute_db("DELETE FROM exams;")

            for e in exams:
                execute_db("""
                    INSERT INTO exams (id, course_code, exam_name, exam_date, created_at)
                    VALUES (?, ?, ?, ?, ?);
                """, (e['id'], e['course_code'], e['exam_name'], e['exam_date'], e['created_at']))

            for t in topics:
                execute_db("""
                    INSERT INTO topics (id, exam_id, name, confidence, practice_score, last_reviewed, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    t['id'], t['exam_id'], t['name'], int(t['confidence']), int(t['practice_score']),
                    t['last_reviewed'], t.get('notes', ''), t.get('created_at', datetime.now().strftime("%Y-%m-%d")),
                    t.get('updated_at', datetime.now().strftime("%Y-%m-%d"))
                ))

            for p in progress:
                if isinstance(p, dict) and all(k in p for k in ('id', 'exam_id', 'readiness_score', 'recorded_at')):
                    execute_db("""
                        INSERT INTO progress_history (id, exam_id, readiness_score, critical_count, high_count, moderate_count, safe_count, recorded_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        p['id'], p['exam_id'], int(p['readiness_score']),
                        int(p.get('critical_count', 0)), int(p.get('high_count', 0)),
                        int(p.get('moderate_count', 0)), int(p.get('safe_count', 0)),
                        p['recorded_at']
                    ))

            for l in logs:
                if isinstance(l, dict) and all(k in l for k in ('id', 'exam_id', 'topic_name', 'action', 'timestamp')):
                    execute_db("""
                        INSERT INTO activity_logs (id, exam_id, topic_name, action, timestamp)
                        VALUES (?, ?, ?, ?, ?);
                    """, (l['id'], l['exam_id'], l['topic_name'], l['action'], l['timestamp']))

            if exams:
                execute_db("UPDATE settings SET active_exam_id = ? WHERE id = 1;", (exams[0]['id'],))
            else:
                execute_db("UPDATE settings SET active_exam_id = NULL WHERE id = 1;")

        except Exception as err:
            print(f"Import error: {err}")

    return redirect(url_for('settings_page'))

@app.route('/api/topic/<topic_id>')
def get_topic_detail(topic_id):
    topic = query_db("SELECT * FROM topics WHERE id = ?;", (topic_id,), one=True)
    if not topic:
        return jsonify({'error': 'Topic not found'}), 404

    exam = query_db("SELECT * FROM exams WHERE id = ?;", (topic['exam_id'],), one=True)
    calc = calculate_topic_risk(topic, exam['exam_date'] if exam else datetime.now().strftime("%Y-%m-%d"))

    return jsonify({
        'topic': dict(topic),
        'calc': calc
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
