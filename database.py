#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧飲水系統 - 資料庫模組
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'hydration.db')

def init_database():
    """初始化資料庫"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 水壺資料表
    c.execute('''
        CREATE TABLE IF NOT EXISTS bottles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            empty_weight REAL NOT NULL,
            capacity INTEGER NOT NULL,
            photo_path TEXT,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    # 飲水記錄表
    c.execute('''
        CREATE TABLE IF NOT EXISTS drink_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bottle_id INTEGER,
            amount_ml INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (bottle_id) REFERENCES bottles (id)
        )
    ''')
    
    # 系統設定表
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    # 即時狀態表（單行）
    c.execute('''
        CREATE TABLE IF NOT EXISTS current_status (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            water_ml INTEGER DEFAULT 0,
            status TEXT DEFAULT 'OK',
            last_drink_minutes INTEGER DEFAULT 0,
            today_total_ml INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    # 初始化預設設定
    c.execute('''
        INSERT OR IGNORE INTO settings (key, value) VALUES 
        ('daily_goal_ml', '2000'),
        ('remind_interval_min', '60')
    ''')
    
    # 初始化狀態
    c.execute('INSERT OR IGNORE INTO current_status (id) VALUES (1)')
    
    conn.commit()
    conn.close()
    print(f"✓ 資料庫初始化完成: {DB_PATH}")

# ========== 水壺管理 ==========

def add_bottle(name: str, empty_weight: float, capacity: int, photo_path: str = None) -> int:
    """新增水壺"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO bottles (name, empty_weight, capacity, photo_path)
        VALUES (?, ?, ?, ?)
    ''', (name, empty_weight, capacity, photo_path))
    bottle_id = c.lastrowid
    conn.commit()
    conn.close()
    return bottle_id

def get_all_bottles() -> List[Dict]:
    """取得所有水壺"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM bottles ORDER BY created_at DESC')
    bottles = [dict(row) for row in c.fetchall()]
    conn.close()
    return bottles

def get_active_bottle() -> Optional[Dict]:
    """取得當前使用的水壺"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM bottles WHERE is_active = 1 LIMIT 1')
    bottle = c.fetchone()
    conn.close()
    return dict(bottle) if bottle else None

def set_active_bottle(bottle_id: int):
    """設定當前使用的水壺"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 先取消所有啟用
    c.execute('UPDATE bottles SET is_active = 0')
    # 啟用指定水壺
    c.execute('UPDATE bottles SET is_active = 1 WHERE id = ?', (bottle_id,))
    conn.commit()
    conn.close()

def update_bottle(bottle_id: int, name: str, empty_weight: float, capacity: int, photo_path: str = None):
    """更新水壺資訊"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if photo_path:
        c.execute('''
            UPDATE bottles 
            SET name = ?, empty_weight = ?, capacity = ?, photo_path = ?
            WHERE id = ?
        ''', (name, empty_weight, capacity, photo_path, bottle_id))
    else:
        c.execute('''
            UPDATE bottles 
            SET name = ?, empty_weight = ?, capacity = ?
            WHERE id = ?
        ''', (name, empty_weight, capacity, bottle_id))
    conn.commit()
    conn.close()

def delete_bottle(bottle_id: int):
    """刪除水壺"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM bottles WHERE id = ?', (bottle_id,))
    conn.commit()
    conn.close()

# ========== 飲水記錄 ==========

def add_drink_event(amount_ml: int, bottle_id: int = None):
    """記錄飲水事件"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO drink_events (bottle_id, amount_ml)
        VALUES (?, ?)
    ''', (bottle_id, amount_ml))
    conn.commit()
    conn.close()

def get_today_drinks() -> List[Dict]:
    """取得今日飲水記錄"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT * FROM drink_events 
        WHERE DATE(timestamp) = DATE('now', 'localtime')
        ORDER BY timestamp DESC
    ''')
    drinks = [dict(row) for row in c.fetchall()]
    conn.close()
    return drinks

def get_today_total() -> int:
    """取得今日總飲水量"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT COALESCE(SUM(amount_ml), 0) 
        FROM drink_events 
        WHERE DATE(timestamp) = DATE('now', 'localtime')
    ''')
    total = c.fetchone()[0]
    conn.close()
    return total

def get_drinks_by_date(date: str) -> List[Dict]:
    """取得指定日期的飲水記錄"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT * FROM drink_events 
        WHERE DATE(timestamp) = ?
        ORDER BY timestamp DESC
    ''', (date,))
    drinks = [dict(row) for row in c.fetchall()]
    conn.close()
    return drinks

def get_hourly_stats(date: str = None) -> List[Dict]:
    """取得每小時飲水統計"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT 
            strftime('%H', timestamp) as hour,
            SUM(amount_ml) as total_ml,
            COUNT(*) as count
        FROM drink_events 
        WHERE DATE(timestamp) = ?
        GROUP BY hour
        ORDER BY hour
    ''', (date,))
    stats = [dict(row) for row in c.fetchall()]
    conn.close()
    return stats

# ========== 系統設定 ==========

def get_setting(key: str) -> str:
    """取得設定值"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_setting(key: str, value: str):
    """設定值"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, datetime('now', 'localtime'))
    ''', (key, value))
    conn.commit()
    conn.close()

def get_all_settings() -> Dict:
    """取得所有設定"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT key, value FROM settings')
    settings = {row['key']: row['value'] for row in c.fetchall()}
    conn.close()
    return settings

# ========== 即時狀態 ==========

def update_status(water_ml: int, status: str, last_drink_minutes: int, today_total_ml: int):
    """更新即時狀態"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE current_status 
        SET water_ml = ?, status = ?, last_drink_minutes = ?, 
            today_total_ml = ?, timestamp = datetime('now', 'localtime')
        WHERE id = 1
    ''', (water_ml, status, last_drink_minutes, today_total_ml))
    conn.commit()
    conn.close()

def get_current_status() -> Dict:
    """取得即時狀態"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM current_status WHERE id = 1')
    status = dict(c.fetchone())
    conn.close()
    return status

# ========== 初始化 ==========

if __name__ == "__main__":
    init_database()
    print("資料庫測試：")
    
    # 測試新增水壺
    bottle_id = add_bottle("測試水壺", 150.0, 500)
    print(f"新增水壺 ID: {bottle_id}")
    
    # 測試取得水壺
    bottles = get_all_bottles()
    print(f"所有水壺: {bottles}")
    
    # 測試記錄飲水
    add_drink_event(200, bottle_id)
    print(f"今日總量: {get_today_total()} ml")