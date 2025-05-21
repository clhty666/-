
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import sys,pymysql,json



class Config:
    SECRET_KEY = '123'     # 随机生成一个密钥
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'    # MySQL 用户名
    MYSQL_PASSWORD = ''    #MySQL 密码
    MYSQL_DB = 'user_db'
    MYSQL_CURSORCLASS = 'DictCursor'    # 返回字典格式数据

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许所有域的API请求
app.config.from_object(Config)
mysql = MySQL(app)





# 管理员登录路由
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (username, password))
        admin = cur.fetchone()
        cur.close()

        if admin:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')


# 界面路由
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    active_tab = request.args.get('active_tab', 'library')

    try:
        cur = mysql.connection.cursor()

        # 获取词库数据
        cur.execute("""
            SELECT 
                b.book_id,
                b.book_name,
                COUNT(cw.word_id) AS word_count
            FROM english.book_library AS b
            LEFT JOIN english.combined_words AS cw ON b.book_id = cw.book_id
            GROUP BY b.book_id
        """)
        libraries = cur.fetchall()

        # 获取用户数据
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        cur.execute("""
            SELECT 
                wechat_id,
                created_at,
                updated_at
            FROM user_db.users
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        users = cur.fetchall()

        # 检查是否有下一页
        cur.execute("SELECT COUNT(*) FROM user_db.users")
        total = cur.fetchone()['COUNT(*)']
        has_next = page * per_page < total

        cur.close()

        return render_template('admin.html',
                               username=session['username'],
                               libraries=libraries,
                               users=users,
                               page=page,
                               has_next=has_next,
                               active_tab = active_tab)  # 新增参数

    except Exception as e:
        print(f"数据库错误: {str(e)}")
        return "服务器内部错误", 500


# 删除词库
@app.route('/delete/library/<string:book_id>')
def delete_library(book_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    active_tab = request.args.get('active_tab', 'library')

    try:

        cur = mysql.connection.cursor()
        # 先删除关联单词
        cur.execute("DELETE FROM english.combined_words WHERE book_id = %s", (book_id,))
        # 再删除词库
        cur.execute("DELETE FROM english.book_library WHERE book_id = %s", (book_id,))
        mysql.connection.commit()
        return redirect(url_for('admin_dashboard', active_tab=active_tab))
    except Exception as e:
        mysql.connection.rollback()
        print(f"删除失败: {str(e)}")
        return "删除操作失败", 501

#添加词库
@app.route('/add/library', methods=['POST'])
def add_library():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    try:
        # 获取表单数据
        book_name = request.form.get('book_name')
        json_file = request.files.get('json_file')

        # 校验输入
        if not book_name or not json_file or not json_file.filename.endswith('.json'):
            return "请提供有效的词库名称和JSON文件", 502

        # 创建数据库游标
        cur = mysql.connection.cursor()

        # 读取并处理JSON文件内容
        def process_upload():
            # 读取第一行获取book_id
            first_line = json_file.stream.readline().decode('utf-8').strip()
            first_data = json.loads(first_line)
            book_id = first_data["bookId"]

            # 检查词库是否已存在
            cur.execute("SELECT book_id FROM english.book_library WHERE book_id = %s", (book_id,))
            if cur.fetchone():
                return {"status": "error", "message": "词库ID已存在"}, None

            # 插入新词库
            cur.execute(
                "INSERT INTO english.book_library (book_id, book_name) VALUES (%s, %s)",
                (book_id, book_name)
            )

            # 处理所有数据行
            json_file.stream.seek(0)  # 重置文件指针
            for line in json_file.stream:
                line = line.decode('utf-8').strip()
                if not line:
                    continue

                word_data = json.loads(line.strip())
                content = word_data["content"]["word"]["content"]

                sentences = [{"en": s["sContent"], "cn": s["sCn"]}
                             for s in content.get("sentence", {}).get("sentences", [])]

                phrases = [{"phrase": p["pContent"], "trans": p["pCn"]}
                           for p in content.get("phrase", {}).get("phrases", [])]

                related_words = []
                for rel in content.get("relWord", {}).get("rels", []):
                    for word in rel.get("words", []):
                        related_words.append({
                            "pos": rel["pos"],
                            "word": word["hwd"],
                            "trans": word["tran"]
                        })

                translations = [{
                    "pos": t["pos"],
                    "chinese": t["tranCn"],
                    "english": t.get("tranOther", "[暂无英英释义]")
                } for t in content.get("trans", [])]
                # 插入合并表
                insert_sql = """
                                INSERT INTO english.combined_words 
                                (word_id, word_rank, head_word, book_id, us_phone, uk_phone,
                                 us_speech, uk_speech, sentences, phrases, related_words, translations)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """

                # 执行插入操作
                cur.execute(insert_sql, (
                    word_data["content"]["word"]["wordId"],
                    word_data["wordRank"],
                    word_data["headWord"],
                    word_data["bookId"],
                    content.get("usphone"),
                    content.get("ukphone"),
                    content.get("usspeech"),
                    content.get("ukspeech"),
                    json.dumps(sentences, ensure_ascii=False),
                    json.dumps(phrases, ensure_ascii=False),
                    json.dumps(related_words, ensure_ascii=False),
                    json.dumps(translations, ensure_ascii=False)
                ))

            return {"status": "success", "book_id": book_id}, book_id

        # 执行处理并提交事务
        result, book_id = process_upload()
        if result["status"] == "error":
            mysql.connection.rollback()
            return result["message"], 503
        mysql.connection.commit()
        return redirect(url_for('admin_dashboard', active_tab='library'))

    except json.JSONDecodeError:
        mysql.connection.rollback()
        return "无效的JSON文件格式", 504
    except KeyError as e:
        mysql.connection.rollback()
        return f"缺少必要字段: {str(e)}", 505
    except Exception as e:
        mysql.connection.rollback()
        print(f"添加失败: {str(e)}")
        return "服务器内部错误", 506


# 删除用户
@app.route('/delete/user/<string:user_id>')
def delete_user(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    active_tab = request.args.get('active_tab', 'user')

    try:

        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM user_db.users WHERE wechat_id = %s", (user_id,))
        mysql.connection.commit()
        return redirect(url_for('admin_dashboard', active_tab=active_tab))
    except Exception as e:
        mysql.connection.rollback()
        print(f"删除用户失败: {str(e)}")
        return "删除用户失败", 507


# 退出登录
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))







if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)