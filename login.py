import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import db

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="black")
        self.master = master
        self.current_user_email = None

        # --- โหลดภาพพื้นหลังต้นฉบับ ---
        try:
            self.bg_image_orig = Image.open("assets/background.png")  # ✅ ตัดโลโก้ออกแล้ว
        except Exception as e:
            print("⚠️ ไม่พบไฟล์ภาพพื้นหลัง:", e)
            self.bg_image_orig = None

        # --- Label แสดงภาพพื้นหลัง ---
        if self.bg_image_orig:
            self.bg_photo = ImageTk.PhotoImage(self.bg_image_orig)
            self.bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            # ปรับขนาดอัตโนมัติเมื่อ Resize
            self.bind("<Configure>", self.resize_bg)

        # --- กล่องกรอกข้อมูล ---
        self.email_entry = ctk.CTkEntry(
            self,
            placeholder_text="Email",
            width=300,
            height=40,
            fg_color="#FFFFFF",
            text_color="#000000"
        )
        self.email_entry.place(relx=0.5, rely=0.40, anchor="center")

        self.password_entry = ctk.CTkEntry(
            self,
            placeholder_text="Password",
            show="*",
            width=300,
            height=40,
            fg_color="#FFFFFF",
            text_color="#000000"
        )
        self.password_entry.place(relx=0.5, rely=0.48, anchor="center")

        # --- ปุ่มสีดำ ตัวหนังสือสีขาว ---
        button_style = {
            "width": 300,
            "height": 40,
            "fg_color": "black",
            "hover_color": "#333333",
            "text_color": "white"
        }

        login_btn = ctk.CTkButton(
            self, text="Login", command=self.login, **button_style
        )
        login_btn.place(relx=0.5, rely=0.56, anchor="center")

        register_btn = ctk.CTkButton(
            self, text="Register",
            command=lambda: master.show_frame("register"), **button_style
        )
        register_btn.place(relx=0.5, rely=0.64, anchor="center")

        forgot_btn = ctk.CTkButton(
            self, text="Forgot Password?",
            command=lambda: master.show_frame("forgot"), **button_style
        )
        forgot_btn.place(relx=0.5, rely=0.72, anchor="center")

    # --- ฟังก์ชันปรับขนาดภาพพื้นหลัง ---
    def resize_bg(self, event):
        if self.bg_image_orig:
            width = event.width
            height = event.height
            resized = self.bg_image_orig.resize((width, height), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(resized)
            self.bg_label.configure(image=self.bg_photo)

    # --- ฟังก์ชัน Login ---
    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        user = db.get_user(email, password)

        if user:
            self.current_user_email = email
            if email == "admin@store.com":
                self.master.show_frame("admin")
            else:
                self.master.show_frame("user")
        else:
            messagebox.showerror("Error", "Invalid Email or Password")
