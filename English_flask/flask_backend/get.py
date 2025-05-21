import json
import pymysql
import sys


def get_book_name():
    """获取用户输入的词库名"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return input("请输入词库名称：")


def update_book_library(cursor, book_id, book_name):
    """更健壮的词库表更新"""
    try:
        # 先检查是否存在
        cursor.execute("SELECT 1 FROM book_library WHERE book_id = %s", (book_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO book_library (book_id, book_name) VALUES (%s, %s)",
                (book_id, book_name)
            )
            print(f"新增词库记录：{book_id} - {book_name}")
        else:
            print(f"词库已存在：{book_id}，跳过更新")
    except pymysql.Error as e:
        print(f"数据库操作失败：{str(e)}")
        raise


def process_json_file(filename, book_name):
    with open(filename, 'r', encoding='utf-8') as file:
        with conn.cursor() as cursor:
            # 先获取book_id（假设单个文件只包含一个book_id）
            first_line = file.readline().strip()
            book_id = json.loads(first_line)["bookId"]

            # 更新词库表
            update_book_library(cursor, book_id, book_name)

            # 重置文件指针并处理数据
            file.seek(0)
            for line in file.readlines():
                word_data = json.loads(line.strip())
                content = word_data["content"]["word"]["content"]

                # 处理嵌套数据
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
                                INSERT INTO combined_words 
                                (word_id, word_rank, head_word, book_id, us_phone, uk_phone,
                                 us_speech, uk_speech, sentences, phrases, related_words, translations)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                cursor.execute(insert_sql, (
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

            conn.commit()


if __name__ == "__main__":
    # 创建数据库连接
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='english',
        charset='utf8mb4'
    )

    try:
        # 获取用户输入
        book_name = get_book_name()

        # 执行处理json
        process_json_file("json/CET6_2.json", book_name)

        print(f"数据导入完成，词库'{book_name}'已登记")
    finally:
        conn.close()