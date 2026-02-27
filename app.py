#!/usr/bin/env python3
"""
IRA System Backend - Ultra Minimal Version
不需要任何复杂依赖，保证部署成功
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import uuid
import datetime
import random
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 数据库初始化
def init_db():
    conn = sqlite3.connect('ira_system.db')
    c = conn.cursor()

    # 候选人表
    c.execute('''CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        position TEXT,
        education TEXT,
        experience TEXT,
        status TEXT DEFAULT '待初筛',
        score INTEGER DEFAULT 0,
        match_skills TEXT,
        source TEXT,
        source_type TEXT DEFAULT 'manual',
        rpa_task_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # RPA任务表
    c.execute('''CREATE TABLE IF NOT EXISTS rpa_tasks (
        id TEXT PRIMARY KEY,
        status TEXT,
        config TEXT,
        candidates_found INTEGER DEFAULT 0,
        messages_sent INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        error TEXT
    )''')

    # 活动日志表
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        target TEXT,
        status TEXT DEFAULT 'completed',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 初始化数据
    c.execute('SELECT count(*) FROM candidates')
    if c.fetchone()[0] == 0:
        candidates = [
            ('王五', 'wangwu@email.com', '138****8888', '高级前端工程师', '硕士', '5年', 92, '待初试', 'React,TypeScript,Vue', 'BOSS直聘'),
            ('李明', 'liming@email.com', '139****9999', '全栈工程师', '本科', '4年', 88, '待沟通', 'Python,Django,React', '拉勾网'),
            ('张伟', 'zhangwei@email.com', '137****7777', 'Python开发工程师', '本科', '3年', 85, '已推荐', 'Python,FastAPI,MongoDB', '猎聘'),
            ('赵婷', 'zhaoting@email.com', '136****6666', '数据分析师', '硕士', '2年', 90, '待复试', 'Python,SQL,Tableau', '内推'),
            ('陈军', 'chenjun@email.com', '135****5555', 'DevOps工程师', '本科', '6年', 87, '待初筛', 'Kubernetes,Docker,Jenkins', 'BOSS直聘'),
            ('刘芳', 'liufang@email.com', '134****4444', '产品经理', '本科', '5年', 83, '待沟通', '产品设计,数据分析,Axure', '官网'),
        ]
        for cands in candidates:
            c.execute('''INSERT INTO candidates
                (name, email, phone, position, education, experience, score, status, match_skills, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', cands)

        # 初始活动日志
        logs = [
            ('筛选简历', '王五 - 高级前端工程师'),
            ('发送面试邀请', '李明 - 全栈工程师'),
            ('解答候选人问题', '张伟 - Python开发工程师'),
            ('生成JD优化建议', '后端工程师岗位'),
            ('安排面试时间', '赵婷 - 数据分析师'),
        ]
        for log in logs:
            c.execute('INSERT INTO activity_logs (action, target) VALUES (?, ?)', log)

    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# ========== API 端点 ==========

@app.route('/')
def index():
    return jsonify({'message': 'IRA System API Running', 'version': '2.0'})

@app.route('/dashboard/stats')
def get_stats():
    conn = sqlite3.connect('ira_system.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT count(*) FROM candidates WHERE status IN ('待初筛', '待沟通')")
    pending = c.fetchone()[0]

    c.execute("SELECT count(*) FROM candidates")
    total = c.fetchone()[0]

    c.execute("SELECT count(*) FROM candidates WHERE status IN ('待初试', '待复试', '已推荐')")
    converted = c.fetchone()[0]

    conversion_rate = round(converted / total * 100, 1) if total > 0 else 0
    ai_saved = total * 2 + 120

    conn.close()

    return jsonify({
        'pending_resumes': pending,
        'pending_interviews': 3,
        'today_interviews': 2,
        'ai_saved_hours': ai_saved,
        'week_growth': 12.5,
        'conversion_rate': conversion_rate
    })

@app.route('/dashboard/funnel')
def get_funnel():
    conn = sqlite3.connect('ira_system.db')
    c = conn.cursor()

    c.execute('SELECT count(*) FROM candidates')
    total = c.fetchone()[0] or 1

    c.execute("SELECT count(*) FROM candidates WHERE score >= 70")
    ai_screened = c.fetchone()[0]

    c.execute("SELECT count(*) FROM candidates WHERE status IN ('待初试', '待复试', '已推荐')")
    hr_screened = c.fetchone()[0]

    c.execute("SELECT count(*) FROM candidates WHERE status IN ('待初试', '待复试')")
    first_interview = c.fetchone()[0]

    c.execute("SELECT count(*) FROM candidates WHERE status = '待复试'")
    second_interview = c.fetchone()[0]

    c.execute("SELECT count(*) FROM candidates WHERE status = '已推荐'")
    offer = c.fetchone()[0]

    conn.close()

    return jsonify([
        {'stage': '简历投递', 'count': total, 'rate': 100},
        {'stage': 'AI初筛', 'count': ai_screened, 'rate': round(ai_screened/total*100, 1)},
        {'stage': 'HR筛选', 'count': hr_screened, 'rate': round(hr_screened/total*100, 1)},
        {'stage': '初试', 'count': first_interview, 'rate': round(first_interview/total*100, 1)},
        {'stage': '复试', 'count': second_interview, 'rate': round(second_interview/total*100, 1)},
        {'stage': 'Offer', 'count': offer, 'rate': round(offer/total*100, 1)}
    ])

@app.route('/dashboard/activity')
def get_activity():
    conn = sqlite3.connect('ira_system.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 10')
    logs = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(logs)

@app.route('/candidates')
def get_candidates():
    conn = sqlite3.connect('ira_system.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    status = request.args.get('status')
    search = request.args.get('search')

    query = 'SELECT * FROM candidates WHERE 1=1'
    params = []

    if status:
        query += ' AND status = ?'
        params.append(status)
    if search:
        query += ' AND (name LIKE ? OR position LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    query += ' ORDER BY created_at DESC LIMIT 50'

    c.execute(query, params)
    candidates = [dict(row) for row in c.fetchall()]

    # 转换 skills
    for c in candidates:
        if c.get('match_skills'):
            c['match_skills'] = c['match_skills'].split(',')
        else:
            c['match_skills'] = []

    conn.close()
    return jsonify(candidates)

@app.route('/candidates/<int:candidate_id>', methods=['PATCH'])
def update_candidate(candidate_id):
    data = request.json
    conn = sqlite3.connect('ira_system.db')
    c = conn.cursor()

    for key, value in data.items():
        if key == 'match_skills':
            value = ','.join(value) if isinstance(value, list) else value
        c.execute(f'UPDATE candidates SET {key} = ? WHERE id = ?', (value, candidate_id))

    conn.commit()
    conn.close()
    return jsonify({'message': 'updated'})

# 简历上传端点
@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 使用UUID重命名文件
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # 模拟AI解析简历并创建候选人
        # 实际项目中这里会使用PDF解析库提取简历信息
        names = ['候选人A', '候选人B', '候选人C', '候选人D', '候选人E']
        positions = ['前端工程师', '后端工程师', '全栈工程师', '产品经理', '数据分析师']

        conn = sqlite3.connect('ira_system.db')
        c = conn.cursor()

        # 随机生成候选人信息（模拟AI解析结果）
        name = random.choice(names)
        position = random.choice(positions)

        c.execute('''INSERT INTO candidates
            (name, email, phone, position, education, experience, score, status, match_skills, source, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name, f'{name.lower()}@email.com', f'138{random.randint(1000,9999)}****',
             position, random.choice(['本科', '硕士']), f'{random.randint(1,5)}年',
             random.randint(75, 95), '待初筛',
             'Python,JavaScript,React', '简历上传', 'upload'))

        candidate_id = c.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'message': '上传成功',
            'filename': unique_filename,
            'candidate_id': candidate_id,
            'parsed_data': {
                'name': name,
                'position': position,
                'score': random.randint(75, 95)
            }
        })

    return jsonify({'error': '不支持的文件类型'}), 400

# RPA 端点
rpa_tasks = {}

@app.route('/rpa/tasks', methods=['POST'])
def create_rpa_task():
    data = request.json
    task_id = str(uuid.uuid4())

    rpa_tasks[task_id] = {
        'id': task_id,
        'status': 'running',
        'config': data,
        'candidates_found': 0,
        'messages_sent': 0,
        'created_at': str(datetime.datetime.now()),
        'completed_at': None,
        'error': None
    }

    # 模拟任务（异步执行）
    import threading
    import time

    def run_task():
        import random
        time.sleep(2)

        # 模拟发现候选人
        names = ['张三', '李四', '王五', '赵六', '钱七']
        positions = ['Python工程师', '后端开发', '全栈工程师', 'Java开发', 'Go工程师']

        conn = sqlite3.connect('ira_system.db')
        c = conn.cursor()

        found = 0
        for i, (name, pos) in enumerate(zip(names, positions[:data.get('max_profiles', 5)])):
            c.execute('''INSERT INTO candidates
                (name, email, phone, position, education, experience, score, status, match_skills, source, source_type, rpa_task_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, f'{name.lower()}@email.com', f'138****{i:04d}', pos,
                 random.choice(['本科', '硕士']), random.choice(['2年', '3年', '4年']),
                 random.randint(80, 95), '待初筛', 'Python,Django,PostgreSQL',
                 data.get('platform', 'boss'), 'rpa', task_id))
            found += 1

            if data.get('auto_greeting'):
                rpa_tasks[task_id]['messages_sent'] += 1

        conn.commit()
        conn.close()

        rpa_tasks[task_id]['status'] = 'completed'
        rpa_tasks[task_id]['candidates_found'] = found
        rpa_tasks[task_id]['completed_at'] = str(datetime.datetime.now())

    thread = threading.Thread(target=run_task)
    thread.start()

    return jsonify(rpa_tasks[task_id])

@app.route('/rpa/tasks')
def get_rpa_tasks():
    return jsonify(list(rpa_tasks.values()))

@app.route('/rpa/tasks/<task_id>')
def get_rpa_task(task_id):
    task = rpa_tasks.get(task_id)
    if task:
        return jsonify(task)
    return jsonify({'error': 'not found'}), 404

@app.route('/rpa/tasks/<task_id>/logs')
def get_rpa_logs(task_id):
    task = rpa_tasks.get(task_id)
    if not task:
        return jsonify([])

    logs = []
    config = task.get('config', {})

    if task['status'] == 'running':
        logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': f'🚀 任务启动: {config.get("keywords")}'})
        logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': f'📋 平台: {config.get("platform")}'})
        logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': '🔐 正在登录招聘平台...'})
        logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': '✅ 登录成功'})
        logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': f'🔍 搜索关键词: {config.get("keywords")}'})
        logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': '📄 正在浏览候选人列表...'})

        for i in range(task['candidates_found']):
            logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': f'📋 发现候选人: 候选人{i+1}'})
            if config.get('auto_greeting'):
                logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': f'💬 发送打招呼消息'})
    elif task['status'] == 'completed':
        logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': f'✅ 任务完成! 共发现 {task["candidates_found"]} 位候选人'})
        logs.append({'timestamp': datetime.datetime.now().isoformat(), 'level': 'INFO', 'message': f'📊 已发送 {task["messages_sent"]} 条打招呼消息'})

    return jsonify(logs)

@app.route('/rpa/status')
def get_rpa_status():
    running = sum(1 for t in rpa_tasks.values() if t['status'] == 'running')
    return jsonify({'status': 'ready', 'running_tasks': running, 'total_tasks': len(rpa_tasks)})

@app.route('/jobs')
def get_jobs():
    return jsonify([
        {'id': 1, 'title': '高级前端工程师', 'department': '技术部', 'salary': '25K-40K', 'headcount': 2, 'status': '招聘中'},
        {'id': 2, 'title': '全栈工程师', 'department': '技术部', 'salary': '20K-35K', 'headcount': 3, 'status': '招聘中'},
        {'id': 3, 'title': 'Python开发工程师', 'department': '技术部', 'salary': '18K-30K', 'headcount': 2, 'status': '招聘中'},
    ])

@app.route('/interviews')
def get_interviews():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    return jsonify([
        {'id': 1, 'candidate_id': 1, 'candidate_name': '王五', 'position': '高级前端工程师',
         'interviewer': '张经理', 'interview_time': f'{today} 14:00', 'interview_type': '技术面试', 'status': '已确认', 'meeting_link': 'https://meet.example.com/abc123'},
        {'id': 2, 'candidate_id': 4, 'candidate_name': '赵婷', 'position': '数据分析师',
         'interviewer': '李总监', 'interview_time': f'{today} 10:00', 'interview_type': '综合面试', 'status': '已确认', 'meeting_link': 'https://meet.example.com/def456'},
    ])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
