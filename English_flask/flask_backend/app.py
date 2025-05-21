# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许跨域请求

# 数据库配置（根据实际修改）
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'charset': 'utf8mb4'
}


# 艾宾浩斯记忆曲线阶段配置（单位：分钟）
EBINHAUS_STAGES = [5, 30, 1440, 2880, 5760, 21600]  # 5分钟, 30分钟, 1天, 2天，4天，15天


def get_db_connection(db_name):
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        db=db_name,
        charset=DB_CONFIG['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )


# ------------------- 用户登录相关接口 -------------------
@app.route('/api/login', methods=['POST'])
def login():
    """微信登录/注册接口"""
    wechat_id = request.json.get('wechat_id')
    if not wechat_id:
        return jsonify({'code': 400, 'message': 'Missing wechat_id'})

    conn = get_db_connection('user_db')
    try:
        with conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT * FROM users WHERE wechat_id = %s", (wechat_id,))
            user = cursor.fetchone()

            if not user:  # 新用户注册
                cursor.execute("""
                    INSERT INTO users (wechat_id, daily_goal, selected_libraries)
                    VALUES (%s, 20, '四级英语词汇')
                """, (wechat_id,))
                conn.commit()

            # 获取完整用户数据
            cursor.execute("""
                SELECT wechat_id, daily_goal, selected_libraries,
                vocabulary_book, learning_stats 
                FROM users WHERE wechat_id = %s
            """, (wechat_id,))
            user = cursor.fetchone()

            # 处理JSON字段
            user['vocabulary_book'] = json.loads(user['vocabulary_book']) if user['vocabulary_book'] else {}
            user['learning_stats'] = json.loads(user['learning_stats'])

            return jsonify({'code': 200, 'data': user})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})
    finally:
        conn.close()




# ------------------- 用户数据相关接口 -------------------
#"""更新每日学习目标"""
@app.route('/api/user/goal', methods=['POST'])
def update_goal():
    wechat_id = request.json.get('wechat_id')
    new_goal = request.json.get('daily_goal')
    if not all([wechat_id, new_goal]):
        return jsonify({'code': 400, 'message': 'Invalid parameters'})
    conn = get_db_connection('user_db')
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET daily_goal = %s
                WHERE wechat_id = %s
            """, (new_goal, wechat_id))
            conn.commit()
            return jsonify({'code': 200, 'message': 'Goal updated'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})
    finally:
        conn.close()




# 词库相关接口 -------------------
# """获取所有可用词库"""
@app.route('/api/libraries', methods=['GET'])
def get_libraries():
    conn = get_db_connection('english')
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT book_id, book_name FROM book_library")
            libraries = cursor.fetchall()
            return jsonify({'code': 200, 'data': libraries})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})
    finally:
        conn.close()

#"""更新用户选择的词库"""
@app.route('/api/user/library', methods=['POST'])
def update_library():
    wechat_id = request.json.get('wechat_id')
    book_name = request.json.get('book_name')

    if not all([wechat_id, book_name]):
        return jsonify({'code': 400, 'message': 'Invalid parameters'})

    conn = get_db_connection('user_db')
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET selected_libraries = %s
                WHERE wechat_id = %s
            """, (book_name, wechat_id))
            conn.commit()
            return jsonify({'code': 200, 'message': 'Library updated'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})
    finally:
        conn.close()


#词库单词查看接口 -------------------
@app.route('/api/library/words', methods=['GET'])
def get_library_words():
    """获取指定词库全部单词"""
    book_id = request.args.get('book_id')
    if not book_id:
        return jsonify({'code': 400, 'message': '缺少词库ID'})

    conn = get_db_connection('english')
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT head_word 
                FROM combined_words 
                WHERE book_id = %s 
                ORDER BY word_rank
            """, (book_id,))
            words = [{'word': row['head_word']} for row in cursor.fetchall()]

            return jsonify({'code': 200, 'data': words})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})
    finally:
        conn.close()




# ------------------- 学习相关接口 -------------------
'''def get_review_words(vocab_book):
    """根据艾宾浩斯曲线获取需要复习的单词"""
    now = datetime.now()
    return [
        word_id for word_id, details in vocab_book.items()
        if datetime.strptime(details['next_review'], '%Y-%m-%d %H:%M:%S') <= now
    ]
'''
#单词获取接口
@app.route('/api/learn/words', methods=['GET'])
def get_learning_words():
    wechat_id = request.args.get('wechat_id')
    if not wechat_id:
        return jsonify({'code': 400, 'message': 'Missing wechat_id'})

    user_conn = get_db_connection('user_db')
    try:
        with user_conn.cursor() as cursor:
            # 获取用户数据
            cursor.execute("""
                SELECT daily_goal, selected_libraries, vocabulary_book, learning_stats 
                FROM users WHERE wechat_id = %s
            """, (wechat_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'code': 404, 'message': '用户不存在'})
            # 反序列化 JSON 字段（添加异常处理）
            try:
                vocab_book = json.loads(user['vocabulary_book']) if user['vocabulary_book'] else {}
                learning_stats = json.loads(user['learning_stats']) if user['learning_stats'] else {}
            except json.JSONDecodeError as e:
                return jsonify({'code': 500, 'message': f'JSON解析失败: {str(e)}'})
            # 合并复习词
            def get_review_items(data_dict):
                now = datetime.now()
                return [
                    word_id for word_id, details in data_dict.items()
                    if datetime.strptime(details['next_review'], '%Y-%m-%d %H:%M:%S') <= now
                ]
            review_words = list(set(
                get_review_items(vocab_book) +
                get_review_items(learning_stats)
            ))
            # 获取词库ID
            english_conn = get_db_connection('english')
            try:
                with english_conn.cursor() as cursor:
                    cursor.execute("SELECT book_id FROM book_library WHERE book_name = %s", (user['selected_libraries'],))
                    book_data = cursor.fetchone()
                    if not book_data:
                        return jsonify({'code': 404, 'message': '词库不存在'})
                    book_id = book_data['book_id']
                    # 获取新单词
                    limit = max(0, user.get('daily_goal', 50) - len(review_words))
                    cursor.execute("""
                        SELECT * FROM combined_words 
                        WHERE book_id = %s 
                        ORDER BY word_rank 
                        LIMIT %s
                    """, (book_id, limit))
                    new_words = cursor.fetchall()
                    # 获取复习单词
                    review_data = []
                    if review_words:
                        cursor.execute("SELECT * FROM combined_words WHERE word_id IN %s", (review_words,))
                        review_data = cursor.fetchall()
                    # 合并数据
                    combined = review_data + new_words
                    for word in combined:
                        word['is_starred'] = word['word_id'] in vocab_book
                        # 处理翻译数据
                        word['translations'] = [{
                            'pos': t.get('pos'),
                            'chinese': t.get('chinese'),
                            'english': t.get('english')
                        } for t in json.loads(word.get('translations') or '[]')]
                        # 处理例句数据
                        word['sentences'] = [{
                            'en': s.get('en'),
                            'cn': s.get('cn')
                        } for s in json.loads(word.get('sentences') or '[]')]
                        # 处理短语数据
                        word['phrases'] = [{
                            'phrase': p.get('phrase'),
                            'trans': p.get('trans')
                        } for p in json.loads(word.get('phrases') or '[]')]
                        # 处理同根词数据
                        word['related_words'] = [{
                            'word': r.get('word'),
                            'pos': r.get('pos'),
                            'trans': r.get('trans')
                        } for r in json.loads(word.get('related_words') or '[]')]
                    return jsonify({'code': 200, 'data': combined})
            finally:
                english_conn.close()
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})
    finally:
        user_conn.close()


#修改学习数据接口-------------------
@app.route('/api/learning/stats', methods=['POST', 'DELETE'])
def handle_learning_stats():
    if request.method == 'POST':
        # 更新逻辑
        return update_learning_stats()
    elif request.method == 'DELETE':
        # 删除逻辑
        return remove_from_stats()
def update_learning_stats():
    """更新学习统计，阶段自动递增"""
    data = request.json
    wechat_id = data.get('wechat_id')
    word_id = data.get('word_id')
    conn = get_db_connection('user_db')
    try:
        with conn.cursor() as cursor:
            # 获取当前学习数据
            cursor.execute("SELECT learning_stats FROM users WHERE wechat_id = %s FOR UPDATE", (wechat_id,))
            result = cursor.fetchone()
            stats = json.loads(result['learning_stats']) if result['learning_stats'] else {}
            # 自动递增阶段
            current_stage = stats.get(word_id, {}).get('stage', -1) + 1  # 新单词从0开始
            # 防止阶段溢出
            current_stage = min(current_stage, len(EBINHAUS_STAGES) - 1)
            # 计算下次复习时间
            next_review = datetime.now() + timedelta(minutes=EBINHAUS_STAGES[current_stage])
            # 更新数据
            stats[word_id] = {
                'stage': current_stage,
                'next_review': next_review.strftime('%Y-%m-%d %H:%M:%S')
            }
            # 保存到数据库
            cursor.execute("UPDATE users SET learning_stats = %s WHERE wechat_id = %s",
                           (json.dumps(stats), wechat_id))
            conn.commit()
            return jsonify({'code': 200, 'message': 'Stats updated'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})
    finally:
        conn.close()

def remove_from_stats():
    data = request.json
    wechat_id = data.get('wechat_id')
    word_id = data.get('word_id')
    conn = get_db_connection('user_db')
    try:
        with conn.cursor() as cursor:
            # 获取当前统计
            cursor.execute("SELECT learning_stats FROM users WHERE wechat_id = %s", (wechat_id,))
            result = cursor.fetchone()
            stats = json.loads(result['learning_stats']) if result['learning_stats'] else {}
            # 允许静默删除（无论是否存在都返回成功）
            if word_id in stats:
                del stats[word_id]
                cursor.execute("UPDATE users SET learning_stats = %s WHERE wechat_id = %s",
                               (json.dumps(stats), wechat_id))
                conn.commit()
            return jsonify({'code': 200, 'message': '操作成功'})  # 统一返回200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})
    finally:
        conn.close()





# ------------------- 生词本相关接口 -------------------
"""
    统一生词本操作接口
    POST请求格式：
    {
        "wechat_id": "用户微信ID",
        "word_id": "可选，操作单词ID",
        "action": "可选，操作类型（add/remove）"
    }
    """
@app.route('/api/vocabulary', methods=['POST'])
def handle_vocabulary():
    data = request.json
    wechat_id = data.get('wechat_id')
    # 参数验证
    if not wechat_id:
        return jsonify({'code': 400, 'message': 'Missing wechat_id'})
    # 操作路由
    if 'action' in data:
        return update_vocabulary(data)
    else:
        return get_vocabulary(data)

def get_vocabulary(data):
    """获取生词本"""
    wechat_id = data['wechat_id']

    try:
        # 连接用户数据库
        user_conn = get_db_connection('user_db')
        with user_conn.cursor() as user_cursor:
            # 1. 获取原始生词本数据
            user_cursor.execute(
                "SELECT vocabulary_book FROM users WHERE wechat_id = %s",
                (wechat_id,)
            )
            result = user_cursor.fetchone()
            if not result:
                return jsonify({'code': 404, 'message': '用户不存在'})
            raw_book = json.loads(result['vocabulary_book']) if result['vocabulary_book'] else {}
            # 2. 无生词快速返回
            if not raw_book:
                return jsonify({'code': 200, 'data': {}})
            # 3. 获取head_word映射
            english_conn = get_db_connection('english')
            try:
                with english_conn.cursor() as english_cursor:
                    # 构建批量查询
                    word_ids = list(raw_book.keys())
                    placeholders = ','.join(['%s'] * len(word_ids))
                    # 执行查询（使用索引优化）
                    english_cursor.execute(
                        f"""SELECT word_id, head_word 
                            FROM combined_words 
                            WHERE word_id IN ({placeholders})""",
                        tuple(word_ids)
                    )
                    # 构建映射字典
                    word_mapping = {row['word_id']: row['head_word'] for row in english_cursor.fetchall()}
                    # 4. 处理数据转换
                    processed_book = {}
                    for word_id, details in raw_book.items():
                        if word_id not in word_mapping:
                            continue  # 忽略无效单词
                        head_word = word_mapping[word_id]
                        # 处理重复head_word（添加word_id后缀）
                        if head_word in processed_book:
                            head_word = f"{head_word}（{word_id}）"
                        # 保留原始word_id用于操作
                        details['word_id'] = word_id
                        processed_book[head_word] = details
                    return jsonify({'code': 200, 'data': processed_book})
            finally:
                english_conn.close()
    except Exception as e:
        app.logger.error(f"获取生词本失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'})
    finally:
        if 'user_conn' in locals():
            user_conn.close()


def update_vocabulary(data):
    """更新生词本（添加/删除）"""
    required_fields = ['wechat_id', 'word_id', 'action']
    if not all(field in data for field in required_fields):
        return jsonify({'code': 400, 'message': '缺少必要参数'})

    action = data['action']
    if action not in ['add', 'remove']:
        return jsonify({'code': 400, 'message': '无效操作类型'})

    try:
        conn = get_db_connection('user_db')
        with conn.cursor() as cursor:
            # 1. 获取当前生词本
            cursor.execute(
                "SELECT vocabulary_book FROM users WHERE wechat_id = %s FOR UPDATE",
                (data['wechat_id'],)
            )
            result = cursor.fetchone()
            if not result:
                return jsonify({'code': 404, 'message': '用户不存在'})
            vocab_book = json.loads(result['vocabulary_book']) if result['vocabulary_book'] else {}
            # 2. 执行操作
            word_id = data['word_id']
            if action == 'add':
                # 添加生词逻辑
                if word_id in vocab_book:
                    return jsonify({'code': 200, 'message': '单词已在生词本中'})
                # 设置艾宾浩斯初始阶段
                next_review = datetime.now() + timedelta(minutes=5)
                vocab_book[word_id] = {
                    'added_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'stage': 0,
                    'next_review': next_review.strftime('%Y-%m-%d %H:%M:%S')
                }
            else:  # remove
                if word_id not in vocab_book:
                    return jsonify({'code': 404, 'message': '单词不在生词本中'})
                del vocab_book[word_id]
            # 3. 更新数据库
            cursor.execute(
                "UPDATE users SET vocabulary_book = %s WHERE wechat_id = %s",
                (json.dumps(vocab_book), data['wechat_id'])
            )
            conn.commit()

            return jsonify({'code': 200, 'message': '操作成功'})
    except pymysql.err.IntegrityError:
        return jsonify({'code': 404, 'message': '单词不存在'})
    except Exception as e:
        conn.rollback()
        app.logger.error(f"更新生词本失败: {str(e)}")
        return jsonify({'code': 500, 'message': '服务器内部错误'})
    finally:
        if 'conn' in locals():
            conn.close()














if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)