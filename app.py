#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧飲水系統 - Flask Web 應用
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import database as db

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# 確保上傳資料夾存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化資料庫
db.init_database()

# ========== 網頁路由 ==========

@app.route('/')
def index():
    """首頁 - 即時監控"""
    return render_template('index.html')

@app.route('/bottles')
def bottles():
    """水壺管理頁面"""
    return render_template('bottles.html')

@app.route('/history')
def history():
    """歷史記錄頁面"""
    return render_template('history.html')

@app.route('/settings')
def settings():
    """設定頁面"""
    return render_template('settings.html')

# ========== API 路由 ==========

# --- 即時狀態 ---

@app.route('/api/status')
def api_status():
    """取得即時狀態"""
    try:
        status = db.get_current_status()
        bottle = db.get_active_bottle()
        settings = db.get_all_settings()
        
        return jsonify({
            'success': True,
            'status': status,
            'bottle': bottle,
            'settings': settings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --- 水壺管理 ---

@app.route('/api/bottles', methods=['GET'])
def api_get_bottles():
    """取得所有水壺"""
    try:
        bottles = db.get_all_bottles()
        return jsonify({'success': True, 'bottles': bottles})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bottles', methods=['POST'])
def api_add_bottle():
    """新增水壺"""
    try:
        data = request.form
        name = data.get('name')
        empty_weight = float(data.get('empty_weight'))
        capacity = int(data.get('capacity'))
        
        # 處理照片上傳
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photo_path = f"uploads/{filename}"
        
        bottle_id = db.add_bottle(name, empty_weight, capacity, photo_path)
        
        return jsonify({'success': True, 'bottle_id': bottle_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bottles/<int:bottle_id>', methods=['PUT'])
def api_update_bottle(bottle_id):
    """更新水壺"""
    try:
        data = request.form
        name = data.get('name')
        empty_weight = float(data.get('empty_weight'))
        capacity = int(data.get('capacity'))
        
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photo_path = f"uploads/{filename}"
        
        db.update_bottle(bottle_id, name, empty_weight, capacity, photo_path)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bottles/<int:bottle_id>', methods=['DELETE'])
def api_delete_bottle(bottle_id):
    """刪除水壺"""
    try:
        db.delete_bottle(bottle_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bottles/<int:bottle_id>/activate', methods=['POST'])
def api_activate_bottle(bottle_id):
    """設定為當前使用的水壺"""
    try:
        db.set_active_bottle(bottle_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --- 飲水記錄 ---

@app.route('/api/drinks/today')
def api_today_drinks():
    """取得今日飲水記錄"""
    try:
        drinks = db.get_today_drinks()
        total = db.get_today_total()
        return jsonify({'success': True, 'drinks': drinks, 'total': total})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/drinks/date/<date>')
def api_drinks_by_date(date):
    """取得指定日期的飲水記錄"""
    try:
        drinks = db.get_drinks_by_date(date)
        return jsonify({'success': True, 'drinks': drinks})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/drinks/hourly')
def api_hourly_stats():
    """取得每小時統計"""
    try:
        date = request.args.get('date')
        stats = db.get_hourly_stats(date)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --- 設定 ---

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """取得所有設定"""
    try:
        settings = db.get_all_settings()
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """更新設定"""
    try:
        data = request.json
        for key, value in data.items():
            db.set_setting(key, str(value))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ========== 啟動 ==========

if __name__ == '__main__':
    print("="*60)
    print("智慧飲水系統 Web Dashboard")
    print("="*60)
    print("啟動中...")
    print("請開啟瀏覽器訪問: http://raspberrypi.local:5000")
    print("或: http://localhost:5000")
    print("按 Ctrl+C 停止")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)