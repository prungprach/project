import customtkinter as ctk
from login import LoginFrame
from register import RegisterFrame
from forgot import ForgotFrame
from admin_dashboard import AdminDashboard
from user_dashboard import UserDashboard
import db

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Supplement Store")
        self.state('zoomed')  # fullscreen

        # --- สร้าง DB + admin + sample products ---
        db.create_admin_and_sample_products()

        # --- โหลดสินค้าเป็น list ของ dict สำหรับหน้า user ---
        products = db.get_products()
        self.products = [
            {
                "id": p[0],
                "name": p[1],
                "price": p[2],
                "stock": p[3],
                "unit": p[4],
                "description": p[5] if len(p) > 5 else ""  # เพิ่ม description
            }
            for p in products
        ]

        # --- Frames ---
        self.frames = {}
        self.frames["login"] = LoginFrame(self)
        self.frames["register"] = RegisterFrame(self)
        self.frames["forgot"] = ForgotFrame(self)
        self.frames["admin"] = AdminDashboard(self)
        self.frames["user"] = UserDashboard(self, self.products)

        self.show_frame("login")

    def show_frame(self, name):
        for f in self.frames.values():
            f.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()


