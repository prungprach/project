import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import os, shutil, webbrowser
from datetime import datetime, timedelta
import db
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from functools import partial

VAT_RATE = 0.07  # อัตราภาษีมูลค่าเพิ่ม 7%

class UserDashboard(ctk.CTkFrame):
    def __init__(self, master, products):
        super().__init__(master)
        self.master = master
        self.products = products
        self.cart = {}
        self.slip_path = None

        # 🟩 เพิ่มตัวแปรเก็บหมวดหมู่ที่เลือก
        self.selected_category = "ทั้งหมด"

        self.create_ui()

    def create_ui(self):
        # ================= Background =================
        bg_path = os.path.join("assets", "sho.png")
        if os.path.exists(bg_path):
            bg_img = Image.open(bg_path)
            window_width = self.winfo_screenwidth()
            window_height = self.winfo_screenheight()
            bg_img = bg_img.resize((window_width, window_height), Image.LANCZOS)
            self.bg_ctk = ctk.CTkImage(light_image=bg_img, size=(window_width, window_height))
            self.bg_label = ctk.CTkLabel(self, image=self.bg_ctk, text="")
            self.bg_label.place(x=0, y=0)
        else:
            self.configure(fg_color="#1f1f1f")

        # ================= Scrollable Main Frame =================
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF")
        self.main_scroll.pack(fill="both", expand=True)

        # ================= Top Bar =================
        top_bar = ctk.CTkFrame(self.main_scroll, fg_color="#FFFFFF", height=80, corner_radius=0)
        top_bar.pack(fill="x", pady=(0, 10))

        title = ctk.CTkLabel(top_bar, text="GYMLION STORE", font=("Segoe UI Black", 28), text_color="#1E88E5")
        title.pack(side="left", padx=25, pady=20)

        # ปุ่มด้านขวา
        btn_style = dict(
            fg_color="#1E88E5",
            hover_color="#1565C0",
            text_color="white",
            corner_radius=20,
            height=36
        )

        cart_btn = ctk.CTkButton(top_bar, text="🛒 ตะกร้า / ชำระเงิน", width=160, **btn_style, command=self.open_cart)
        cart_btn.pack(side="right", padx=10, pady=20)

        history_btn = ctk.CTkButton(top_bar, text="📦 ประวัติคำสั่งซื้อ", width=150, **btn_style, command=self.open_order_history)
        history_btn.pack(side="right", padx=10, pady=20)

        info_btn = ctk.CTkButton(top_bar, text="👤 ข้อมูลลูกค้า", width=140, **btn_style, command=self.open_customer_info)
        info_btn.pack(side="right", padx=10, pady=20)

        contact_btn = ctk.CTkButton(top_bar, text="📞 ติดต่อร้านค้า", width=130, **btn_style, command=self.open_contact)
        contact_btn.pack(side="right", padx=10, pady=20)

        about_btn = ctk.CTkButton(top_bar, text="ℹ️ About us", width=120, **btn_style, command=self.open_about)
        about_btn.pack(side="right", padx=10, pady=20)

        logout_btn = ctk.CTkButton(top_bar, text="🚪 ออกจากระบบ", width=130, **btn_style, command=self.logout)
        logout_btn.pack(side="right", padx=10, pady=20)

        # ================= Banner Section =================
        banner_path = os.path.join("assets", "banner.png")
        if os.path.exists(banner_path):
            banner_img = Image.open(banner_path)
            screen_w = self.winfo_screenwidth()
            banner_height = int(screen_w * 500 / 1920)
            banner_img = banner_img.resize((screen_w, banner_height), Image.LANCZOS)
            self.banner_ctk = ctk.CTkImage(light_image=banner_img, size=(screen_w, banner_height))
            banner_label = ctk.CTkLabel(self.main_scroll, image=self.banner_ctk, text="")
            banner_label.pack(fill="x", pady=(0, 10))
        else:
            banner_label = ctk.CTkLabel(self.main_scroll, text="(ไม่พบภาพแบนเนอร์)", font=("Segoe UI", 20))
            banner_label.pack(fill="x", pady=10)

        # ================= Section Title =================
        section_title = ctk.CTkLabel(self.main_scroll, text="สินค้าแนะนำ", font=("Segoe UI Semibold", 24), text_color="#333333")
        section_title.pack(anchor="w", padx=30, pady=(10, 10))

        # ================= Category Filter =================
        category_frame = ctk.CTkFrame(self.main_scroll, fg_color="#FFFFFF")
        category_frame.pack(fill="x", padx=30, pady=(5, 5))

        ctk.CTkLabel(category_frame, text="หมวดหมู่สินค้า:", font=("Segoe UI", 16), text_color="#333").pack(side="left")

        # 🟩 เพิ่มรายชื่อหมวดหมู่ที่ต้องการ
        categories = [
            "ทั้งหมด",
            "หมวดเสริมโปรตีน / เสริมกล้ามเนื้อ",
            "หมวดเสริมพลังงาน / เพิ่มสมรรถนะการออกกำลังกาย",
            "หมวดควบคุมน้ำหนัก / เผาผลาญไขมัน",
            "หมวดวิตามินและแร่ธาตุเสริม",
            "หมวดฟื้นฟูร่างกาย / Recovery"
        ]


        self.category_option = ctk.CTkOptionMenu(
            category_frame,
            values=categories,
            fg_color="#1E88E5",
            button_color="#1565C0",
            text_color="white",
            command=self.filter_by_category
        )
        self.category_option.pack(side="left", padx=10, pady=5)

        # ================= Product Section =================
        self.product_frame = ctk.CTkFrame(self.main_scroll, fg_color="#F8F9FA")
        self.product_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # โหลดสินค้า
        self.load_products()

        # ================= Footer =================
        footer = ctk.CTkLabel(self.main_scroll, text="© 2025 GYMLION STORE. All rights reserved.",
                            font=("Segoe UI", 14), text_color="#666666")
        footer.pack(pady=(20, 10))

        # ================= Bind Resize =================
        self.bind("<Configure>", self._resize_bg)

    # ================= ฟังก์ชันกรองหมวดหมู่ =================
    def filter_by_category(self, selected):
        self.selected_category = selected
        self.load_products()

    # ================= Products =================


# ================= Products =================


    def load_products(self):
        from functools import partial
        from tkinter import messagebox

        for widget in self.product_frame.winfo_children():
            widget.destroy()

        # --- โหลดสินค้าจาก DB ---
        conn = db.connect()
        c = conn.cursor()
        if self.selected_category == "ทั้งหมด":
            c.execute("SELECT * FROM products")
        else:
            c.execute("""
                SELECT p.* FROM products p
                JOIN product_categories pc ON p.id = pc.product_id
                JOIN categories c2 ON pc.category_id = c2.id
                WHERE c2.name = ?
            """, (self.selected_category,))
        products = c.fetchall()
        conn.close()

        keys = ["id", "name", "price", "stock", "unit", "description"]
        self.products = [dict(zip(keys, p)) for p in products]

        # แปลง stock ให้เป็น int
        for p in self.products:
            try:
                p["stock"] = int(p["stock"])
            except (TypeError, ValueError):
                p["stock"] = 0

        columns = 4
        row, col = 0, 0

        # ----------------- ฟังก์ชันปรับจำนวนสินค้า -----------------
        def remove_qty(pid, var):
            current_qty = self.cart.get(pid, 0)
            if current_qty > 0:
                self.cart[pid] = current_qty - 1
                if self.cart[pid] == 0:
                    self.cart.pop(pid)
            else:
                self.cart.pop(pid, None)
            var.set(str(self.cart.get(pid, 0)))
            self.load_products()

        def add_qty(pid, var):
            product = next((p for p in self.products if p["id"] == pid), None)
            if not product:
                return
            stock = product["stock"]
            current_qty = self.cart.get(pid, 0)
            if current_qty < stock:
                self.cart[pid] = current_qty + 1
            else:
                messagebox.showwarning("สินค้าไม่เพียงพอ", f"สินค้า \"{product['name']}\" มีในสต็อกเพียง {stock} ชิ้น")
            var.set(str(self.cart.get(pid, 0)))
            self.load_products()

        def on_qty_change(event, pid, var):
            product = next((p for p in self.products if p["id"] == pid), None)
            if not product:
                return
            stock = product["stock"]
            val = var.get()
            if val.isdigit():
                q = int(val)
                if q > stock:
                    messagebox.showwarning("สินค้าไม่เพียงพอ", f"สินค้า \"{product['name']}\" มีในสต็อกเพียง {stock} ชิ้น")
                    q = stock
                if q > 0:
                    self.cart[pid] = q
                else:
                    self.cart.pop(pid, None)
                var.set(str(q))
            else:
                messagebox.showwarning("แจ้งเตือน", "กรุณากรอกตัวเลขเท่านั้น")
                var.set(str(self.cart.get(pid, 0)))
            self.load_products()

        # ----------------- สร้างกรอบสินค้า -----------------
        for p in self.products:
            frame = ctk.CTkFrame(
                self.product_frame,
                fg_color="#FFFFFF",
                corner_radius=20,
                border_width=0
            )
            frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

            # รูปสินค้า
            img_path = os.path.join("assets", f"{p['name']}.png")
            if os.path.exists(img_path):
                img = Image.open(img_path).resize((140, 140))
                photo = ctk.CTkImage(light_image=img, size=(140, 140))
                img_label = ctk.CTkLabel(frame, image=photo, text="")
                img_label.image = photo
                img_label.pack(pady=(10, 5))

            # ชื่อ / ราคา / Stock
            ctk.CTkLabel(frame, text=p['name'], font=("Segoe UI", 15, "bold"), text_color="#111111").pack()
            ctk.CTkLabel(frame, text=f"{p['price']:,.2f} ฿ / {p['unit']}", text_color="#1E88E5", font=("Segoe UI", 13, "bold")).pack()
            ctk.CTkLabel(frame, text=f"Stock: {p['stock']}", text_color="#757575", font=("Segoe UI", 11)).pack(pady=(2, 5))

            desc = p.get("description", "")
            if desc:
                ctk.CTkLabel(frame, text=desc, text_color="#666666", font=("Segoe UI", 10), wraplength=180, justify="center").pack(pady=(0, 8))

            # ----------------- แถวเพิ่ม/ลดสินค้า -----------------
            qty_frame = ctk.CTkFrame(frame, fg_color="#F1F3F4", corner_radius=12)
            qty_frame.pack(pady=(0, 10))
            qty_var = ctk.StringVar(value=str(self.cart.get(p['id'], 0)))

            ctk.CTkButton(qty_frame, text="-", width=30, height=28,
                        fg_color="#1E88E5", hover_color="#1565C0",
                        command=partial(remove_qty, p['id'], qty_var)).pack(side="left", padx=5)

            qty_entry = ctk.CTkEntry(qty_frame, textvariable=qty_var, width=50,
                                    justify="center", font=("Segoe UI", 13))
            qty_entry.pack(side="left")
            qty_entry.bind("<Return>", partial(on_qty_change, pid=p['id'], var=qty_var))
            qty_entry.bind("<FocusOut>", partial(on_qty_change, pid=p['id'], var=qty_var))

            ctk.CTkButton(qty_frame, text="+", width=30, height=28,
                        fg_color="#1E88E5", hover_color="#1565C0",
                        command=partial(add_qty, p['id'], qty_var)).pack(side="left", padx=5)

            col += 1
            if col >= columns:
                col = 0
                row += 1

        for i in range(columns):
            self.product_frame.grid_columnconfigure(i, weight=1)






    # ================= ปรับภาพพื้นหลังเมื่อขนาดหน้าต่างเปลี่ยน =================
    def _resize_bg(self, event=None):
        """ปรับภาพพื้นหลังให้เต็มหน้าจออัตโนมัติ"""
        try:
            if hasattr(self, "bg_ctk") and self.bg_ctk is not None:
                window_width = self.winfo_width()
                window_height = self.winfo_height()

                # โหลดภาพพื้นหลังใหม่ให้เต็มจอ
                bg_path = os.path.join("assets", "sho.png")
                if os.path.exists(bg_path):
                    from PIL import Image
                    bg_img = Image.open(bg_path)
                    bg_img = bg_img.resize((window_width, window_height))
                    self.bg_ctk = ctk.CTkImage(light_image=bg_img, size=(window_width, window_height))
                    self.bg_label.configure(image=self.bg_ctk)
        except Exception as e:
            print("❌ Error resizing background:", e)




            # ================= Cart / Checkout =================
    def open_cart(self):
        from functools import partial
        from tkinter import messagebox

        popup = ctk.CTkToplevel(self)
        popup.title("🛒 ตะกร้าสินค้า / ชำระเงิน")
        popup.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        popup.configure(fg_color="#FFFFFF")

        # ส่วนหัว
        header = ctk.CTkFrame(popup, fg_color="#1E88E5", height=60, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="🛒 ตะกร้าสินค้าของคุณ", font=("Segoe UI Black", 24), text_color="white").pack(pady=10)

        if not self.cart:
            ctk.CTkLabel(popup, text="ยังไม่มีสินค้าในตะกร้า", font=("Segoe UI", 18), text_color="#444").pack(pady=30)
            return

        # โหลด stock จาก DB ใหม่ทุกครั้ง
        conn = db.connect()
        c = conn.cursor()
        c.execute("SELECT id, stock FROM products")
        stock_data = {pid: s for pid, s in c.fetchall()}
        conn.close()

        cart_frame = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF")
        cart_frame.pack(fill="both", expand=True, padx=50, pady=20)

        subtotal = 0
        for pid, qty in list(self.cart.items()):
            stock = stock_data.get(pid, 0)

            # ข้อมูลสินค้า
            p = next((prod for prod in self.products if prod["id"] == pid), None)
            if not p:
                continue

            total = p["price"] * qty
            subtotal += total

            item_frame = ctk.CTkFrame(cart_frame, fg_color="#F7F7F7", corner_radius=15)
            item_frame.pack(fill="x", pady=10, padx=10)

            # รูปสินค้า
            img_path = os.path.join("assets", f"{p['name']}.png")
            if os.path.exists(img_path):
                img = Image.open(img_path).resize((100, 100))
                photo = ctk.CTkImage(light_image=img, size=(100, 100))
                img_label = ctk.CTkLabel(item_frame, image=photo, text="")
                img_label.image = photo
                img_label.pack(side="left", padx=15, pady=10)

            # ข้อมูลสินค้า
            info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=10)
            ctk.CTkLabel(info_frame, text=p["name"], font=("Segoe UI", 16, "bold"), text_color="#111").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"{p['price']:,.2f} ฿ / {p['unit']}", font=("Segoe UI", 13), text_color="#555").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Stock: {stock}", font=("Segoe UI", 11), text_color="#757575").pack(anchor="w")

            # ----------------- ฟังก์ชันเพิ่ม/ลด/กรอกจำนวน -----------------
            qty_frame = ctk.CTkFrame(item_frame, fg_color="#F1F3F4", corner_radius=12)
            qty_frame.pack(pady=(0, 10))
            qty_var = ctk.StringVar(value=str(self.cart.get(pid, 0)))

            def remove_qty(pid, var):
                current_qty = self.cart.get(pid, 0)
                if current_qty > 0:
                    self.cart[pid] = current_qty - 1
                    if self.cart[pid] == 0:
                        self.cart.pop(pid)
                else:
                    self.cart.pop(pid, None)
                var.set(str(self.cart.get(pid, 0)))
                popup.destroy()
                self.open_cart()

            def add_qty(pid, stock, var):
                current_qty = self.cart.get(pid, 0)
                if current_qty < stock:
                    self.cart[pid] = current_qty + 1
                else:
                    messagebox.showwarning("สินค้าไม่เพียงพอ", f"มีสินค้าในสต็อกเพียง {stock} ชิ้น")
                var.set(str(self.cart.get(pid, 0)))
                popup.destroy()
                self.open_cart()

            def on_cart_qty_change(event, pid, stock, var):
                val = var.get()
                if val.isdigit():
                    q = int(val)
                    if q > stock:
                        messagebox.showwarning("สินค้าไม่เพียงพอ", f"มีสินค้าในสต็อกเพียง {stock} ชิ้น")
                        q = stock
                    if q > 0:
                        self.cart[pid] = q
                    else:
                        self.cart.pop(pid, None)
                    var.set(str(q))
                else:
                    messagebox.showwarning("แจ้งเตือน", "กรุณากรอกตัวเลขเท่านั้น")
                    var.set(str(self.cart.get(pid, 0)))
                popup.destroy()
                self.open_cart()

            ctk.CTkButton(qty_frame, text="-", width=30, height=28,
                        fg_color="#1E88E5", hover_color="#1565C0",
                        command=partial(remove_qty, pid, qty_var)).pack(side="left", padx=5)

            qty_entry = ctk.CTkEntry(qty_frame, textvariable=qty_var, width=50,
                                    justify="center", font=("Segoe UI", 13))
            qty_entry.pack(side="left")
            qty_entry.bind("<Return>", partial(on_cart_qty_change, pid=pid, stock=stock, var=qty_var))
            qty_entry.bind("<FocusOut>", partial(on_cart_qty_change, pid=pid, stock=stock, var=qty_var))

            ctk.CTkButton(qty_frame, text="+", width=30, height=28,
                        fg_color="#1E88E5", hover_color="#1565C0",
                        command=partial(add_qty, pid, stock, qty_var)).pack(side="left", padx=5)

            # ----------------- ปุ่มลบสินค้า -----------------
            def delete_item(pid=pid):
                if messagebox.askyesno("ยืนยันการลบ", f"ต้องการลบ {p['name']} ออกจากตะกร้าหรือไม่?"):
                    del self.cart[pid]
                    popup.destroy()
                    self.open_cart()

            delete_btn = ctk.CTkButton(
                item_frame, text="🗑 ลบสินค้า", fg_color="#E53935", hover_color="#C62828",
                text_color="white", corner_radius=12, width=100, height=35,
                command=delete_item
            )
            delete_btn.pack(side="right", padx=20, pady=20)

        # สรุปยอด
        ctk.CTkLabel(popup, text=f"รวม: {subtotal:,.2f} ฿", font=("Segoe UI", 18, "bold"), text_color="#111").pack(pady=20)



        # คำนวณ VAT และยอดรวมสุทธิ
        vat_amount = round(subtotal * VAT_RATE, 2)
        grand_total = round(subtotal + vat_amount, 2)

        # ราคารวมทั้งหมด (แสดง Subtotal, VAT, Grand Total)
        total_frame = ctk.CTkFrame(popup, fg_color="#FFFFFF")
        total_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(total_frame, text=f"ยอดรวมย่อย (Subtotal): {subtotal:,.2f} ฿", font=("Segoe UI", 18), text_color="#333").pack(pady=(5,2))
        ctk.CTkLabel(total_frame, text=f"ภาษีมูลค่าเพิ่ม (VAT 7%): {vat_amount:,.2f} ฿", font=("Segoe UI", 18), text_color="#333").pack(pady=(2,2))
        ctk.CTkLabel(total_frame, text=f"ยอดรวมสุทธิ (Grand Total): {grand_total:,.2f} ฿", font=("Segoe UI Black", 20), text_color="#1E88E5").pack(pady=(2,10))
     


        # ปุ่มชำระเงิน -> ส่ง grand_total ไปยังหน้าชำระเงิน
        ctk.CTkButton(total_frame, text="ชำระเงินตอนนี้ 💳", fg_color="#1E88E5", hover_color="#1565C0",
                    text_color="white", corner_radius=20, height=45, width=200,
                    command=lambda: self.checkout_popup(subtotal, popup)).pack(side="right", padx=50, pady=10)


    def checkout_popup(self, subtotal, cart_popup):
        # คำนวณ VAT และยอดรวมสุทธิ
        vat_amount = round(subtotal * VAT_RATE, 2)
        grand_total = round(subtotal + vat_amount, 2)

        qr_popup = ctk.CTkToplevel(self)
        qr_popup.title("💳 ชำระเงิน")
        qr_popup.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        qr_popup.configure(fg_color="#FFFFFF")

        # 🟦 Scrollable Frame (แก้ปัญหาปุ่มหาย)
        main_frame = ctk.CTkScrollableFrame(qr_popup, fg_color="#FFFFFF")
        main_frame.pack(fill="both", expand=True)

        # ส่วนหัว
        header = ctk.CTkFrame(main_frame, fg_color="#1E88E5", height=60, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="ชำระเงินด้วย QR Code", font=("Segoe UI Black", 24), text_color="white").pack(pady=10)

        # QR Code
        qr_path = os.path.join("assets", "qr.png")
        if os.path.exists(qr_path):
            qr_img = Image.open(qr_path).resize((300, 300))
            qr_photo = ctk.CTkImage(light_image=qr_img, size=(300, 300))
            ctk.CTkLabel(main_frame, image=qr_photo, text="").pack(pady=30)
        else:
            ctk.CTkLabel(main_frame, text="(ไม่พบ QR Code)", text_color="#FF3333").pack(pady=30)

        # แสดงสรุปยอด (Subtotal, VAT, Grand Total) ที่หน้าชำระเงิน
        ctk.CTkLabel(main_frame, text=f"ยอดรวมย่อย (Subtotal): {subtotal:,.2f} ฿", font=("Segoe UI", 18), text_color="#333").pack(pady=(5,2))
        ctk.CTkLabel(main_frame, text=f"ภาษีมูลค่าเพิ่ม (VAT 7%): {vat_amount:,.2f} ฿", font=("Segoe UI", 18), text_color="#333").pack(pady=(2,2))
        ctk.CTkLabel(main_frame, text=f"ยอดรวมสุทธิ (Total to pay): {grand_total:,.2f} ฿", font=("Segoe UI Black", 20), text_color="#1E88E5").pack(pady=(2,10))

        # ยอดรวม (เดิม)
        ctk.CTkLabel(main_frame, text=f"ยอดชำระทั้งหมด: {grand_total:,.2f} ฿",
                    font=("Segoe UI", 20, "bold"), text_color="#1E88E5").pack(pady=10)

        # 🧾 พื้นที่อัปโหลดสลิป
        upload_frame = ctk.CTkFrame(main_frame, fg_color="#F5F5F5", corner_radius=20)
        upload_frame.pack(pady=20)
        slip_preview_label = ctk.CTkLabel(upload_frame, text="ยังไม่ได้อัปโหลดสลิป", text_color="#333")
        slip_preview_label.pack(pady=10)
        slip_img = [None]

        def upload_slip():
            file_path = filedialog.askopenfilename(title="เลือกสลิป", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if file_path:
                os.makedirs("slips", exist_ok=True)
                ext = os.path.splitext(file_path)[1]
                new_path = os.path.join("slips", f"slip_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")
                shutil.copy(file_path, new_path)
                self.slip_path = new_path

                # จำกัดขนาดสลิปไม่ให้ใหญ่เกิน
                img = Image.open(file_path)
                img.thumbnail((300, 300))

                slip_img[0] = ctk.CTkImage(light_image=img, size=(300, 300))
                slip_preview_label.configure(image=slip_img[0], text="")
                messagebox.showinfo("อัปโหลดสำเร็จ", f"บันทึกสลิปที่: {new_path}")

        ctk.CTkButton(upload_frame, text="📤 อัปโหลดสลิป",
                    command=upload_slip, fg_color="#1E88E5", hover_color="#1565C0").pack(pady=10)

        # ✅ ปุ่มยืนยันการชำระเงิน
        def confirm_payment():
            if not self.slip_path:
                messagebox.showwarning("แจ้งเตือน", "กรุณาอัปโหลดสลิปก่อนยืนยันการชำระเงิน")
                return

            # 🔸 ตรวจสอบว่าสินค้าในตะกร้ามีเพียงพอหรือไม่
            for pid, qty in self.cart.items():
                current_stock = db.get_product_stock(pid)
                if qty > current_stock:
                    p = next(p for p in self.products if p["id"] == pid)
                    messagebox.showerror(
                        "สินค้าไม่เพียงพอ",
                        f"สินค้า \"{p['name']}\" มีในสต็อกเพียง {current_stock} ชิ้น\nกรุณาปรับจำนวนใหม่อีกครั้ง"
                    )
                    return  # ❌ หยุดทันที ไม่บันทึกคำสั่งซื้อ

            # ✅ ถ้าสินค้าพอ -> ดำเนินการต่อ
            qr_popup.destroy()
            cart_popup.destroy()

            email = getattr(self.master.frames["login"], "current_user_email", None)
            info = db.get_customer_info(email)
            cart_items = {}
            for pid, qty in self.cart.items():
                p = next(p for p in self.products if p["id"] == pid)
                cart_items[pid] = {"name": p["name"], "qty": qty, "price": p["price"]}

            
                # 🔸 ลดสต็อกหลังจากตรวจสอบผ่านแล้ว
                db.reduce_product_stock(pid, qty)


            address = f"{info[3]} ต.{info[4]} อ.{info[5]} จ.{info[6]} {info[7]}"

            import json
            order_id, created_at = db.add_order(
                email, info[1], info[2], address,
                json.dumps(list(cart_items.values()), ensure_ascii=False),
                grand_total, self.slip_path
            )

            self.create_receipt_pdf(info, cart_items, subtotal, vat_amount, grand_total, order_id, created_at)
            messagebox.showinfo("สำเร็จ", "การสั่งซื้อเสร็จสิ้น ✅")

            self.cart.clear()
            self.slip_path = None


        # 🟩 แยกปุ่มไว้ด้านล่างสุด
        ctk.CTkButton(main_frame, text="ยืนยันการชำระเงิน ✅", fg_color="#1E88E5",
                    hover_color="#1565C0", text_color="white", height=45,
                    width=250, corner_radius=20, command=confirm_payment).pack(pady=40)

    # ================= Order History =================
    def open_order_history(self):
        """เปิดหน้าประวัติคำสั่งซื้อ (ลิงก์กับ open_orders)"""
        self.open_orders()


    # ================= About Us =================
    def open_about(self):
        popup = ctk.CTkToplevel(self)
        popup.title("About Us")
        
        # ตั้งค่า geometry ครั้งแรก
        popup.geometry(f"{self.winfo_width()}x{self.winfo_height()}")
        popup.configure(fg_color="#1f1f1f")
        
        about_img_path = os.path.join("assets", "about_us.png")
        
        if os.path.exists(about_img_path):
            # โหลดภาพครั้งแรกด้วยขนาดเริ่มต้นของ popup
            initial_width = self.winfo_width() # ใช้ขนาดจาก self เป็นค่าเริ่มต้น
            initial_height = self.winfo_height()
            
            img = Image.open(about_img_path).resize((initial_width, initial_height))
            photo = ctk.CTkImage(light_image=img, size=(initial_width, initial_height))
            
            # สร้าง Label
            label = ctk.CTkLabel(popup, image=photo, text="")
            label.image = photo
            label.pack(fill="both", expand=True)

    # ================= Contact Us =================
    from datetime import datetime, timedelta

    def open_contact(self):
        import db
        import os, shutil
        from tkinter import filedialog, messagebox

        popup = ctk.CTkToplevel(self)
        popup.title("📞 ติดต่อร้านค้า")
        popup.geometry("700x800")
        popup.configure(fg_color="#FFFFFF")

        # ==== Header ====
        header = ctk.CTkFrame(popup, fg_color="#1E88E5", height=70, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="📩 ติดต่อร้านค้า", font=("Segoe UI Black", 24),
                    text_color="white").pack(pady=15)

        # ==== Scrollable content ====
        form = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF", width=600, height=700)
        form.pack(padx=20, pady=20, fill="both", expand=True)

        name_var = ctk.StringVar()
        phone_var = ctk.StringVar()
        email_var = ctk.StringVar()
        message_var = ctk.StringVar()
        image_path = [None]

        # ====== ช่องกรอกข้อมูล ======
        def add_field(label, var, multiline=False):
            ctk.CTkLabel(form, text=label, anchor="w",
                        font=("Segoe UI", 13, "bold"), text_color="#111111").pack(fill="x", padx=20, pady=(10, 0))
            if multiline:
                entry = ctk.CTkTextbox(form, width=520, height=120,
                                    fg_color="#F1F3F4", text_color="#111111",
                                    border_color="#CCCCCC", corner_radius=10)
                entry.pack(padx=20, pady=(0, 10))
                return entry
            else:
                entry = ctk.CTkEntry(form, textvariable=var, width=520,
                                    fg_color="#F1F3F4", text_color="#111111", border_color="#CCCCCC")
                entry.pack(padx=20, pady=(0, 5))
                return entry

        name_entry = add_field("ชื่อ - นามสกุล", name_var)
        phone_entry = add_field("เบอร์โทร", phone_var)
        email_entry = add_field("อีเมล", email_var)
        message_box = add_field("ข้อความที่ต้องการแจ้ง", message_var, multiline=True)

        # ==== แสดงภาพตัวอย่างที่แนบ (Preview) ====
        preview_label = ctk.CTkLabel(form, text="ยังไม่มีภาพที่แนบ", text_color="#888")
        preview_label.pack(pady=(5, 20))

        # ==== แนบรูปภาพ ====
        def upload_image():
            file_path = filedialog.askopenfilename(
                title="แนบรูปภาพ", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
            )
            if file_path:
                os.makedirs("messages_images", exist_ok=True)
                ext = os.path.splitext(file_path)[1]
                new_path = os.path.join("messages_images", f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")
                shutil.copy(file_path, new_path)
                image_path[0] = new_path

                # แสดงภาพที่แนบใน preview_label
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(new_path)
                    img.thumbnail((300, 300))  # ปรับขนาดให้เหมาะสม
                    img_tk = ImageTk.PhotoImage(img)
                    preview_label.configure(image=img_tk, text="")
                    preview_label.image = img_tk  # เก็บ reference เพื่อไม่ให้ภาพหาย
                except Exception as e:
                    preview_label.configure(text=f"ไม่สามารถแสดงภาพได้: {e}", image="")
                    preview_label.image = None

                messagebox.showinfo("สำเร็จ", f"แนบรูปภาพแล้ว: {new_path}")

        ctk.CTkButton(form, text="📎 แนบรูปภาพ", fg_color="#1E88E5",
                    hover_color="#1565C0", text_color="white",
                    width=140, command=upload_image).pack(pady=(10, 20))

        # ==== ปุ่มส่งข้อความ ====
        def send_message():
            name = name_var.get().strip()
            phone = phone_var.get().strip()
            email = email_var.get().strip()
            msg_text = message_box.get("1.0", "end").strip()

            if not (name and phone and email and msg_text):
                messagebox.showwarning("แจ้งเตือน", "กรุณากรอกข้อมูลให้ครบทุกช่องก่อนส่งข้อความ")
                return

            try:
                db.add_message(name, phone, email, msg_text, image_path[0])
                messagebox.showinfo("สำเร็จ", "ส่งข้อความถึงร้านค้าเรียบร้อยแล้ว ✅")
                # ล้างข้อมูล
                message_box.delete("1.0", "end")
                image_path[0] = None
                preview_label.configure(text="ยังไม่มีภาพที่แนบ", image="")
                preview_label.image = None
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกข้อความได้\n{e}")

        ctk.CTkButton(form, text="📤 ส่งข้อความ", fg_color="#43A047", hover_color="#388E3C",
                    text_color="white", width=200, height=40,
                    command=send_message).pack(pady=10)

        # ==== ปุ่มดูประวัติข้อความ ====
        def show_history_popup():
            history_popup = ctk.CTkToplevel(popup)
            history_popup.title("📜 ประวัติการติดต่อร้านค้า")
            history_popup.geometry("650x600")
            history_popup.configure(fg_color="#FFFFFF")

            scroll_frame = ctk.CTkScrollableFrame(history_popup, fg_color="#FFFFFF", width=600, height=580)
            scroll_frame.pack(padx=10, pady=10, fill="both", expand=True)

            email_text = email_var.get().strip()
            if not email_text:
                ctk.CTkLabel(scroll_frame, text="กรุณากรอกอีเมลก่อนเพื่อดูประวัติ", text_color="#555").pack(pady=20)
                return

            messages = db.get_messages_by_email(email_text)
            if not messages:
                ctk.CTkLabel(scroll_frame, text="ยังไม่มีข้อความที่คุณเคยส่งถึงร้านค้า",
                            text_color="#555", font=("", 13)).pack(pady=20)
                return

            for msg_id, name, phone, email, msg_text, image, reply, created in messages:
                box = ctk.CTkFrame(scroll_frame, fg_color="#F5F5F5", corner_radius=10)
                box.pack(fill="x", padx=10, pady=8)

             
        # แก้ไขเวลาเพิ่ม 7 ชั่วโมง
                try:
                    # เพิ่มบรรทัดนี้: ตัดส่วน .microseconds (ถ้ามี) ทิ้งไปก่อน
                    created_base = created.split('.')[0] 
                    
                    dt = datetime.strptime(created_base, "%Y-%m-%d %H:%M:%S") # ใช้ created_base แทน created
                    dt += timedelta(hours=7)
                    created_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    # (แนะนำ) เพิ่ม print(e) ไว้ดู error ด้วยก็ได้ครับ
                    print(f"Error converting time: {e}, original value: {created}") 
                    created_str = created  # กรณีแปลงเวลาไม่ได้แสดงตามเดิม

                ctk.CTkLabel(box, text=f"📅 วันที่ส่ง: {created_str}", text_color="#555", font=("", 12)).pack(anchor="w", padx=10, pady=(5, 0))
                ctk.CTkLabel(box, text=f"📨 ข้อความของคุณ: {msg_text}", text_color="#000", wraplength=550, justify="left").pack(anchor="w", padx=10, pady=(3, 5))

                if image:
                    def open_image(path=image):
                        os.startfile(path)
                    ctk.CTkButton(box, text="📷 ดูรูปที่แนบ", fg_color="#FFA500", hover_color="#FFB733", command=open_image).pack(anchor="w", padx=10, pady=(2, 4))

                if reply:
                    ctk.CTkLabel(box, text=f"💬 คำตอบจากร้านค้า: {reply}", text_color="#1E88E5",
                                wraplength=550, justify="left").pack(anchor="w", padx=10, pady=(3, 8))
                else:
                    ctk.CTkLabel(box, text="⏳ รอคำตอบจากร้านค้า...", text_color="#888").pack(anchor="w", padx=10, pady=(3, 8))

        ctk.CTkButton(form, text="📜 ประวัติการติดต่อร้านค้า", fg_color="#1E88E5",
                    hover_color="#1565C0", text_color="white",
                    width=250, height=40, command=show_history_popup).pack(pady=20)





    # ================= Customer Info =================
    def open_customer_info(self):
        popup = ctk.CTkToplevel(self)
        popup.title("ข้อมูลลูกค้า")
        popup.geometry("550x700")
        popup.configure(fg_color="#F8F9FA")

        email = getattr(self.master.frames["login"], "current_user_email", None)
        info = db.get_customer_info(email)

        # ดึงข้อมูลลูกค้า
        fullname = ctk.StringVar(value=info[1] if info else "")
        phone = ctk.StringVar(value=info[2] if info else "")
        address = ctk.StringVar(value=info[3] if info else "")
        subdistrict = ctk.StringVar(value=info[4] if info else "")
        district = ctk.StringVar(value=info[5] if info else "")
        province = ctk.StringVar(value=info[6] if info else "")
        postalcode = ctk.StringVar(value=info[7] if info else "")

        # ==== Header ====
        header = ctk.CTkFrame(popup, fg_color="#1E88E5", height=70, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="ข้อมูลลูกค้า", font=("Segoe UI Black", 24),
                     text_color="white").pack(pady=15)

        # ==== Form ====
        form = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF", width=500, height=550)
        form.pack(padx=20, pady=15, fill="both", expand=True)

        # ==== รูปโปรไฟล์ลูกค้า ====
        profile_frame = ctk.CTkFrame(form, fg_color="#F1F3F4", corner_radius=15)
        profile_frame.pack(pady=15)

        img_label = ctk.CTkLabel(profile_frame, text="ยังไม่มีรูปภาพ", text_color="#666666")
        img_label.pack(pady=10)

        # ตรวจสอบว่ามีรูปอยู่ไหม
        os.makedirs("profiles", exist_ok=True)
        profile_path = os.path.join("profiles", f"{email}.png")
        if os.path.exists(profile_path):
            img = Image.open(profile_path).resize((150, 150))
            photo = ctk.CTkImage(light_image=img, size=(150, 150))
            img_label.configure(image=photo, text="")
            img_label.image = photo

        def upload_profile():
            file_path = filedialog.askopenfilename(title="เลือกรูปโปรไฟล์",
                            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if file_path:
                img = Image.open(file_path)
                img.thumbnail((300, 300))
                new_path = os.path.join("profiles", f"{email}.png")
                img.save(new_path)

                photo = ctk.CTkImage(light_image=img, size=(150, 150))
                img_label.configure(image=photo, text="")
                img_label.image = photo
                messagebox.showinfo("อัปโหลดสำเร็จ", "บันทึกรูปโปรไฟล์เรียบร้อยแล้ว ✅")

        ctk.CTkButton(profile_frame, text="📷 อัปโหลดรูปโปรไฟล์",
                      fg_color="#1E88E5", hover_color="#1565C0",
                      text_color="white", command=upload_profile).pack(pady=10)

        # ==== ช่องกรอกข้อมูล ====
        def add_field(label, var):
            lbl = ctk.CTkLabel(form, text=label, anchor="w",
                               font=("Segoe UI", 13, "bold"), text_color="#111111")
            lbl.pack(fill="x", padx=20, pady=(10, 0))
            entry = ctk.CTkEntry(form, textvariable=var, width=450,
                                 fg_color="#F1F3F4", text_color="#111111", border_color="#CCCCCC")
            entry.pack(padx=20, pady=(0, 5))

        add_field("ชื่อ - นามสกุล", fullname)
        add_field("เบอร์โทร", phone)
        add_field("ที่อยู่", address)
        add_field("ตำบล", subdistrict)
        add_field("อำเภอ", district)
        add_field("จังหวัด", province)
        add_field("รหัสไปรษณีย์", postalcode)

        # ==== ปุ่มบันทึก ====
        def save_info():
            db.save_customer_info(email, fullname.get(), phone.get(), address.get(),
                                  subdistrict.get(), district.get(), province.get(), postalcode.get())
            messagebox.showinfo("สำเร็จ", "บันทึกข้อมูลลูกค้าเรียบร้อยแล้ว! ✅")
            popup.destroy()

        ctk.CTkButton(popup, text="💾 บันทึกข้อมูล",
                      fg_color="#1E88E5", hover_color="#1565C0",
                      text_color="white", height=40, width=200,
                      corner_radius=20, command=save_info).pack(pady=20)



# ================= สร้าง PDF ใบเสร็จ (สไตล์เต็มรายละเอียด) =================
    def create_receipt_pdf(self, customer_info, cart_items, subtotal, vat_amount, total_paid, order_id, created_at):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from datetime import datetime, timedelta
        import os, webbrowser

        # --- ฟอนต์ไทย ---
        font_path = os.path.join("assets", "THSarabunNew.ttf")
        pdfmetrics.registerFont(TTFont("THSarabunNew", font_path))

        os.makedirs("receipts", exist_ok=True)
        pdf_filename = os.path.join(
            "receipts", f"receipt_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        doc = SimpleDocTemplate(pdf_filename, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Thai", fontName="THSarabunNew", fontSize=16, leading=20))
        styles.add(ParagraphStyle(name="ThaiCenter", fontName="THSarabunNew", fontSize=16, alignment=1))
        styles.add(ParagraphStyle(name="ThaiTitle", fontName="THSarabunNew", fontSize=22, alignment=1, spaceAfter=10, leading=26))

        elements = []

        # ========== โลโก้ร้าน ==========
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=80, height=80)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(1, 4))

        # ========== ชื่อร้านและหัวกระดาษ ==========
        shop_info = (
            "<para leftindent=20>"
            "<b>ใบเสร็จรับเงิน</b><br/>"
            "GYMLION STORE<br/>"
            "ที่อยู่: เลขที่ 123 หมู่ 16 ถนนมิตรภาพ ตำบลในเมือง อำเภอเมืองขอนแก่น<br/>"
            "จังหวัดขอนแก่น 40000<br/>"
            "เบอร์ติดต่อ: 061-032-3319<br/>"
            "อีเมล: prungprach.s@kkumail.com"
            "</para>"
        )
        elements.append(Paragraph(shop_info, styles["Thai"]))
        elements.append(Spacer(1, 10))

        # ========== ข้อมูลลูกค้า ==========
        thai_time = datetime.utcnow() + timedelta(hours=7)
        created_th = thai_time.strftime("%Y-%m-%d %H:%M:%S")

        if customer_info:
            fullname = customer_info[1] or "-"
            phone = customer_info[2] or "-"
            address_full = f"{customer_info[3]} หมู่ {customer_info[4]} ต.{customer_info[5]} อ.{customer_info[6]} จ.{customer_info[7]}"
        else:
            fullname, phone, address_full = "-", "-", "-"

        cust_table_data = [[Paragraph(
            f"<b>หมายเลขคำสั่งซื้อ:</b> {order_id}<br/>"
            f"<b>วันที่สั่งซื้อ:</b> {created_th}<br/><br/>"
            f"<b>ชื่อลูกค้า:</b> {fullname}<br/>"
            f"<b>อีเมล:</b> {customer_info[0] if customer_info else '-'}<br/>"
            f"<b>เบอร์โทร:</b> {phone}<br/>"
            f"<b>ที่อยู่:</b> {address_full}",
            styles["Thai"]
        )]]
        cust_table = Table(cust_table_data, colWidths=[480])
        cust_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(cust_table)
        elements.append(Spacer(1, 15))

        # ========== ตารางสินค้า ==========
        data = [["ลำดับ", "รายการสินค้า", "จำนวน", "ราคาต่อชิ้น", "รวม (บาท)"]]
        for i, (pid, item) in enumerate(cart_items.items(), start=1):
            total_item = item["price"] * item["qty"]
            data.append([
                str(i),
                item["name"],
                str(item["qty"]),
                f"{item['price']:,.0f} บาท",
                f"{total_item:,.0f} บาท",
            ])

        table = Table(data, colWidths=[40, 220, 70, 100, 100])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'THSarabunNew'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # ========== ตารางสรุปยอด (ปรับให้เข้ากับตารางสินค้า) ==========
        # ========== ตารางสรุปยอด (ปรับแนวให้อยู่ระนาบเดียวกับ "ลำดับ") ==========
        summary_data = [
            ["ยอดรวมสินค้า", f"{subtotal:,.0f} บาท"],
            ["ภาษีมูลค่าเพิ่ม 7% (VAT)", f"{vat_amount:,.0f} บาท"],
            ["ยอดที่ต้องชำระทั้งหมด", f"{total_paid:,.0f} บาท"]
        ]

        # ✅ ใช้ความกว้างรวมเท่ากับตารางสินค้า
        summary_table = Table(summary_data, colWidths=[40 + 220 + 70 + 100, 100])  

        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'THSarabunNew'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            # ✅ ขยับข้อความให้อยู่แนวเดียวกับคอลัมน์ "ลำดับ"
            ('LEFTPADDING', (0, 0), (0, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 15))

        # ========== วันที่ออกใบเสร็จ ==========
        elements.append(Paragraph(f"วันที่ออกใบเสร็จ: {created_th}", styles["Thai"]))

        # ========== สร้าง PDF ==========
        doc.build(elements)
        webbrowser.open(os.path.abspath(pdf_filename))



         # ================= My Orders =================
    def open_orders(self):
        import json, glob, os
        from datetime import datetime

        popup = ctk.CTkToplevel(self)
        popup.title("คำสั่งซื้อของฉัน")
        popup.geometry("900x650")
        popup.configure(fg_color="#F8F9FA")

        # ===== Header =====
        header = ctk.CTkFrame(popup, fg_color="#1E88E5", height=70, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="📦 คำสั่งซื้อของฉัน",
                    font=("Segoe UI Black", 24),
                    text_color="white").pack(pady=15)

        email = getattr(self.master.frames["login"], "current_user_email", None)
        orders = db.get_orders_by_email(email) if hasattr(db, "get_orders_by_email") else []

        if not orders:
            ctk.CTkLabel(
                popup,
                text="ไม่พบคำสั่งซื้อ",
                font=("Segoe UI", 18, "bold"),
                text_color="#666666"
            ).pack(pady=40)
            return

        # ===== Scrollable Area =====
        frame = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF", width=850, height=500, corner_radius=20)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        for order in orders:
            oid, email, name, phone, address, items, total, slip_path, status, created_at = order
            box = ctk.CTkFrame(frame, fg_color="#FFFFFF", corner_radius=15, border_color="#E0E0E0", border_width=1)
            box.pack(fill="x", padx=10, pady=10)

            # Hover effect
            def on_enter(e, b=box): b.configure(border_color="#1E88E5")
            def on_leave(e, b=box): b.configure(border_color="#E0E0E0")
            box.bind("<Enter>", on_enter)
            box.bind("<Leave>", on_leave)

            dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            thai_time_str = dt.strftime("%d/%m/%Y %H:%M:%S")

            # ===== Title =====
            ctk.CTkLabel(box, text=f"คำสั่งซื้อ #{oid}",
                        font=("Segoe UI", 16, "bold"), text_color="#111111").pack(anchor="w", padx=15, pady=(8, 0))
            ctk.CTkLabel(box, text=f"วันที่สั่งซื้อ: {thai_time_str}",
                        font=("Segoe UI", 12), text_color="#555555").pack(anchor="w", padx=15, pady=(0, 3))

            # ===== Status =====
            ctk.CTkLabel(box, text=f"สถานะ: {status}",
                        font=("Segoe UI", 13, "bold"), text_color="#1E88E5").pack(anchor="w", padx=15, pady=(2, 5))

            # ===== Items =====
            try:
                items_list = json.loads(items)
                if isinstance(items_list, list):
                    items_text = "\n".join([
                    f"• {it.get('name', '?')} x{it.get('qty', 0)} = {float(it.get('price', 0)) * int(it.get('qty', 0)):,.2f} ฿"
                    for it in items_list
                ])
                else:
                    items_text = str(items)
            except:
                items_text = str(items)

            ctk.CTkLabel(
                box,
                text=f"รายการสินค้า:\n{items_text}",
                font=("Segoe UI", 12),
                justify="left",
                text_color="#444444",
                wraplength=700
            ).pack(anchor="w", padx=20, pady=(0, 5))

            # ===== VAT Calculation =====
            VAT_RATE = 0.07
            subtotal = round(total / (1 + VAT_RATE), 2)
            vat_amount = round(total - subtotal, 2)

            # ===== Totals =====
            total_frame = ctk.CTkFrame(box, fg_color="#FAFAFA", corner_radius=10)
            total_frame.pack(fill="x", padx=15, pady=(5, 10))

            ctk.CTkLabel(total_frame, text=f"ยอดรวมค่าสินค้า (Subtotal): {subtotal:,.2f} ฿",
                        font=("Segoe UI", 13), text_color="#111111").pack(anchor="e", padx=15, pady=(5, 0))
            ctk.CTkLabel(total_frame, text=f"ภาษีมูลค่าเพิ่ม 7% (VAT): {vat_amount:,.2f} ฿",
                        font=("Segoe UI", 13), text_color="#111111").pack(anchor="e", padx=15, pady=2)
            ctk.CTkLabel(total_frame, text=f"ยอดสุทธิที่ชำระ (Total Paid): {total:,.2f} ฿",
                        font=("Segoe UI Black", 14), text_color="#1E88E5").pack(anchor="e", padx=15, pady=(2, 8))

            # ===== Buttons (Slip + Receipt) =====
            btn_frame = ctk.CTkFrame(box, fg_color="transparent")
            btn_frame.pack(anchor="e", padx=15, pady=(5, 10))

            if slip_path and os.path.exists(slip_path):
                ctk.CTkButton(
                    btn_frame, text="เปิดสลิปที่ลูกค้าอัปโหลด 📎",
                    fg_color="#1E88E5", hover_color="#1565C0",
                    text_color="white", width=200, height=36,
                    corner_radius=15,
                    command=lambda p=slip_path: os.startfile(p)
                ).pack(side="left", padx=5)

            receipt_files = glob.glob(f"receipts/receipt_{oid}_*.pdf")
            receipt_files.sort()
            for rpath in receipt_files:
                if os.path.exists(rpath):
                    ctk.CTkButton(
                        btn_frame,
                        text="เปิดใบเสร็จร้านค้า (PDF) 🧾",
                        fg_color="#00AAFF", hover_color="#0091EA",
                        text_color="white", width=200, height=36,
                        corner_radius=15,
                        command=lambda p=rpath: os.startfile(p)
                    ).pack(side="left", padx=5)

    def logout(self):
        """ออกจากระบบและกลับไปหน้า Login"""
        from tkinter import messagebox
        if messagebox.askyesno("ออกจากระบบ", "คุณต้องการออกจากระบบหรือไม่?"):
            self.master.show_frame("login")


