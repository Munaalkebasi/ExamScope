import unittest
import json
import os
import sys
import io
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from utils.db import init_db, query_db, execute_db
from utils.risk_calculator import calculate_topic_risk, calculate_readiness_overview, get_days_until_exam
from utils.demo_data import load_demo_data

class ExamScopeTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        init_db()
        load_demo_data(force=True)

    def test_01_pages_render(self):
        """Test all 4 main pages render with 200 OK status."""
        for path in ['/', '/topics', '/progress', '/settings']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, f"Page {path} failed to render.")

    def test_02_risk_calculator_logic(self):
        """Test risk score calculation formula and classification."""
        topic = {
            'id': 'test-topic-1',
            'name': 'Test Eigenvalues',
            'confidence': 30,
            'practice_score': 40,
            'last_reviewed': (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        }
        exam_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        calc = calculate_topic_risk(topic, exam_date)

        self.assertIn(calc['risk_level'], ['Critical', 'High', 'Moderate', 'Safe'])
        self.assertGreaterEqual(calc['risk_score'], 0)
        self.assertLessEqual(calc['risk_score'], 100)
        self.assertIn('x', calc)
        self.assertIn('y', calc)

    def test_03_readiness_overview(self):
        """Test aggregate readiness overview calculation."""
        topics = query_db("SELECT * FROM topics WHERE exam_id = 'exam-math232-m1';")
        exam_date = (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d")
        overview = calculate_readiness_overview(topics, exam_date)

        self.assertIn('readiness_score', overview)
        self.assertIn('top_risk_topic', overview)
        self.assertIn('study_next_recommendation', overview)
        self.assertGreater(len(overview['topic_calculations']), 0)

    def test_04_exam_crud(self):
        """Test create, edit, select, and delete exam operations."""
        # Create exam
        create_res = self.client.post('/exams/create', data={
            'course_code': 'CHEM 101',
            'exam_name': 'Midterm Exam',
            'exam_date': '2026-11-15'
        }, follow_redirects=True)
        self.assertEqual(create_res.status_code, 200)

        created_exam = query_db("SELECT * FROM exams WHERE course_code = 'CHEM 101';", one=True)
        self.assertIsNotNone(created_exam)

        # Edit exam
        edit_res = self.client.post(f'/exams/edit/{created_exam["id"]}', data={
            'course_code': 'CHEM 101',
            'exam_name': 'Updated Midterm Exam',
            'exam_date': '2026-11-20'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)

        updated_exam = query_db("SELECT * FROM exams WHERE id = ?;", (created_exam['id'],), one=True)
        self.assertEqual(updated_exam['exam_name'], 'Updated Midterm Exam')

        # Delete exam
        delete_res = self.client.post(f'/exams/delete/{created_exam["id"]}', follow_redirects=True)
        self.assertEqual(delete_res.status_code, 200)
        self.assertIsNone(query_db("SELECT * FROM exams WHERE id = ?;", (created_exam['id'],), one=True))

    def test_05_topic_crud(self):
        """Test topic creation, edit, mark reviewed, and deletion."""
        active_exam = query_db("SELECT * FROM exams LIMIT 1;", one=True)
        
        # Create topic
        create_res = self.client.post('/topics/create', data={
            'name': 'Fourier Series',
            'confidence': '40',
            'practice_score': '55',
            'last_reviewed': (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            'notes': 'Practice odd/even functions.'
        }, follow_redirects=True)
        self.assertEqual(create_res.status_code, 200)

        new_topic = query_db("SELECT * FROM topics WHERE name = 'Fourier Series';", one=True)
        self.assertIsNotNone(new_topic)

        # Edit topic
        edit_res = self.client.post(f'/topics/edit/{new_topic["id"]}', data={
            'name': 'Fourier Series & Transforms',
            'confidence': '70',
            'practice_score': '80',
            'last_reviewed': datetime.now().strftime("%Y-%m-%d"),
            'notes': 'Mastered basics.'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)

        updated_topic = query_db("SELECT * FROM topics WHERE id = ?;", (new_topic['id'],), one=True)
        self.assertEqual(updated_topic['confidence'], 70)

        # Review topic
        review_res = self.client.post(f'/topics/review/{new_topic["id"]}', follow_redirects=True)
        self.assertEqual(review_res.status_code, 200)

        # Delete topic
        delete_res = self.client.post(f'/topics/delete/{new_topic["id"]}', follow_redirects=True)
        self.assertEqual(delete_res.status_code, 200)
        self.assertIsNone(query_db("SELECT * FROM topics WHERE id = ?;", (new_topic['id'],), one=True))

    def test_06_topics_sorting_and_filtering(self):
        """Test sorting and filtering parameters on topics page."""
        for sort_param in ['highest_risk', 'lowest_risk', 'lowest_confidence', 'lowest_practice', 'least_reviewed', 'name']:
            res = self.client.get(f'/topics?sort={sort_param}')
            self.assertEqual(res.status_code, 200)

        for filter_param in ['all', 'critical', 'high', 'moderate', 'safe']:
            res = self.client.get(f'/topics?filter={filter_param}')
            self.assertEqual(res.status_code, 200)

    def test_07_api_topic_detail(self):
        """Test JSON API for topic drawer details."""
        topic = query_db("SELECT * FROM topics LIMIT 1;", one=True)
        res = self.client.get(f'/api/topic/{topic["id"]}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('topic', data)
        self.assertIn('calc', data)
        self.assertIn('risk_level', data['calc'])

    def test_08_import_export_validation(self):
        """Test export download and import validation safety."""
        # Export
        export_res = self.client.get('/data/export')
        self.assertEqual(export_res.status_code, 200)
        self.assertEqual(export_res.mimetype, 'application/json')
        export_bytes = export_res.data
        export_data = json.loads(export_bytes)
        self.assertIn('exams', export_data)
        self.assertIn('topics', export_data)

        # Invalid Import Rejection (Malformed JSON without required keys)
        invalid_json_stream = (io.BytesIO(b'{"invalid": "structure"}'), 'invalid.json')
        import_bad_res = self.client.post('/data/import', data={'file': invalid_json_stream}, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(import_bad_res.status_code, 200)

        # Ensure existing exams were NOT wiped by bad import
        exams = query_db("SELECT * FROM exams;")
        self.assertGreater(len(exams), 0)

        # Valid Import (Roundtrip)
        valid_json_stream = (io.BytesIO(export_bytes), 'backup.json')
        import_valid_res = self.client.post('/data/import', data={'file': valid_json_stream}, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(import_valid_res.status_code, 200)
        restored_exams = query_db("SELECT * FROM exams;")
        self.assertEqual(len(restored_exams), len(export_data['exams']))

    def test_09_theme_toggle(self):
        """Test dark/light theme setting update."""
        res = self.client.post('/settings/theme', data={'theme': 'light'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        settings = query_db("SELECT * FROM settings WHERE id = 1;", one=True)
        self.assertEqual(settings['theme'], 'light')

if __name__ == '__main__':
    unittest.main()
