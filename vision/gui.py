import customtkinter as ctk
from tkinter import messagebox

#this will be changed later so it will match with the theme of the webstie
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue") 




class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

   
        self.title("ClockGuard Kiosk System")
        self.attributes("-fullscreen", True) #fullscreen it but we need to lock it later
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False)) 

   

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.login_frame = ctk.CTkFrame(self, width=400, height=500, corner_radius=15)
        self.login_frame.grid(row=0, column=0, padx=20, pady=20)
        self.login_frame.grid_propagate(False)
        self.label = ctk.CTkLabel(self.login_frame, text="ClockGuard Admin", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=(40, 20))
        self.email_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Admin Email", width=300)
        self.email_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Password", show="*", width=300)
        self.password_entry.pack(pady=10)
        self.login_button = ctk.CTkButton(self.login_frame, text="Login", command=self.attempt_login, width=300)
        self.login_button.pack(pady=30)
        self.exit_button = ctk.CTkButton(self.login_frame, text="Exit Application", fg_color="transparent", 
                                          text_color="gray", hover_color="#333333", command=self.destroy)
        self.exit_button.pack(pady=10)

    def attempt_login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        if not email or not password:
            messagebox.showwarning("Error", "Please fill in all fields.")
            return

        #will be replaced with api calls 
        print(f"DEBUG: Attempting login for {email}")

        if email == "admin" and password == "1234":
            messagebox.showinfo("Success", "Authenticated! Launching Camera...")
            self.launch_camera_mode()
        else:
            messagebox.showerror("Failed", "Invalid Credentials")

    def launch_camera_mode(self):
        self.destroy()

if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()