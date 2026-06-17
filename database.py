"""
Database Manager

Manages SQLite database operations for history, statistics, and templates.

Database Tables:
    - conversion_history: Logs every conversion operation with metadata.
    - daily_stats: Aggregated daily statistics for dashboard charts.
    - templates: Stores user-defined conversion presets.

Classes:
    DatabaseManager: Handles CRUD operations, statistics queries, and data export.

Features:
    - Automatic daily stats aggregation
    - History filtering (date, search query, limit)
    - Export functionality (CSV, JSON)
    - Template storage and retrieval

"""

import sqlite3, csv, json
from datetime import datetime, timedelta

class DatabaseManager:
    """Database manager for history and statistics"""

    def __init__(self):
        self.db_path = "file_converter_stats.db"
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self.init_database()

    def close(self):
        """Call this when the application exits to flush and close the DB."""
        try:
            self._conn.close()
        except Exception:
            pass

    def init_database(self):
        conn = self._conn
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_file TEXT,
            source_format TEXT,
            target_file TEXT,
            target_format TEXT,
            operation_type TEXT,
            file_size INTEGER,
            conversion_time REAL,
            success BOOLEAN,
            notes TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            template_type TEXT,
            config_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date DATE PRIMARY KEY,
            total_conversions INTEGER DEFAULT 0,
            total_size INTEGER DEFAULT 0,
            total_time_saved INTEGER DEFAULT 0,
            pdf_to_word INTEGER DEFAULT 0,
            word_to_pdf INTEGER DEFAULT 0,
            image_to_pdf INTEGER DEFAULT 0,
            merge_operations INTEGER DEFAULT 0,
            split_operations INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()

    def add_conversion_record(self, source_file, source_format, target_file, target_format, 
                            operation_type, file_size, conversion_time, success=True, notes=""):
        conn = self._conn
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO conversion_history 
        (source_file, source_format, target_file, target_format, operation_type, 
         file_size, conversion_time, success, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (source_file, source_format, target_file, target_format, operation_type,
              file_size, conversion_time, success, notes))
        
        today = datetime.now().date().isoformat()
        cursor.execute('''
        INSERT OR IGNORE INTO daily_stats (date) VALUES (?)
        ''', (today,))
        
        cursor.execute('''
        UPDATE daily_stats 
        SET total_conversions = total_conversions + 1,
            total_size = total_size + ?,
            total_time_saved = total_time_saved + ?
        WHERE date = ?
        ''', (file_size, int(conversion_time * 60), today))
        
        if operation_type == "PDF vers Word":
            cursor.execute('UPDATE daily_stats SET pdf_to_word = pdf_to_word + 1 WHERE date = ?', (today,))
        elif operation_type == "Word vers PDF":
            cursor.execute('UPDATE daily_stats SET word_to_pdf = word_to_pdf + 1 WHERE date = ?', (today,))
        elif operation_type == "Images vers PDF":
            cursor.execute('UPDATE daily_stats SET image_to_pdf = image_to_pdf + 1 WHERE date = ?', (today,))
        elif "fusion" in operation_type.lower():
            cursor.execute('UPDATE daily_stats SET merge_operations = merge_operations + 1 WHERE date = ?', (today,))
        elif "diviser" in operation_type.lower():
            cursor.execute('UPDATE daily_stats SET split_operations = split_operations + 1 WHERE date = ?', (today,))
        
        conn.commit()

    def get_conversion_history(self, limit=100, search_query=None, start_date=None, end_date=None):
        conn = self._conn
        cursor = conn.cursor()
        
        query = '''
        SELECT id, timestamp, source_file, source_format, target_file, target_format, 
               operation_type, file_size, conversion_time, success, notes
        FROM conversion_history
        WHERE 1=1
        '''
        params = []
        
        if search_query:
            query += " AND (source_file LIKE ? OR target_file LIKE ? OR operation_type LIKE ?)"
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param, search_param])
        
        if start_date:
            query += " AND DATE(timestamp) >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND DATE(timestamp) <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_first_conversion_date(self):
        """Return the date of the first conversion, or None if no records exist."""
        conn = self._conn
        cursor = conn.cursor()
        cursor.execute('SELECT MIN(DATE(timestamp)) FROM conversion_history')
        result = cursor.fetchone()
        return result[0] if result and result[0] else None

    def get_statistics(self, days=30):
        conn = self._conn
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            COUNT(*) as total_conversions,
            SUM(file_size) as total_size,
            SUM(conversion_time) as total_time,
            AVG(conversion_time) as avg_time
        FROM conversion_history
        WHERE success = 1
        ''')
        general_stats = cursor.fetchone()
        
        cursor.execute('''
        SELECT target_format, COUNT(*) as count
        FROM conversion_history
        WHERE success = 1
        GROUP BY target_format
        ORDER BY count DESC
        LIMIT 10
        ''')
        top_formats = cursor.fetchall()
        
        cursor.execute('''
        SELECT operation_type, COUNT(*) as count
        FROM conversion_history
        WHERE success = 1
        GROUP BY operation_type
        ORDER BY count DESC
        LIMIT 10
        ''')
        top_operations = cursor.fetchall()
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        cursor.execute('''
        SELECT date, total_conversions, total_size, total_time_saved
        FROM daily_stats
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        ''', (start_date.isoformat(), end_date.isoformat()))
        daily_stats = cursor.fetchall()
        
        return {
            'general': general_stats,
            'top_formats': top_formats,
            'top_operations': top_operations,
            'daily_stats': daily_stats
        }

    def export_history(self, filepath, format='csv'):
        history = self.get_conversion_history(limit=10000)
        
        if format == 'csv':
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Date/Time', 'Source File', 'Source Format',
                               'Target File', 'Target Format', 'Operation Type',
                               'Size (bytes)', 'Time (s)', 'Success', 'Notes'])
                for row in history:
                    writer.writerow(row)
        elif format == 'json':
            data = []
            for row in history:
                data.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'source_file': row[2],
                    'source_format': row[3],
                    'target_file': row[4],
                    'target_format': row[5],
                    'operation_type': row[6],
                    'file_size': row[7],
                    'conversion_time': row[8],
                    'success': bool(row[9]),
                    'notes': row[10]
                })
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def save_template(self, name, template_type, config_data):
        conn = self._conn
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO templates (name, template_type, config_data)
        VALUES (?, ?, ?)
        ''', (name, template_type, json.dumps(config_data)))
        
        conn.commit()

    def get_templates(self, template_type=None):
        conn = self._conn
        cursor = conn.cursor()
        
        if template_type:
            cursor.execute('SELECT id, name, template_type, config_data, created_at, last_used FROM templates WHERE template_type = ? ORDER BY last_used DESC, created_at DESC', (template_type,))
        else:
            cursor.execute('SELECT id, name, template_type, config_data, created_at, last_used FROM templates ORDER BY last_used DESC, created_at DESC')
        
        return cursor.fetchall()

    def update_template_usage(self, template_id):
        conn = self._conn
        cursor = conn.cursor()
        cursor.execute('UPDATE templates SET last_used = CURRENT_TIMESTAMP WHERE id = ?', (template_id,))
        conn.commit()

    def update_template_config(self, template_id, config_data_json):
        """Update the config_data of an existing template (JSON string)."""
        conn = self._conn
        cursor = conn.cursor()
        cursor.execute('UPDATE templates SET config_data = ? WHERE id = ?',
                       (config_data_json, template_id))
        conn.commit()

    def delete_template(self, template_id):
        conn = self._conn
        cursor = conn.cursor()
        cursor.execute('DELETE FROM templates WHERE id = ?', (template_id,))
        conn.commit()
