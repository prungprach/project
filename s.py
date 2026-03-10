import customtkinter as ctk
from PIL import Image
import os
import db
from tkinter import filedialog, messagebox
from shutil import copyfile
import re

# --- ฟังก์ชันช่วยแปลงตัวเลข --- แปลง เลขไทย (๑๒๓) → เลขอารบิก (123)
def _to_arabic_digits(s: str) -> str:
    """แปลงเลขไทย -> เลขอารบิก (ถ้ามี)"""
    thai_digits = "๐๑๒๓๔๕๖๗๘๙"
    arabic_digits = "0123456789"
    trans = str.maketrans(thai_digits, arabic_digits)
    return s.translate(trans)

#แปลงข้อความที่กรอกเป็น ตัวเลขทศนิยม (float)
def parse_float(s: str):
    """พยายามแปลงสตริงเป็น float อย่างยืดหยุ่น"""
    if s is None:
        raise ValueError("Empty")
    s = str(s).strip()
    s = _to_arabic_digits(s)
    if s == "":
        raise ValueError("Empty")
    if ',' in s and '.' in s:
        s = s.replace(',', '')
    else:
        if s.count(',') > 1:
            s = s.replace(',', '')
        elif s.count(',') == 1 and '.' not in s:
            s = s.replace(',', '.')
    s = re.sub(r'[^\d\.\-]', '', s)
    if s in ("", ".", "-"):
        raise ValueError("Invalid")
    return float(s)

#แปลงข้อความที่กรอกเป็น จำนวนเต็ม (int)
def parse_int(s: str):
    """พยายามแปลงสตริงเป็น int อย่างยืดหยุ่น"""
    if s is None:
        raise ValueError("Empty")
    s = str(s).strip()
    s = _to_arabic_digits(s)
    if s == "":
        raise ValueError("Empty")
    s2 = s.replace(',', '')
    s2 = re.sub(r'[^\d\-]', '', s2)
    if s2 == "" or s2 == "-":
        raise ValueError("Invalid")
    try:
        return int(s2)
    except ValueError:
        try:
            f = parse_float(s)
            if abs(f - int(f)) < 1e-9:
                return int(f)
            else:
                raise ValueError("Not integer")
        except Exception as e:
            raise ValueError("Invalid") from e


# ===================== CLASS ===================== เป็นหน้าจอหลักของแอดมินหลังจากเข้าสู่ระบบ
class AdminDashboard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.master = master

        screen_w = master.winfo_screenwidth()
        screen_h = master.winfo_screenheight()

        # --- Background ---
        try:
            img_path = os.path.join("assets", "admin.png")
            bg_image = Image.open(img_path).resize((screen_w, screen_h))
            self.bg_photo = ctk.CTkImage(light_image=bg_image, size=(screen_w, screen_h))
            bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except:
            self.configure(fg_color="#E6F5EB")  # ✅ สีพื้นสำรองเป็นขาวเขียวอ่อน

        # --- Top Frame: Title + Buttons ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", pady=10)

        title = ctk.CTkLabel(top_frame, text="Admin Dashboard", font=("", 28, "bold"), text_color="#006633")  # ✅ สี Title เขียวเข้ม
        title.pack(side="left", padx=20)

        # ✅ สไตล์ปุ่มธีมเขียว
        btn_style = dict(
            fg_color="#66CC99",       # สีเขียวอ่อน
            hover_color="#33CC66",    # สีเขียวเมื่อ hover
            text_color="white",
            corner_radius=10,
            height=32
        )

        order_btn = ctk.CTkButton(top_frame, text="คำสั่งซื้อ", command=self.show_orders, **btn_style)
        order_btn.pack(side="right", padx=10)

        summary_btn = ctk.CTkButton(top_frame, text="สรุปยอดขาย", command=self.show_sales_summary, **btn_style)
        summary_btn.pack(side="right", padx=10)

        inbox_btn = ctk.CTkButton(top_frame, text="กล่องข้อความ", command=self.show_inbox, **btn_style)
        inbox_btn.pack(side="right", padx=10)

        add_btn = ctk.CTkButton(top_frame, text="เพิ่มสินค้า", command=self.add_product_popup, **btn_style)
        add_btn.pack(side="right", padx=10)

        logout_btn = ctk.CTkButton(top_frame, text="Logout", command=lambda: master.show_frame("login"), **btn_style)
        logout_btn.pack(side="right", padx=10)

        # --- Product Frame ---
        self.product_frame = ctk.CTkScrollableFrame(
            self, 
            width=screen_w-40, 
            height=int(screen_h*0.8), 
            fg_color="transparent"
        )
        self.product_frame.pack(padx=20, pady=5, fill="both", expand=True)

        self.load_products()

    # ---------------- Load Products ---------------- ดึงข้อมูลสินค้าจากฐานข้อมูลด้วย db.get_products()
    def load_products(self):
        for widget in self.product_frame.winfo_children():
            widget.destroy()

        cat_id = getattr(self, "current_category_id", 0)  # 0 = หมวดทั้งหมด
        products = db.get_products_by_category(cat_id)

    # ... สร้างกรอบสินค้าเหมือนเดิม ...

        products = db.get_products()
        cols = 4  
        rows = (len(products) + cols - 1) // cols
        index = 0

        for r in range(rows):
            self.product_frame.grid_rowconfigure(r, weight=1)
            for c in range(cols):
                self.product_frame.grid_columnconfigure(c, weight=1)
                if index >= len(products):
                    break
                p = products[index]

                # ✅ กรอบสินค้า (ธีมขาวเขียว)
                frame = ctk.CTkFrame(
                    self.product_frame, 
                    fg_color="#E6F5EB",      # ขาวเขียวอ่อน
                    corner_radius=18,
                    border_width=1,
                    border_color="#33CC66"   # ขอบเขียวสด
                )
                frame.grid(row=r, column=c, padx=18, pady=18, sticky="nsew")

                # ===== แสดงรูปสินค้า =====
                img_path = os.path.join("assets", f"{p[1]}.png")
                if os.path.exists(img_path):
                    img = Image.open(img_path).resize((220, 220), Image.Resampling.LANCZOS)
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(220, 220))
                    img_label = ctk.CTkLabel(frame, image=photo, text="")
                    img_label.image = photo
                    img_label.pack(pady=(10, 5))

                # ===== ข้อความสินค้า =====
                ctk.CTkLabel(frame, text=p[1], font=("", 17, "bold"), text_color="#006633").pack(pady=(0, 2))
                ctk.CTkLabel(frame, text=f"{p[2]:,.2f} ฿ / {p[4]}", text_color="#009966", font=("", 14, "bold")).pack()
                ctk.CTkLabel(frame, text=f"Stock: {p[3]}", text_color="#666666", font=("", 12)).pack(pady=(2, 5))
                ctk.CTkLabel(frame, text=p[5] if len(p)>5 else "", text_color="#333333", wraplength=200, font=("", 12)).pack(pady=(0, 10))

                # ✅ แสดงหมวดหมู่
                cat_name = db.get_product_category(p[0])
                if cat_name:
                    ctk.CTkLabel(frame, text=f"หมวดหมู่: {cat_name}", text_color="#006633", font=("", 12, "bold")).pack(pady=(0,5))


                # ===== ปุ่มแก้ไข / ลบ =====
                btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
                btn_frame.pack(pady=(0, 10))

                ctk.CTkButton(
                    btn_frame, text="แก้ไข", width=70, height=28,
                    fg_color="#33CC66",
                    hover_color="#00CC44",
                    command=lambda pid=p[0]: self.edit_product_popup(pid)
                ).pack(side="left", padx=5)

                ctk.CTkButton(
                    btn_frame, text="ลบ", width=70, height=28,
                    fg_color="#c0392b", hover_color="#e74c3c",
                    command=lambda pid=p[0]: self.delete_product(pid)
                ).pack(side="right", padx=5)

                index += 1

    # ---------------- Add Product Popup ---------------- เปิดหน้าต่างเล็กให้แอดมินกรอกข้อมูลสินค้าใหม่
    def add_product_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("เพิ่มสินค้า")
        popup.geometry("420x400")
        popup.configure(fg_color="#E6F5EB")  # ✅ พื้นหลังขาวเขียวอ่อน

        entry_style = dict(
            fg_color="white",        # พื้นขาว
            text_color="#006633",    # ตัวอักษรเขียวเข้ม
            placeholder_text_color="#99CC99", # Placeholder สีเขียวอ่อน
            border_width=1,
            border_color="#33CC66",
            corner_radius=8
        )

        name_entry = ctk.CTkEntry(popup, placeholder_text="ชื่อสินค้า", **entry_style)
        name_entry.pack(pady=8, padx=20, fill="x")
        price_entry = ctk.CTkEntry(popup, placeholder_text="ราคา (เช่น 1200 หรือ 1,200.00)", **entry_style)
        price_entry.pack(pady=8, padx=20, fill="x")
        stock_entry = ctk.CTkEntry(popup, placeholder_text="จำนวน (จำนวนเต็ม)", **entry_style)
        stock_entry.pack(pady=8, padx=20, fill="x")
        unit_entry = ctk.CTkEntry(popup, placeholder_text="หน่วย (เช่น กรัม, เม็ด)", **entry_style)
        unit_entry.pack(pady=8, padx=20, fill="x")
        desc_entry = ctk.CTkEntry(popup, placeholder_text="คำอธิบายสินค้า", **entry_style)
        desc_entry.pack(pady=8, padx=20, fill="x")

        img_path_var = ctk.StringVar()

        def choose_image():
            path = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png"), ("All Images", "*.*")])
            if path:
                img_path_var.set(path)

        img_btn = ctk.CTkButton(
            popup, text="เลือกรูปภาพ (.png)", 
            fg_color="#33CC66", hover_color="#00CC44", text_color="white",
            corner_radius=10,
            command=choose_image
        )
        img_btn.pack(pady=6)

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "กรุณากรอกชื่อสินค้า")
                return
            try:
                price = parse_float(price_entry.get())
            except Exception:
                messagebox.showerror("Error", "กรุณากรอกราคาเป็นตัวเลขที่ถูกต้อง")
                return
            try:
                stock = parse_int(stock_entry.get())
            except Exception:
                messagebox.showerror("Error", "กรุณากรอกจำนวนเป็นจำนวนเต็ม")
                return

            unit = unit_entry.get().strip() or "g"
            description = desc_entry.get().strip()

            ok = db.add_product(name, price, stock, unit, description)
            if not ok:
                messagebox.showerror("Error", "เพิ่มสินค้าไม่สำเร็จ — อาจมีชื่อสินค้าซ้ำ")
                return

            if img_path_var.get():
                dest = os.path.join("assets", f"{name}.png")
                try:
                    copyfile(img_path_var.get(), dest)
                except Exception as e:
                    messagebox.showwarning("Warning", f"บันทึกรูปไม่สำเร็จ: {e}")

            popup.destroy()
            self.load_products()

        save_btn = ctk.CTkButton(
            popup, text="บันทึก",
            fg_color="#33CC66", hover_color="#00CC44", text_color="white",
            corner_radius=10,
            command=save
        )
        save_btn.pack(pady=10)

    # ---------------- Edit Product Popup ---------------- เปิดหน้าต่างแก้ไขข้อมูลสินค้าที่เลือก
    def edit_product_popup(self, pid):
        product = next((p for p in db.get_products() if p[0]==pid), None)
        if not product:
            messagebox.showerror("Error", "ไม่พบสินค้านี้")
            return

        popup = ctk.CTkToplevel(self)
        popup.title("แก้ไขสินค้า")
        popup.geometry("420x500")
        popup.configure(fg_color="#E6F5EB")  # ✅ พื้นหลังขาวเขียวอ่อน

        entry_style = dict(
            fg_color="white",
            text_color="#006633",
            placeholder_text_color="#99CC99",
            border_width=1,
            border_color="#33CC66",
            corner_radius=8
        )

        name_entry = ctk.CTkEntry(popup, **entry_style)
        name_entry.insert(0, product[1])
        name_entry.pack(pady=8, padx=20, fill="x")

        price_entry = ctk.CTkEntry(popup, **entry_style)
        price_entry.insert(0, str(product[2]))
        price_entry.pack(pady=8, padx=20, fill="x")

        stock_entry = ctk.CTkEntry(popup, **entry_style)
        stock_entry.insert(0, str(product[3]))
        stock_entry.pack(pady=8, padx=20, fill="x")

        unit_entry = ctk.CTkEntry(popup, **entry_style)
        unit_entry.insert(0, product[4])
        unit_entry.pack(pady=8, padx=20, fill="x")

        desc_entry = ctk.CTkEntry(popup, **entry_style)
        desc_entry.insert(0, product[5] if len(product) > 5 else "")
        desc_entry.pack(pady=8, padx=20, fill="x")

        # --- รูปภาพเดิม ---
        current_img_path = os.path.join("assets", f"{product[1]}.png")
        if os.path.exists(current_img_path):
            try:
                img_preview = Image.open(current_img_path).resize((160, 160))
                img_photo = ctk.CTkImage(light_image=img_preview, dark_image=img_preview, size=(160, 160))
                img_label = ctk.CTkLabel(popup, image=img_photo, text="")
                img_label.image = img_photo
                img_label.pack(pady=5)
            except Exception:
                ctk.CTkLabel(popup, text="(ไม่สามารถแสดงรูปได้)", text_color="#666666").pack()

        # --- ปุ่มเลือกรูปใหม่ ---
        img_path_var = ctk.StringVar()

        def choose_image():
            path = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png"), ("All Images", "*.*")])
            if path:
                img_path_var.set(path)
                ctk.CTkLabel(popup, text=f"เลือกรูปใหม่แล้ว: {os.path.basename(path)}",
                            text_color="#009966").pack(pady=3)

        img_btn = ctk.CTkButton(
            popup, text="เลือกรูปใหม่ (.png)",
            fg_color="#33CC66", hover_color="#00CC44", text_color="white",
            corner_radius=10,
            command=choose_image
        )
        img_btn.pack(pady=6)

        # --- เลือกหมวดหมู่ ---
        ctk.CTkLabel(popup, text="เลือกหมวดหมู่:", text_color="#006633", font=("", 14, "bold")).pack(pady=(10, 0))
        categories = db.get_all_categories()
        category_names = [c[1] for c in categories]

        selected_category = ctk.StringVar(value=db.get_product_category(pid) or category_names[0])
        category_menu = ctk.CTkOptionMenu(popup, values=category_names, variable=selected_category,
                                        fg_color="white", text_color="#006633", button_color="#33CC66")
        category_menu.pack(pady=5)

        category_label = ctk.CTkLabel(popup, text=f"หมวดหมู่: {selected_category.get()}", text_color="#006633", font=("", 12, "bold"))
        category_label.pack(pady=5)

        def on_category_change(new_value):
            category_label.configure(text=f"หมวดหมู่: {new_value}")

        selected_category.trace_add("write", lambda *args: on_category_change(selected_category.get()))


        # --- ปุ่มบันทึก ---
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "กรุณากรอกชื่อสินค้า")
                return
            try:
                price = parse_float(price_entry.get())
            except Exception:
                messagebox.showerror("Error", "กรุณากรอกราคาเป็นตัวเลขที่ถูกต้อง")
                return
            try:
                stock = parse_int(stock_entry.get())
            except Exception:
                messagebox.showerror("Error", "กรุณากรอกจำนวนเป็นจำนวนเต็ม")
                return

            unit = unit_entry.get().strip() or "g"
            description = desc_entry.get().strip()

            try:
                db.update_product(pid, name, price, stock, unit, description)
            except Exception as e:
                messagebox.showerror("Error", f"บันทึกการแก้ไขล้มเหลว: {e}")
                return

            # ✅ อัปเดตหมวดหมู่ที่เลือกไว้
            chosen_cat_name = selected_category.get()
            cat_id = next((c[0] for c in categories if c[1] == chosen_cat_name), None)
            if cat_id:
                db.assign_product_to_category(pid, cat_id)

            # ✅ ถ้าเลือกรูปใหม่ ให้คัดลอกมาทับไฟล์เดิม
            if img_path_var.get():
                dest = os.path.join("assets", f"{name}.png")
                try:
                    copyfile(img_path_var.get(), dest)
                except Exception as e:
                    messagebox.showwarning("Warning", f"บันทึกรูปไม่สำเร็จ: {e}")

            popup.destroy()
            self.load_products()


        save_btn = ctk.CTkButton(
            popup, text="บันทึก",
            fg_color="#33CC66", hover_color="#00CC44", text_color="white",
            corner_radius=10,
            command=save
        )
        save_btn.pack(pady=10)

        # ---------------- Delete Product ---------------- แสดงหน้าต่างถามยืนยันก่อนลบ
    def delete_product(self, pid):
        confirm = messagebox.askyesno("ยืนยัน", "ต้องการลบสินค้านี้หรือไม่?")
        if confirm:
            db.delete_product(pid)
            self.load_products()


    # ---------------- Show Orders  ---------------- เปิดหน้าต่างใหม่แสดงรายการคำสั่งซื้อทั้งหมดจากลูกค้า
    def show_orders(self):
        popup = ctk.CTkToplevel(self)
        popup.title("รายการคำสั่งซื้อทั้งหมด")
        popup.geometry("900x600")
        popup.configure(fg_color="#E6F5EB")  # พื้นหลังขาวเขียวอ่อน

        frame = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF", width=880, height=550)  # ScrollFrame พื้นขาว
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        orders = db.get_all_orders()
        if not orders:
            ctk.CTkLabel(frame, text="ยังไม่มีคำสั่งซื้อ", text_color="#006633", font=("", 16)).pack(pady=20)
            return

        for order in orders:
            oid, email, name, phone, address, items, total, slip, status, created = order

            box = ctk.CTkFrame(frame, fg_color="#E6F5EB", corner_radius=12, border_width=1, border_color="#33CC66")
            box.pack(fill="x", padx=8, pady=8)

            # หัวข้อ
            ctk.CTkLabel(box, text=f"คำสั่งซื้อ #{oid} - {name}", font=("", 18, "bold"), text_color="#006633").pack(anchor="w", padx=10, pady=(8,0))
            ctk.CTkLabel(box, text=f"อีเมล: {email} | เบอร์: {phone}", text_color="#009966").pack(anchor="w", padx=10)
            ctk.CTkLabel(box, text=f"ที่อยู่: {address}", text_color="#006633", wraplength=850).pack(anchor="w", padx=10)

            # ✅ แปลง JSON ของสินค้าให้อ่านง่าย
            import json
            try:
                items_list = json.loads(items)
                if isinstance(items_list, list):
                    items_text = "\n".join(
                        [f"• {it.get('name', 'ไม่ทราบชื่อสินค้า')} x{it.get('qty',0)} = {float(it.get('price',0)) * int(it.get('qty',0)):,.2f} บาท"
                        for it in items_list]
                    )
                else:
                    items_text = str(items)
            except Exception:
                items_text = str(items)

            ctk.CTkLabel(
                box,
                text=f"รายการสินค้า:\n{items_text}",
                text_color="#004d33",  # เขียวเข้ม
                wraplength=850,
                justify="left"
            ).pack(anchor="w", padx=10, pady=(2,0))

            # ✅ แสดงยอดรวมแบบแยกรายละเอียด
            subtotal = total / 1.07
            vat = total - subtotal

            ctk.CTkLabel(box, text=f"ยอดรวมค่าสินค้า (Subtotal): {subtotal:,.2f} บาท",
                        text_color="#006633", font=("",13)).pack(anchor="w", padx=10, pady=(2,0))
            ctk.CTkLabel(box, text=f"ภาษีมูลค่าเพิ่ม 7% (VAT): {vat:,.2f} บาท",
                        text_color="#009966", font=("",13)).pack(anchor="w", padx=10, pady=(0,0))
            ctk.CTkLabel(box, text=f"ยอดสุทธิที่ชำระ (Total Paid): {total:,.2f} บาท",
                        text_color="#33CC66", font=("",14,"bold")).pack(anchor="w", padx=10, pady=(0,4))
            ctk.CTkLabel(box, text=f"สถานะปัจจุบัน: {status}", text_color="#006633").pack(anchor="w", padx=10, pady=(2,4))

            # ===== ปุ่ม =====
            btn_frame = ctk.CTkFrame(box, fg_color="transparent")
            btn_frame.pack(anchor="w", padx=10, pady=5)

            # ปุ่มเปิดสลิป
            if slip and os.path.exists(slip):
                ctk.CTkButton(btn_frame, text="เปิดสลิป", width=90,
                            fg_color="#33CC66", hover_color="#00CC44", text_color="white",
                            command=lambda p=slip: os.startfile(p)).pack(side="left", padx=5)

            # ปุ่มเปลี่ยนสถานะ
            def change_status(order_id=oid):
                status_popup = ctk.CTkToplevel(popup)
                status_popup.title("เปลี่ยนสถานะคำสั่งซื้อ")
                status_popup.geometry("300x250")
                status_popup.configure(fg_color="#E6F5EB")  # พื้นหลังขาวเขียวอ่อน

                options = ["รอตรวจสอบ", "ชำระเงินแล้ว"]
                status_var = ctk.StringVar(value=status)

                for opt in options:
                    ctk.CTkRadioButton(status_popup, text=opt, variable=status_var, value=opt,
                                    text_color="#006633", fg_color="#FFFFFF", hover_color="#CCFFDD").pack(anchor="w", padx=20, pady=6)

                save_btn = ctk.CTkButton(status_popup, text="บันทึก",
                                        fg_color="#33CC66", hover_color="#00CC44", text_color="white",
                                        command=lambda: self._save_order_status(order_id, status_var.get(), status_popup, popup))
                save_btn.pack(pady=10)

            ctk.CTkButton(btn_frame, text="เปลี่ยนสถานะ", width=100,
                        fg_color="#33CC66", hover_color="#00CC44", text_color="white",
                        command=change_status).pack(side="left", padx=5)

            # ปุ่มลบคำสั่งซื้อ
            ctk.CTkButton(btn_frame, text="ลบคำสั่งซื้อ", width=100,
                        fg_color="#c0392b", hover_color="#e74c3c", text_color="white",
                        command=lambda oid=oid: self.delete_order(oid)).pack(side="left", padx=5)

    # ---------------- ฟังก์ชันช่วยบันทึกสถานะ ---------------- เปลี่ยนสถานะคำสั่งซื้อ
    def _save_order_status(self, order_id, new_status, status_popup, parent_popup):
        db.update_order_status(order_id, new_status)
        messagebox.showinfo("สำเร็จ", "อัปเดตสถานะเรียบร้อยแล้ว")
        status_popup.destroy()
        parent_popup.destroy()
        self.show_orders()

    # ---------------- Show Inbox  ---------------- เปิดหน้าต่างแสดงข้อความที่ลูกค้าส่งเข้ามา (feedback หรือสอบถาม)
    def show_inbox(self):
        import os, datetime, webbrowser
        from tkinter import messagebox

        popup = ctk.CTkToplevel(self)
        popup.title("กล่องข้อความลูกค้า")
        popup.geometry("950x650")
        popup.configure(fg_color="#E6F5EB")  # พื้นหลังขาวเขียวอ่อน

        frame = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF", width=930, height=600)  # ScrollFrame ขาว
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        messages = db.get_all_messages()
        if not messages:
            ctk.CTkLabel(frame, text="ยังไม่มีข้อความจากลูกค้า", text_color="#006633", font=("", 16)).pack(pady=20)
            return

        # ตั้ง timezone เป็นประเทศไทย
        import pytz
        tz = pytz.timezone("Asia/Bangkok")

        for mid, sender, phone, email, message, image, reply, created in messages:
            # แปลงเวลาให้ตรงกับไทย
            try:
                utc_dt = datetime.datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                local_time = utc_dt.replace(tzinfo=pytz.utc).astimezone(tz)
                created_local = local_time.strftime("%d/%m/%Y %H:%M")
            except:
                created_local = created

            box = ctk.CTkFrame(frame, fg_color="#E6F5EB", corner_radius=12, border_width=1, border_color="#33CC66")
            box.pack(fill="x", padx=8, pady=8)

            # ข้อมูลผู้ส่ง
            ctk.CTkLabel(box, text=f"👤 ชื่อ: {sender}", text_color="#006633", font=("", 15, "bold")).pack(anchor="w", padx=10, pady=(5,0))
            ctk.CTkLabel(box, text=f"📞 เบอร์โทร: {phone}", text_color="#009966", font=("", 13)).pack(anchor="w", padx=10)
            ctk.CTkLabel(box, text=f"📧 อีเมล: {email}", text_color="#009966", font=("", 13)).pack(anchor="w", padx=10)
            ctk.CTkLabel(box, text=f"🕒 วันที่ส่ง: {created_local}", text_color="#006633", font=("", 12)).pack(anchor="w", padx=10, pady=(0,4))
            ctk.CTkLabel(box, text=f"💬 ข้อความ: {message}", text_color="#004d33", wraplength=850, justify="left").pack(anchor="w", padx=10, pady=(2,4))

            # ปุ่มเปิดภาพแนบ (ถ้ามี)
            if image and os.path.exists(image):
                def open_image(img_path=image):
                    webbrowser.open(img_path)
                ctk.CTkButton(box, text="🖼️ เปิดภาพแนบ",
                            fg_color="#33CC66", hover_color="#00CC44", text_color="white",
                            command=open_image).pack(anchor="w", padx=10, pady=(4,6))

            # แสดงข้อความตอบกลับ
            if reply:
                ctk.CTkLabel(box, text=f"📤 คำตอบจากแอดมิน: {reply}",
                            text_color="#006633", wraplength=850, justify="left").pack(anchor="w", padx=10, pady=(2,4))
            else:
                # ปุ่มตอบกลับ
                def open_reply(mid=mid):
                    reply_popup = ctk.CTkToplevel(popup)
                    reply_popup.title("ตอบกลับลูกค้า")
                    reply_popup.geometry("400x300")
                    reply_popup.configure(fg_color="#E6F5EB")  # พื้นหลังขาวเขียวอ่อน

                    reply_entry = ctk.CTkTextbox(reply_popup, width=360, height=150, fg_color="white", text_color="#006633", border_width=1, border_color="#33CC66", corner_radius=8)
                    reply_entry.pack(padx=20, pady=20)

                    def send_reply():
                        text = reply_entry.get("1.0", "end").strip()
                        if not text:
                            messagebox.showerror("Error", "กรุณากรอกข้อความตอบกลับ")
                            return
                        db.reply_message(mid, text)
                        messagebox.showinfo("สำเร็จ", "ส่งคำตอบเรียบร้อยแล้ว")
                        reply_popup.destroy()
                        popup.destroy()
                        self.show_inbox()

                    ctk.CTkButton(reply_popup, text="ส่งข้อความ",
                                fg_color="#33CC66", hover_color="#00CC44", text_color="white",
                                command=send_reply).pack(pady=10)

                ctk.CTkButton(box, text="✉️ ตอบกลับ",
                            fg_color="#33CC66", hover_color="#00CC44", text_color="white",
                            command=open_reply).pack(anchor="e", padx=10, pady=6)

    # ---------------- Delete Order ---------------- ลบคำสั่งซื้อ
    def delete_order(self, order_id):
        confirm = messagebox.askyesno("ยืนยันการลบ", "คุณต้องการลบคำสั่งซื้อนี้หรือไม่?")
        if confirm:
            try:
                db.delete_order(order_id)
                messagebox.showinfo("สำเร็จ", "ลบคำสั่งซื้อเรียบร้อยแล้ว")
                self.show_orders()  # โหลดตารางใหม่
            except Exception as e:
                messagebox.showerror("Error", f"เกิดข้อผิดพลาดขณะลบคำสั่งซื้อ: {e}")

        # ---------------- สรุปยอดขาย (เลือกช่วงวัน) ----------------
    def show_sales_summary(self):
        from datetime import datetime
        import db
        from tkinter import messagebox

        popup = ctk.CTkToplevel(self)
        popup.title("สรุปยอดขายรวม")
        popup.geometry("900x750")
        popup.configure(fg_color="#E6F5EB")  # พื้นหลังขาวเขียวอ่อน

        # ตัวแปรเก็บ frame ของรายงาน (ไว้ล้างตอนเปลี่ยนวันที่)
        popup.summary_frame = None

        # ========== ส่วนเลือกวันที่ ==========
        top_frame = ctk.CTkFrame(popup, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#33CC66")
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_frame, text="เลือกช่วงวันที่:", text_color="#006633", font=("", 16, "bold")).pack(side="left", padx=10)

        years = [str(y) for y in range(2023, datetime.now().year + 1)]
        months = [f"{m:02}" for m in range(1, 13)]
        days = [f"{d:02}" for d in range(1, 32)]

        start_year = ctk.StringVar(value=str(datetime.now().year))
        start_month = ctk.StringVar(value=f"{datetime.now().month:02}")
        start_day = ctk.StringVar(value="01")

        end_year = ctk.StringVar(value=str(datetime.now().year))
        end_month = ctk.StringVar(value=f"{datetime.now().month:02}")
        end_day = ctk.StringVar(value=f"{datetime.now().day:02}")

        # วันที่เริ่ม
        ctk.CTkLabel(top_frame, text="จาก", text_color="#006633").pack(side="left", padx=(15,5))
        ctk.CTkOptionMenu(top_frame, values=days, variable=start_day, width=60, fg_color="#33CC66", button_color="#00CC44", text_color="#FFFFFF").pack(side="left", padx=2)
        ctk.CTkOptionMenu(top_frame, values=months, variable=start_month, width=70, fg_color="#33CC66", button_color="#00CC44", text_color="#FFFFFF").pack(side="left", padx=2)
        ctk.CTkOptionMenu(top_frame, values=years, variable=start_year, width=80, fg_color="#33CC66", button_color="#00CC44", text_color="#FFFFFF").pack(side="left", padx=2)

        # วันที่สิ้นสุด
        ctk.CTkLabel(top_frame, text="ถึง", text_color="#006633").pack(side="left", padx=(15,5))
        ctk.CTkOptionMenu(top_frame, values=days, variable=end_day, width=60, fg_color="#33CC66", button_color="#00CC44", text_color="#FFFFFF").pack(side="left", padx=2)
        ctk.CTkOptionMenu(top_frame, values=months, variable=end_month, width=70, fg_color="#33CC66", button_color="#00CC44", text_color="#FFFFFF").pack(side="left", padx=2)
        ctk.CTkOptionMenu(top_frame, values=years, variable=end_year, width=80, fg_color="#33CC66", button_color="#00CC44", text_color="#FFFFFF").pack(side="left", padx=2)

            
        def load_summary():
            start_date = f"{start_year.get()}-{start_month.get()}-{start_day.get()}"
            end_date = f"{end_year.get()}-{end_month.get()}-{end_day.get()}"

            # ลบรายงานเก่า
            try:
                if hasattr(popup, "summary_frame") and popup.summary_frame and popup.summary_frame.winfo_exists():
                    popup.summary_frame.pack_forget()
                    popup.summary_frame.destroy()
            except Exception:
                pass
            popup.summary_frame = None

            # ตรวจสอบวันที่
            try:
                dt_start = datetime.strptime(start_date, "%Y-%m-%d")
                dt_end = datetime.strptime(end_date, "%Y-%m-%d")
                if dt_start > dt_end:
                    dt_start, dt_end = dt_end, dt_start
                    start_date = dt_start.strftime("%Y-%m-%d")
                    end_date = dt_end.strftime("%Y-%m-%d")
            except Exception:
                messagebox.showerror("Error", "วันที่ไม่ถูกต้อง (รูปแบบ YYYY-MM-DD)")
                return

            # โหลดข้อมูลจากฐานข้อมูล
            try:
                orders = db.get_orders_by_date_range(start_date, end_date)
                products = db.get_sales_by_product_range(start_date, end_date)
            except Exception as e:
                messagebox.showerror("Error", f"โหลดข้อมูลไม่สำเร็จ: {e}")
                return

            # สร้าง Scrollable Frame ใหม่
            popup.summary_frame = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF", width=860, height=600)
            popup.summary_frame.pack(padx=10, pady=10, fill="both", expand=True)

            total_income = sum(o.get('total', 0) for o in orders) if orders else 0

            # ===== หัวข้อรายงาน =====
            ctk.CTkLabel(
                popup.summary_frame,
                text=f"ยอดขายระหว่าง {start_date} ถึง {end_date}",
                font=("", 18, "bold"), text_color="#006633"
            ).pack(pady=10)

            ctk.CTkLabel(
                popup.summary_frame,
                text=f"รายได้รวม: {total_income:,.2f} บาท",
                font=("", 18, "bold"), text_color="#00CC66"
            ).pack()

            # ===== รายการคำสั่งซื้อ =====
            ctk.CTkLabel(
                popup.summary_frame,
                text="📦 รายการคำสั่งซื้อ",
                font=("", 17, "bold"), text_color="#006633"
            ).pack(anchor="w", padx=10, pady=(15, 5))

            if not orders:
                ctk.CTkLabel(popup.summary_frame, text="ไม่มีคำสั่งซื้อในช่วงนี้", text_color="#009966").pack()
            else:
                for order in orders:
                    order_frame = ctk.CTkFrame(popup.summary_frame, fg_color="#E6F5EB", corner_radius=10, border_width=1, border_color="#33CC66")
                    order_frame.pack(fill="x", padx=10, pady=5)

                    created = order.get('created_at', '')
                    ctk.CTkLabel(
                        order_frame,
                        text=f"คำสั่งซื้อ #{order['id']} - {created}",
                        text_color="#006633", font=("", 14, "bold")
                    ).pack(anchor="w", padx=10, pady=(5, 0))

                    for name, qty, sub in order.get("items", []):
                        ctk.CTkLabel(
                            order_frame, text=f"• {name} x{qty} = {sub:,.2f} บาท", text_color="#004d33"
                        ).pack(anchor="w", padx=20)

                    total_val = float(order.get('total', 0) or 0)
                    subtotal_val = total_val / 1.07
                    vat_val = total_val - subtotal_val

                    ctk.CTkLabel(
                        order_frame,
                        text=f"ยอดรวมค่าสินค้า (Subtotal): {subtotal_val:,.2f} บาท",
                        text_color="#006633", font=("", 13)
                    ).pack(anchor="w", padx=10, pady=(2, 0))

                    ctk.CTkLabel(
                        order_frame,
                        text=f"ภาษีมูลค่าเพิ่ม 7% (VAT): {vat_val:,.2f} บาท",
                        text_color="#009966", font=("", 13)
                    ).pack(anchor="w", padx=10)

                    ctk.CTkLabel(
                        order_frame,
                        text=f"ยอดสุทธิที่ชำระ (Total Paid): {total_val:,.2f} บาท",
                        text_color="#00CC66", font=("", 14, "bold")
                    ).pack(anchor="w", padx=10, pady=(0, 4))

            # ===== สรุปยอดขายตามสินค้า =====
            ctk.CTkLabel(
                popup.summary_frame,
                text="\n📊 สรุปยอดขายตามสินค้า",
                font=("", 17, "bold"), text_color="#006633"
            ).pack(anchor="w", padx=10, pady=(15, 5))

            if not products:
                ctk.CTkLabel(popup.summary_frame, text="ไม่มีข้อมูลสินค้าในช่วงนี้", text_color="#009966").pack()
            else:
                for name, qty, income in products:
                    ctk.CTkLabel(
                        popup.summary_frame,
                        text=f"• {name} {qty} ชิ้น — {income:,.2f} บาท",
                        text_color="#006633"
                    ).pack(anchor="w", padx=20, pady=2)

        # ปรับปุ่มดูรายงานด้านบนให้เข้าธีม
        ctk.CTkButton(
            top_frame,
            text="ดูรายงาน",
            fg_color="#33CC66",
            hover_color="#00CC44",
            text_color="white",
            command=load_summary
        ).pack(side="right", padx=20)
