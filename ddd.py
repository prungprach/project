import sqlite3

DB_NAME = "store.db"

def connect():
    return sqlite3.connect(DB_NAME)

def fix_duplicate_product_categories():
    conn = connect()
    c = conn.cursor()
    try:
        # สร้างตารางใหม่โดยมี UNIQUE constraint
        c.execute("""
            CREATE TABLE IF NOT EXISTS product_categories_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                category_id INTEGER,
                UNIQUE(product_id, category_id),
                FOREIGN KEY(product_id) REFERENCES products(id),
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        """)
        
        # คัดลอกข้อมูลจากตารางเก่าไปใหม่ แบบไม่เอาซ้ำ
        c.execute("""
            INSERT OR IGNORE INTO product_categories_new (product_id, category_id)
            SELECT product_id, category_id FROM product_categories
        """)

        # ลบตารางเก่า
        c.execute("DROP TABLE product_categories")

        # เปลี่ยนชื่อตารางใหม่เป็นของเดิม
        c.execute("ALTER TABLE product_categories_new RENAME TO product_categories")

        conn.commit()
        print("✅ แก้ไขตาราง product_categories เรียบร้อยแล้ว ไม่มีข้อมูลซ้ำ")
    except Exception as e:
        print("❌ เกิดข้อผิดพลาด:", e)
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_duplicate_product_categories()

