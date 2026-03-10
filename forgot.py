import re
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import db

class ForgotFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="black")
        self.master = master

        # --- โหลดภาพพื้นหลัง ---
        try:
            self.bg_image_orig = Image.open("assets/forgot.png")
            self.bg_photo = ImageTk.PhotoImage(self.bg_image_orig)
            self.bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.bind("<Configure>", self.resize_bg)
        except Exception as e:
            print("⚠️ ไม่พบไฟล์ภาพพื้นหลัง:", e)

        entry_style = {"width": 300, "height": 40, "fg_color": "#000000", "text_color": "#FFFFFF"}
        button_style = {"width": 200, "height": 40, "fg_color": "black",
                        "hover_color": "#333333", "text_color": "white"}

        # --- ฟอร์ม ---
        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email", **entry_style)
        self.email_entry.place(relx=0.5, rely=0.35, anchor="center")

        self.phone_entry = ctk.CTkEntry(self, placeholder_text="Phone", **entry_style)
        self.phone_entry.place(relx=0.5, rely=0.43, anchor="center")

        self.new_password_entry = ctk.CTkEntry(self, placeholder_text="New Password", show="*", **entry_style)
        self.new_password_entry.place(relx=0.5, rely=0.51, anchor="center")

        self.confirm_password_entry = ctk.CTkEntry(self, placeholder_text="Confirm Password", show="*", **entry_style)
        self.confirm_password_entry.place(relx=0.5, rely=0.59, anchor="center")

        # --- ปุ่ม ---
        reset_btn = ctk.CTkButton(self, text="Reset Password", command=self.reset_password, **button_style)
        reset_btn.place(relx=0.5, rely=0.69, anchor="center")

        back_btn = ctk.CTkButton(self, text="Back to Login",
                                 command=lambda: master.show_frame("login"), **button_style)
        back_btn.place(relx=0.5, rely=0.77, anchor="center")

    # --- ปรับขนาดภาพพื้นหลัง ---
    def resize_bg(self, event):
        if hasattr(self, "bg_image_orig") and self.bg_image_orig:
            resized = self.bg_image_orig.resize((event.width, event.height), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(resized)
            self.bg_label.configure(image=self.bg_photo)

    # --- ตรวจสอบรหัสผ่าน ---
    def validate_password(self, password):
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):  # ต้องมีตัวพิมพ์ใหญ่
            return False
        if not re.search(r"[a-z]", password):  # ต้องมีตัวพิมพ์เล็ก
            return False
        if not re.search(r"\d", password):  # ต้องมีตัวเลข
            return False
        return True

    # --- ฟังก์ชันรีเซ็ตรหัสผ่าน ---
    def reset_password(self):
        email = self.email_entry.get().strip()
        phone = self.phone_entry.get().strip()
        new_password = self.new_password_entry.get().strip()
        confirm_password = self.confirm_password_entry.get().strip()

        # ตรวจสอบว่ากรอกครบ
        if not email or not phone or not new_password or not confirm_password:
            messagebox.showwarning("Warning", "กรุณากรอกข้อมูลให้ครบทุกช่อง")
            return

        # ตรวจสอบว่ารหัสตรงกัน
        if new_password != confirm_password:
            messagebox.showerror("Error", "รหัสผ่านไม่ตรงกัน")
            return

        # ตรวจสอบรูปแบบรหัสผ่าน
        if not self.validate_password(new_password):
            messagebox.showerror(
                "Error",
                "รหัสผ่านต้องมีอย่างน้อย 8 ตัว และประกอบด้วย:\n"
                "- ตัวอักษรพิมพ์ใหญ่ (A-Z)\n"
                "- ตัวอักษรพิมพ์เล็ก (a-z)\n"
                "- ตัวเลข (0-9)"
            )
            return

                # ตรวจสอบผู้ใช้ในฐานข้อมูล
        user = db.get_user_by_email(email)
        if user:
            stored_phone = user[2]  # phone เก็บใน index 3
            if re.sub(r"\D", "", phone.strip()) == re.sub(r"\D", "", stored_phone.strip()):
                db.update_user_password(email, new_password)
                messagebox.showinfo("Success", "รีเซ็ตรหัสผ่านสำเร็จ! กรุณาเข้าสู่ระบบใหม่อีกครั้ง")
                self.master.show_frame("login")
            else:
                messagebox.showerror("Error", "เบอร์โทรไม่ถูกต้อง")
        else:
            messagebox.showerror("Error", "ไม่พบบัญชีอีเมลนี้ในระบบ")

