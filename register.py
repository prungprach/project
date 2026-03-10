import re
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import db

class RegisterFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="black")
        self.master = master

        # --- โหลดภาพพื้นหลังให้เต็มหน้าจอ ---
        try:
            self.bg_image_orig = Image.open("assets/regis.png")
            self.bg_resized = self.bg_image_orig.resize(
                (self.master.winfo_screenwidth(), self.master.winfo_screenheight())
            )
            self.bg_ctk = ImageTk.PhotoImage(self.bg_resized)
            self.bg_label = ctk.CTkLabel(self, image=self.bg_ctk, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.bind("<Configure>", self.resize_bg)
        except Exception as e:
            print("⚠️ ไม่พบไฟล์ภาพพื้นหลัง:", e)

        entry_style = {"width": 300, "height": 40, "fg_color": "#000000", "text_color": "#FFFFFF"}
        button_style = {"width": 200, "height": 40, "fg_color": "black",
                        "hover_color": "#333333", "text_color": "white"}

        # --- ช่องกรอกข้อมูล ---
        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email", **entry_style)
        self.email_entry.place(relx=0.5, rely=0.30, anchor="center")

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Name", **entry_style)
        self.name_entry.place(relx=0.5, rely=0.38, anchor="center")

        # ✅ ช่องเบอร์โทร — เอา validate ออก เพื่อให้ placeholder แสดงผลได้
        self.phone_entry = ctk.CTkEntry(self, placeholder_text="Telephone number", **entry_style)
        self.phone_entry.place(relx=0.5, rely=0.46, anchor="center")
        self.phone_entry.bind("<FocusOut>", self.check_phone_input)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*", **entry_style)
        self.password_entry.place(relx=0.5, rely=0.54, anchor="center")

        register_btn = ctk.CTkButton(self, text="Register", command=self.register_user, **button_style)
        register_btn.place(relx=0.5, rely=0.62, anchor="center")

        back_btn = ctk.CTkButton(self, text="Back to Login",
                                 command=lambda: master.show_frame("login"), **button_style)
        back_btn.place(relx=0.5, rely=0.70, anchor="center")

    # ✅ ปรับขนาดภาพพื้นหลังให้เต็มหน้าจออัตโนมัติ
    def resize_bg(self, event):
        if hasattr(self, "bg_image_orig") and self.bg_image_orig:
            resized = self.bg_image_orig.resize((event.width, event.height), Image.LANCZOS)
            self.bg_ctk = ImageTk.PhotoImage(resized)
            self.bg_label.configure(image=self.bg_ctk)
            self.bg_label.image = self.bg_ctk

    # ✅ ตรวจสอบเบอร์โทรเมื่อออกจากช่อง
    def check_phone_input(self, event):
        phone = self.phone_entry.get().strip()
        if phone and (not phone.isdigit() or len(phone) > 10):
            messagebox.showwarning("Warning", "กรุณากรอกเฉพาะตัวเลข และไม่เกิน 10 หลัก")
            self.phone_entry.delete(0, "end")

    def register_user(self):
        email = self.email_entry.get().strip()
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not name or not phone or not password:
            messagebox.showwarning("Warning", "กรุณากรอกข้อมูลให้ครบทุกช่อง")
            return

        if not re.fullmatch(r"\d{10}", phone):
            messagebox.showerror("Error", "กรุณากรอกเบอร์โทรให้ถูกต้อง (ตัวเลข 10 หลัก)")
            return

        if len(password) < 8:
            messagebox.showerror("Error", "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
            return
        if not re.search(r"[A-Z]", password):
            messagebox.showerror("Error", "รหัสผ่านต้องมีตัวอักษรพิมพ์ใหญ่ อย่างน้อย 1 ตัว")
            return
        if not re.search(r"[a-z]", password):
            messagebox.showerror("Error", "รหัสผ่านต้องมีตัวอักษรพิมพ์เล็ก อย่างน้อย 1 ตัว")
            return
        if not re.search(r"[0-9]", password):
            messagebox.showerror("Error", "รหัสผ่านต้องมีตัวเลข อย่างน้อย 1 ตัว")
            return

        if db.add_user(email, name, phone, password):
            messagebox.showinfo("Success", f"สร้างบัญชี {email} สำเร็จ")
            self.master.show_frame("login")
        else:
            messagebox.showerror("Error", "Email นี้ถูกใช้งานแล้ว")
