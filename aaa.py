import sqlite3
import os
import json
import re
import hashlib


DB_NAME = "store.db"

# -------------------- เชื่อมต่อฐานข้อมูล --------------------
def connect():
    return sqlite3.connect(DB_NAME)

# -------------------- เพิ่มคอลัมน์อัตโนมัติ --------------------
def add_description_column_if_not_exists():
    conn = connect()
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in c.fetchall()]
        if "description" not in columns:
            c.execute("ALTER TABLE products ADD COLUMN description TEXT DEFAULT ''")
            conn.commit()
            print("✅ เพิ่มคอลัมน์ description สำเร็จ")
    except Exception as e:
        print("⚠️ ไม่สามารถเพิ่มคอลัมน์ description:", e)
    finally:
        conn.close()


def add_unit_price_column_if_not_exists():
    conn = connect()
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(order_items)")
        cols = [col[1] for col in c.fetchall()]
        if "unit_price" not in cols:
            c.execute("ALTER TABLE order_items ADD COLUMN unit_price REAL")
            conn.commit()
            print("✅ เพิ่มคอลัมน์ unit_price สำเร็จ")
    except Exception as e:
        print("⚠️ ไม่สามารถเพิ่มคอลัมน์ unit_price:", e)
    finally:
        conn.close()


# -------------------- สร้างตารางทั้งหมด --------------------
def create_admin_and_sample_products():
    conn = connect()
    c = conn.cursor()

    # Users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            phone TEXT,
            password TEXT
        )
    """)

    # Products
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            price REAL,
            stock INTEGER,
            unit TEXT,
            description TEXT DEFAULT ''
        )
    """)

    # Customer Info
    c.execute("""
        CREATE TABLE IF NOT EXISTS customer_info (
            email TEXT PRIMARY KEY,
            fullname TEXT,
            phone TEXT,
            address TEXT,
            subdistrict TEXT,
            district TEXT,
            province TEXT,
            postalcode TEXT
        )
    """)

    # Orders
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            address TEXT,
            items TEXT,
            total REAL,
            slip_path TEXT,
            status TEXT DEFAULT 'รอตรวจสอบ',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Order items
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    # Admin เริ่มต้น
    c.execute("INSERT OR IGNORE INTO users (email, name, phone, password) VALUES (?,?,?,?)",
              ("admin@store.com", "Admin", "0000000000", "admin123"))

    conn.commit()
    conn.close()

    add_description_column_if_not_exists()
    add_unit_price_column_if_not_exists()
    create_category_table()

# -------------------- Users --------------------
import hashlib
#เพิ่มผู้ใช้ใหม่ลงฐานข้อมูลโดย เข้ารหัสรหัสผ่านด้วย SHA256 ก่อนเก็บเพื่อความปลอดภัย
def add_user(email, name, phone, password):
    conn = connect()
    c = conn.cursor()
    try:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()  # ✅ เข้ารหัสก่อนบันทึก
        c.execute("INSERT INTO users (email, name, phone, password) VALUES (?,?,?,?)",
                  (email, name, phone, hashed_pw))
        conn.commit()
        return True
    except Exception as e:
        print("Add user error:", e)
        return False
    finally:
        conn.close()

#ตรวจสอบว่ามีผู้ใช้ที่อีเมลและรหัสผ่านนี้หรือไม่ (ใช้ตอนล็อกอิน)
def get_user(email, password):
    conn = connect()
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()  # ✅ เข้ารหัสก่อนตรวจสอบ
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hashed_pw))
    user = c.fetchone()
    conn.close()
    return user


#ดึงข้อมูลผู้ใช้จากอีเมล (เช่น ใช้ตอนกู้รหัสผ่าน)
def get_user_by_email(email):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return user

#เปลี่ยนรหัสผ่านใหม่ให้ผู้ใช้ โดยเข้ารหัสก่อนบันทึก
def update_user_password(email, new_password):
    conn = connect()
    c = conn.cursor()
    hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
    c.execute("UPDATE users SET password=? WHERE email=?", (hashed_pw, email))
    conn.commit()
    conn.close()



# -------------------- Products --------------------
#ดึงข้อมูลสินค้าทั้งหมดจากฐานข้อมูล
def get_products():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return products

#เพิ่มสินค้าใหม่ พร้อมราคาต่อหน่วย จำนวนคงเหลือ และคำอธิบายสินค้า
def add_product(name, price, stock, unit, description=""):
    conn = connect()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO products (name, price, stock, unit, description) VALUES (?,?,?,?,?)",
                  (name, price, stock, unit, description))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

#แก้ไขข้อมูลสินค้า เช่น ชื่อ ราคา จำนวน หรือคำอธิบาย
def update_product(pid, name, price, stock, unit, description=""):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE products SET name=?, price=?, stock=?, unit=?, description=? WHERE id=?",
              (name, price, stock, unit, description, pid))
    conn.commit()
    conn.close()

#ลบสินค้าตามรหัส ID
def delete_product(pid):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()

#ดึงข้อมูลสินค้าทั้งหมดในรูปแบบ list ของ dict เพื่อใช้งานง่ายในโปรแกรม
def get_products_dict():
    products = get_products()
    return [
        {
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "stock": p[3],
            "unit": p[4],
            "description": p[5] if len(p) > 5 else ""
        }
        for p in products
    ]

# -------------------- Categories --------------------
def create_category_table():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS product_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            category_id INTEGER,
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
    """)
    conn.commit()

    # ✅ เพิ่มหมวดหมู่พื้นฐานถ้ายังไม่มี
    default_cats = [
        "หมวดเสริมโปรตีน / เสริมกล้ามเนื้อ",
        "หมวดเสริมพลังงาน / เพิ่มสมรรถนะการออกกำลังกาย",
        "หมวดควบคุมน้ำหนัก / เผาผลาญไขมัน",
        "หมวดวิตามินและแร่ธาตุเสริม",
        "หมวดฟื้นฟูร่างกาย / Recovery"
    ]
    for cat in default_cats:
        c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    conn.commit()
    conn.close()


def get_all_categories():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM categories ORDER BY id")
    cats = c.fetchall()
    conn.close()
    return cats


def get_product_category(product_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT categories.name FROM categories
        JOIN product_categories ON categories.id = product_categories.category_id
        WHERE product_categories.product_id = ?
    """, (product_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None



# -------------------- Customer Info --------------------
#บันทึกหรืออัปเดตข้อมูลที่อยู่ลูกค้า (ใช้ในขั้นตอนสั่งซื้อ)
def save_customer_info(email, fullname, phone, address, subdistrict, district, province, postalcode):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO customer_info 
        (email, fullname, phone, address, subdistrict, district, province, postalcode)
        VALUES (?,?,?,?,?,?,?,?)
    """, (email, fullname, phone, address, subdistrict, district, province, postalcode))
    conn.commit()
    conn.close()

#ดึงข้อมูลที่อยู่ของลูกค้าจากอีเมล
def get_customer_info(email):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM customer_info WHERE email=?", (email,))
    info = c.fetchone()
    conn.close()
    return info


# -------------------- Orders --------------------
from datetime import datetime, timedelta
#เพิ่มคำสั่งซื้อใหม่
def add_order(email, customer_name, customer_phone, address, items, total, slip_path):
    import json
    conn = connect()
    c = conn.cursor()

    # เวลาปัจจุบันไทย UTC+7
    now = datetime.utcnow() + timedelta(hours=7)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        INSERT INTO orders (email, customer_name, customer_phone, address, items, total, slip_path, status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (email, customer_name, customer_phone, address, items, total, slip_path, "รอตรวจสอบ", now_str))
    
    order_id = c.lastrowid

    # แปลง items เป็น order_items และตัดสต็อกเหมือนเดิม
    try:
        cart = json.loads(items) if isinstance(items, str) else items
    except:
        cart = []

    for it in cart:
        name = it.get("name")
        qty = int(it.get("qty", 0))
        if not name or qty <= 0:
            continue
        c.execute("SELECT id, price, stock FROM products WHERE name=?", (name,))
        row = c.fetchone()
        if not row:
            continue
        product_id, current_price, stock = row
        unit_price = float(it.get("price", current_price))
        c.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (?,?,?,?)
        """, (order_id, product_id, qty, unit_price))


    conn.commit()
    conn.close()
    return order_id, now_str


#ดึงคำสั่งซื้อทั้งหมด (ใช้ในหน้า Admin)
def get_all_orders():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT id, email, customer_name, customer_phone, address, items, total, slip_path, status, created_at
        FROM orders
        ORDER BY created_at DESC
    """)
    orders = c.fetchall()
    conn.close()
    return orders


# -------------------- อัปเดตสถานะคำสั่งซื้อ --------------------
#เปลี่ยนสถานะคำสั่งซื้อ เช่น “รอชำระเงิน” → “ชำระเงินแล้ว”
def update_order_status(order_id, new_status):
    """
    อัปเดตสถานะคำสั่งซื้อ และตัดสต็อกเฉพาะตอนเปลี่ยนจาก 'รอชำระเงิน' → 'ชำระเงินแล้ว'
    """
    from datetime import datetime, timedelta
    conn = connect()
    c = conn.cursor()

    try:
        # ดึงสถานะเก่าและรายการสินค้า
        c.execute("SELECT status, items FROM orders WHERE id=?", (order_id,))
        row = c.fetchone()
        if not row:
            print("❌ ไม่พบคำสั่งซื้อ")
            return
        old_status, items_json = row

        import json
        items = json.loads(items_json) if isinstance(items_json, str) else []

        # ถ้าเพิ่งเปลี่ยนจาก "รอชำระเงิน" → "ชำระเงินแล้ว" ให้ตัดสต็อก
        if old_status == "รอชำระเงิน" and new_status == "ชำระเงินแล้ว":
            for item in items:
                name = item.get("name")
                qty = int(item.get("qty", 0))
                if not name or qty <= 0:
                    continue

                # ดึงสินค้า
                c.execute("SELECT id, stock FROM products WHERE name=?", (name,))
                product = c.fetchone()
                if not product:
                    continue
                pid, stock = product
                new_stock = max(stock - qty, 0)
                c.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, pid))
                print(f"ลดสต็อก {name}: {stock} → {new_stock}")

        # ✅ ใช้เวลาปัจจุบันของไทย (UTC+7)
        now = datetime.utcnow() + timedelta(hours=7)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # อัปเดตสถานะใหม่และเวลา
        c.execute("UPDATE orders SET status=?, created_at=? WHERE id=?",
                  (new_status, now_str, order_id))
        conn.commit()
        print(f"✅ อัปเดตสถานะคำสั่งซื้อ #{order_id}: {old_status} → {new_status} ({now_str})")

    except Exception as e:
        print("⚠️ เกิดข้อผิดพลาดใน update_order_status:", e)
        conn.rollback()
    finally:
        conn.close()


#ลบคำสั่งซื้อออกจากฐานข้อมูล
def delete_order(order_id):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
    c.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

# -------------------- สรุปยอดขาย --------------------
#ดึงยอดรวมของคำสั่งซื้อที่ “ชำระเงินแล้ว”
def get_sales_summary():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*), SUM(total)
        FROM orders
        WHERE status='ชำระเงินแล้ว'
    """)
    summary = c.fetchone()
    conn.close()
    return {
        "total_orders": summary[0] or 0,
        "total_income": summary[1] or 0.0
    }

#รวมยอดขายแยกตาม “วันที่ขาย”
def get_sales_by_date():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT DATE(created_at), SUM(total)
        FROM orders
        WHERE status='ชำระเงินแล้ว'
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at) DESC
    """)
    data = c.fetchall()
    conn.close()
    return data

#ดึงคำสั่งซื้อที่ “ชำระเงินแล้ว” ทั้งหมด
def get_all_paid_orders():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT id, total, created_at
        FROM orders
        WHERE status='ชำระเงินแล้ว'
        ORDER BY created_at DESC
    """)
    orders = c.fetchall()
    order_list = []
    for order_id, total, created_at in orders:
        c.execute("""
            SELECT p.name, oi.quantity,
                CASE
                    WHEN oi.unit_price > (p.price * 2) THEN p.price * oi.quantity
                    ELSE COALESCE(oi.unit_price, p.price) * oi.quantity
                END AS subtotal
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        """, (order_id,))
        items = c.fetchall()
        order_list.append({
            "id": order_id,
            "total": total,
            "created_at": created_at,
            "items": items
        })
    conn.close()
    return order_list

#รวมยอดขายตามสินค้าในแต่ละวัน
def get_sales_by_product():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT 
            p.name,
            SUM(oi.quantity),
            SUM(
                CASE
                    -- ถ้า unit_price มากกว่าราคาสินค้าเกิน 2 เท่า แปลว่าเก็บเป็นยอดรวม (subtotal)
                    WHEN oi.unit_price > p.price * 2 THEN (oi.unit_price / oi.quantity)
                    ELSE COALESCE(oi.unit_price, p.price)
                END * oi.quantity
            ),
            DATE(o.created_at)
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        JOIN orders o ON o.id = oi.order_id
        WHERE o.status='ชำระเงินแล้ว'
        GROUP BY p.name, DATE(o.created_at)
        ORDER BY DATE(o.created_at) DESC
    """)
    data = c.fetchall()
    conn.close()
    return data



# -------------------- Backfill order_items --------------------
def backfill_all_order_items():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, items FROM orders")
    rows = c.fetchall()

    for order_id, items in rows:
        c.execute("SELECT COUNT(*) FROM order_items WHERE order_id=?", (order_id,))
        if (c.fetchone()[0] or 0) > 0:
            continue

        try:
            cart = json.loads(items) if isinstance(items, str) else (items or [])
        except Exception:
            cart = []

        if not cart and items:
            cart = []
            for line in items.split("\n"):
                m = re.match(r"(.+?) x(\d+) = ([\d,.]+)", line.strip())
                if not m:
                    continue
                name, qty, price = m.groups()
                cart.append({
                    "name": name.strip(),
                    "qty": int(qty),
                    "price": float(price.replace(",", ""))
                })

        for it in cart:
            name = it.get("name")
            qty = int(it.get("qty", 0) or 0)
            if not name or qty <= 0:
                continue
            c.execute("SELECT id, price FROM products WHERE name=?", (name,))
            prow = c.fetchone()
            if not prow:
                continue
            product_id, current_price = prow
            unit_price = float(it.get("price", current_price) or current_price)
            c.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?,?,?,?)
            """, (order_id, product_id, qty, unit_price))

    conn.commit()
    conn.close()


# -------------------- เรียกตอนเริ่มโปรแกรม --------------------
create_admin_and_sample_products()


def fix_unit_price_data():
    """
    ตรวจสอบและแก้ไขข้อมูลใน order_items ให้ unit_price เป็นราคาต่อชิ้นที่ถูกต้อ
    """
    conn = connect()
    c = conn.cursor()

    # ดึงข้อมูลทั้งหมดจาก order_items พร้อมราคาสินค้าจริง
    c.execute("""
        SELECT oi.id, oi.product_id, oi.quantity, oi.unit_price, p.price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
    """)
    rows = c.fetchall()

    fixed_count = 0
    for row in rows:
        oi_id, product_id, qty, unit_price, correct_price = row

        # ถ้า unit_price เกินราคาจริง * 2 แสดงว่ามันเก็บเป็นยอดรวม (subtotal)
        if unit_price is not None and correct_price is not None and unit_price > correct_price * 2:
            new_unit_price = unit_price / qty  # แปลงกลับเป็นราคาต่อชิ้น
            c.execute("UPDATE order_items SET unit_price = ? WHERE id = ?", (new_unit_price, oi_id))
            fixed_count += 1

    conn.commit()
    conn.close()
    print(f"✅ แก้ไขข้อมูล unit_price ทั้งหมด {fixed_count} รายการเรียบร้อยแล้ว")

def get_orders_by_email(email):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE email=? ORDER BY id DESC", (email,))
    data = c.fetchall()
    conn.close()
    return data

# -------------------- ✅ ฟังก์ชันเข้ารหัสรหัสผ่านเก่าทั้งหมด --------------------
def hash_existing_passwords():
    """
    เข้ารหัสรหัสผ่านทั้งหมดที่ยังเป็น plain text (ยังไม่ถูก hash)
    """
    conn = connect()
    c = conn.cursor()
    import hashlib

    c.execute("SELECT email, password FROM users")
    users = c.fetchall()
    updated_count = 0

    for email, password in users:
        # ถ้ายังไม่ hash (ไม่ยาว 64 ตัว หรือไม่มีแค่ [0-9a-f])
        if not password or len(password) != 64 or not all(ch in "0123456789abcdef" for ch in password.lower()):
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            c.execute("UPDATE users SET password=? WHERE email=?", (hashed_pw, email))
            updated_count += 1

    conn.commit()
    conn.close()

    if updated_count > 0:
        print(f"🔒 เข้ารหัสรหัสผ่านเก่าทั้งหมดแล้ว {updated_count} บัญชี")
    else:
        print("✅ ไม่มีรหัสผ่านเก่าที่ต้องเข้ารหัส")


# ✅ เรียกใช้ทันทีตอนเริ่มโปรแกรม
hash_existing_passwords()
#ดึงจำนวนสต็อกปัจจุบันของสินค้าตามรหัส
def get_product_stock(pid):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT stock FROM products WHERE id=?", (pid,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0
#ลดจำนวนสินค้าตามที่ขายไป (เฉพาะถ้ามีของพอ)
def update_product_stock(pid, qty):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?", (qty, pid, qty))
    conn.commit()
    conn.close()


# ดึงคำสั่งซื้อ “ชำระเงินแล้ว” ในช่วงวันที่ที่กำหนด
def get_orders_by_date_range(start_date, end_date):
    """
    คืนรายการคำสั่งซื้อที่ status='ชำระเงินแล้ว' ในช่วงวันที่ (inclusive).
    คืนเป็น list ของ dict: {id, total, created_at, items:[(name,qty,subtotal),...]}
    ฟอร์แมตรับ start_date/end_date เป็น 'YYYY-MM-DD'
    """
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, total, created_at, items
            FROM orders
            WHERE status='ชำระเงินแล้ว'
              AND DATE(created_at) BETWEEN ? AND ?
            ORDER BY created_at ASC
        """, (start_date, end_date))
        rows = cur.fetchall()
    finally:
        conn.close()

    import json
    result = []
    for r in rows:
        order_id, total, created_at, items_blob = r
        parsed_items = []
        if not items_blob:
            # ไม่มีข้อมูล items
            parsed_items = []
        else:
            # พยายาม parse เป็น JSON ก่อน ถ้าไม่สำเร็จ ให้ fallback อ่านเป็นบรรทัดแบบเก่า
            try:
                items = json.loads(items_blob)
                if isinstance(items, list):
                    for it in items:
                        try:
                            name = it.get("name", "ไม่ระบุชื่อสินค้า")
                            qty = int(it.get("qty", 0) or 0)
                            price = float(it.get("price", 0) or 0)
                            subtotal = qty * price
                            parsed_items.append((name, qty, subtotal))
                        except Exception:
                            # ข้ามรายการที่ parse ไม่ได้
                            continue
                else:
                    parsed_items = []
            except Exception:
                # fallback: ถ้า items_blob เป็น text แบบ "Product x2 = 240.00" ต่อบรรทัด
                try:
                    parsed_items = []
                    for line in str(items_blob).splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        # พยายามจับรูปแบบ "ชื่อ xN = PRICE"
                        m = re.match(r"(.+?) x(\d+)\s*=\s*([\d,\.]+)", line)
                        if m:
                            nm = m.group(1).strip()
                            q = int(m.group(2))
                            p = float(m.group(3).replace(",", ""))
                            parsed_items.append((nm, q, p))
                except Exception:
                    parsed_items = []

        result.append({
            "id": order_id,
            "total": total or 0.0,
            "created_at": created_at,
            "items": parsed_items
        })
    return result


# รวมยอดขายตามสินค้าในช่วงวันที่ที่กำหนด
def get_sales_by_product_range(start_date, end_date):
    """
    รวมยอดขายตามสินค้าในช่วงวันที่ (รวมเฉพาะ orders.status='ชำระเงินแล้ว')
    คืน list ของ (name, qty_sum, subtotal_sum)
    """
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT items
            FROM orders
            WHERE status='ชำระเงินแล้ว'
              AND DATE(created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        rows = cur.fetchall()
    finally:
        conn.close()

    product_sales = {}
    import json
    for (items_blob,) in rows:
        if not items_blob:
            continue
        try:
            items = json.loads(items_blob)
            if isinstance(items, list):
                for it in items:
                    try:
                        name = it.get("name", "ไม่ระบุชื่อสินค้า")
                        qty = int(it.get("qty", 0) or 0)
                        price = float(it.get("price", 0) or 0)
                        subtotal = qty * price
                        if name not in product_sales:
                            product_sales[name] = {"qty": 0, "subtotal": 0.0}
                        product_sales[name]["qty"] += qty
                        product_sales[name]["subtotal"] += subtotal
                    except Exception:
                        continue
            else:
                continue
        except Exception:
            # fallback อ่านไลน์แบบเก่า
            try:
                for line in str(items_blob).splitlines():
                    m = re.match(r"(.+?) x(\d+)\s*=\s*([\d,\.]+)", line.strip())
                    if not m:
                        continue
                    name = m.group(1).strip()
                    qty = int(m.group(2))
                    price_val = float(m.group(3).replace(",", ""))
                    subtotal = qty * price_val
                    if name not in product_sales:
                        product_sales[name] = {"qty": 0, "subtotal": 0.0}
                    product_sales[name]["qty"] += qty
                    product_sales[name]["subtotal"] += subtotal
            except Exception:
                continue

    result = [(name, data["qty"], data["subtotal"]) for name, data in product_sales.items()]
    # หากต้องการเรียงตามยอดล่าสุด/มาก→น้อย ให้ sort:
    result.sort(key=lambda x: x[2], reverse=True)
    return result

def remove_duplicate_order_items():
    """
    ลบรายการ order_items ที่ซ้ำกัน (order_id + product_id ซ้ำ)
    เก็บเฉพาะรายการแรกไว้
    """
    conn = connect()
    c = conn.cursor()

    c.execute("""
        DELETE FROM order_items 
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM order_items
            GROUP BY order_id, product_id
        )
    """)
    conn.commit()
    conn.close()
    print("🧹 ล้างข้อมูล order_items ซ้ำเรียบร้อยแล้ว")


# -------------------- ลดจำนวนสต็อกจากสินค้า --------------------
def reduce_product_stock(product_id, quantity):
    conn = connect()
    c = conn.cursor()
    try:
        # ดึงจำนวนคงเหลือปัจจุบัน
        c.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
        result = c.fetchone()
        if result:
            current_stock = result[0]
            new_stock = max(current_stock - quantity, 0)
            c.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
            conn.commit()
    except Exception as e:
        print("❌ Error reducing stock:", e)
    finally:
        conn.close()

# -------------------- ตารางข้อความลูกค้า --------------------
def recreate_messages_table():
    conn = connect()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS messages")
    c.execute("""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            phone TEXT,
            email TEXT,
            message TEXT,
            image TEXT,
            reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ รีเซ็ตตาราง messages เรียบร้อยแล้ว")


# -------------------- ฟังก์ชันเพิ่มข้อความ --------------------
# ลูกค้าส่งข้อความ/รูปภาพ เข้าสู่ระบบ
def add_message(sender, phone, email, message, image=None):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO messages (sender, phone, email, message, image)
        VALUES (?,?,?,?,?)
    """, (sender, phone, email, message, image))
    conn.commit()
    conn.close()


# -------------------- ฟังก์ชันดึงข้อความทั้งหมด --------------------
#ดึงข้อความทั้งหมด (สำหรับแอดมินดู)
def get_all_messages():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT id, sender, phone, email, message, image, reply, created_at
        FROM messages
        ORDER BY created_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows


# -------------------- ฟังก์ชันตอบกลับข้อความ --------------------
#แอดมินตอบกลับข้อความลูกค้า
def reply_message(msg_id, reply_text):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE messages SET reply = ? WHERE id = ?", (reply_text, msg_id))
    conn.commit()
    conn.close()


# -------------------- ฟังก์ชันดึงข้อความเฉพาะของผู้ใช้ --------------------
#ดึงข้อความที่ลูกค้าคนนั้นเคยส่งมา (แสดงในหน้าโปรไฟล์ลูกค้า)
def get_messages_by_email(email):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT id, sender, phone, email, message, image, reply, created_at 
        FROM messages 
        WHERE email = ? ORDER BY created_at DESC
    """, (email,))
    rows = c.fetchall()
    conn.close()
    return rows

def remove_duplicate_product_categories():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        DELETE FROM product_categories
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM product_categories
            GROUP BY product_id, category_id
        )
    """)
    conn.commit()
    conn.close()
    print("🧹 ล้าง product_categories ซ้ำเรียบร้อยแล้ว")

def get_products_by_category(cat_id):
    conn = connect()
    c = conn.cursor()
    if cat_id == 0:  # หมวด "ทั้งหมด"
        c.execute("SELECT * FROM products")
    else:
        c.execute("""
            SELECT DISTINCT p.* FROM products p
            JOIN product_categories pc ON p.id = pc.product_id
            WHERE pc.category_id = ?
        """, (cat_id,))
    products = c.fetchall()
    conn.close()
    return products

def assign_product_to_category(product_id, category_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT 1 FROM product_categories WHERE product_id = ? AND category_id = ?
    """, (product_id, category_id))
    if c.fetchone() is None:
        c.execute("INSERT INTO product_categories (product_id, category_id) VALUES (?, ?)", (product_id, category_id))
    conn.commit()
    conn.close()

