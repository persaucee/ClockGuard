import customtkinter as ctk
from tkinter import messagebox
import cv2
import time
import numpy as np
from keras_facenet import FaceNet
import requests 


api_session = requests.Session()
BACKEND_URL = "http://localhost:8000"

embedder = None
face_cascade = None

def load_ai():
    global embedder, face_cascade
    if embedder is None:
        print("\n[SYSTEM] Loading classifier")
        embedder = FaceNet()
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        print("[SYSTEM] Done Loading\n")
#===============
#camera logic
#================
def run_camera_loop(mode="scanner", emp_data=None):
    emp_name = emp_data["name"] if emp_data else ""
    load_ai() 

    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    capture.set(cv2.CAP_PROP_FPS, 60)

    ROI_W, ROI_H = 450, 550
    x_start = (1920 - ROI_W) // 2
    y_start = (1080 - ROI_H) // 2

    start_Time = None
    duration = 2.0 

    captured_vectors = []
    MAX_SCANS = 5
    last_capture_time = 0 
    
    #set flag to know when to fully exit scanner mode and go back to dashboard
    exit_camera = False 

    print(f"\n LAUNCHING {mode.upper()} MODE")

    while not exit_camera:
        ret, frame = capture.read()
        if not ret: break

        roi_frame = frame[y_start:y_start+ROI_H, x_start:x_start+ROI_W]
        gray_roi = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray_roi, scaleFactor=1.1, minNeighbors=12, minSize=(200, 200)
        )

        cv2.rectangle(frame, (x_start, y_start), (x_start+ROI_W, y_start+ROI_H), (192, 192, 192), 2)
        
        header_text = f"Registering: {emp_name}" if mode == "register" else "Live Scanner: Please Align Face"
        cv2.putText(frame, header_text, (x_start, y_start - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (192, 192, 192), 2)

        if len(faces) > 0:
            if start_Time is None: 
                start_Time = time.time()

            elapsed = time.time() - start_Time
            progress = min(elapsed / duration, 1.0)
            width = int(ROI_W * progress)

            cv2.rectangle(frame, (x_start, y_start + ROI_H + 10), (x_start + width, y_start + ROI_H + 30), (0, 255, 0), -1)

            for (x, y, w, h) in faces:
                fx, fy = x + x_start, y + y_start
                cv2.rectangle(frame, (fx, fy), (fx + w, fy + h), (0, 255, 0), 2)

                #get user to stand still to capture in phase 2
                if elapsed < duration:
                    cv2.putText(frame, f"Hold still... {elapsed:.1f}s", (fx, fy - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
               #CAPTURE LOGIC
                else:
                    # Scanner Mode
                    if mode == "scanner":
                        face_crop = roi_frame[y:y+h, x:x+w]
                        face_160x160 = cv2.resize(face_crop, (160, 160))
                        face_rgb = cv2.cvtColor(face_160x160, cv2.COLOR_BGR2RGB)
                        samples = np.expand_dims(face_rgb, axis=0)
                        
                        raw_vector = embedder.embeddings(samples)[0]
                        norm_vector = raw_vector / np.linalg.norm(raw_vector)
                        vector_512 = norm_vector.tolist()
                        #====================
                        #now verify face embed, this needs to be changed in the future for payroll etc
                        #====================
                        print("\n[API] Verifying scanned face...")
                        payload = {"embedding": vector_512} #this is whats send through the /verify endpoint

                        try:
                            response = api_session.post(f"{BACKEND_URL}/employees/verify", json=payload)

                            if response.status_code == 200:
                                data = response.json()
                                employee = data.get("match", {}).get("name", "Unknown")
                                similarity = data.get("simlarity", 0.0)

                                print(f"[API] YAAAY WE GOT A MATCH YOURE IN THE SYSTEM {employee}! the scan found your face to me {similarity:.2f} similar")

                                cv2.rectangle(frame, (x_start, y_start), (x_start+ROI_W, y_start+ROI_H), (0, 255, 0), 4)
                                cv2.putText(frame, f"WELCOME, {emp_name.upper()}!", (x_start + 20, y_start + ROI_H // 2), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)

                            elif response.status_code == 404:
                                print("[API] Face not recognized")

                                cv2.rectangle(frame, (x_start, y_start), (x_start+ROI_W, y_start+ROI_H), (0, 0, 255), 4)
                                cv2.putText(frame, "ACCESS DENIED", (x_start + 80, y_start + ROI_H // 2), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

                            else:
                                #error 500 internal error
                                print(f"[API] Server Error: {response.text}")
                                cv2.putText(frame, "SERVER ERROR", (x_start + 90, y_start + ROI_H // 2), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

                        except requests.exceptions.ConnectionError:
                            print("[API] Connection Failed")
                            cv2.putText(frame, "CONNECTION FAILED", (x_start + 40, y_start + ROI_H // 2), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

                        # Freeze for 1 second so they can read it
                        cv2.imshow('Clockguard hub!', frame)
                        cv2.waitKey(1000) 
                       
                        #fix
                        start_Time = None 
                        break 

                    # Registration
                    elif mode == "register":
                        cv2.putText(frame, f"Capturing {len(captured_vectors)}/5...", 
                                    (x_start + 10, y_start + ROI_H // 2), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
                        cv2.putText(frame, "Tilt head slightly between flashes!", 
                                    (x_start - 30, y_start + ROI_H // 2 + 40), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                        if time.time() - last_capture_time > 1.0:
                            face_crop = roi_frame[y:y+h, x:x+w].copy()
                            #white flash thing mimimm
                            cv2.rectangle(frame, (x_start, y_start), (x_start+ROI_W, y_start+ROI_H), (255, 255, 255), -1)
                            #cropping
                            face_160x160 = cv2.resize(face_crop, (160, 160))
                            #greyscale
                            face_rgb = cv2.cvtColor(face_160x160, cv2.COLOR_BGR2RGB)
                            #sampels
                            samples = np.expand_dims(face_rgb, axis=0)
                            
                            raw_vector = embedder.embeddings(samples)[0]
                            norm_vector = raw_vector / np.linalg.norm(raw_vector)
                            
                            captured_vectors.append(norm_vector)
                            last_capture_time = time.time()
                            print(f"Captured real face frame {len(captured_vectors)}/{MAX_SCANS}")

                        if len(captured_vectors) >= MAX_SCANS:
                            avg_vector = np.mean(captured_vectors, axis=0)
                            final_vector = avg_vector / np.linalg.norm(avg_vector)
                            final_vector_list = final_vector.tolist()
                            
                            cv2.putText(frame, "REGISTRATION COMPLETE!", (x_start + 40, y_start + ROI_H // 2 + 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                            cv2.imshow('ClockGuard CV Hub', frame)
                            cv2.waitKey(2000)

                            print(f"\n[API] Uploading {emp_name} to Database...")
                            payload = {
                                "name": emp_data["name"],
                                "email": emp_data["email"],
                                "hourly_rate": emp_data["hourly_rate"],
                                "embedding": final_vector_list 
                            }
                            
                            try:
                                response = api_session.post(f"{BACKEND_URL}/employees/", json=payload)
                                
                                if response.status_code == 200:
                                    print(f"[API] SUCCESS: {emp_name} saved to DB!")
                                else:
                                    print(f"[API] ERROR {response.status_code}: {response.text}")
                            except requests.exceptions.ConnectionError:
                                print("[API] CONNECTION ERROR: Is the FastAPI server running?")
                            
                            #main loop close
                            exit_camera = True
                            break 

        else:
            start_Time = None
            cv2.putText(frame, "HURRY UP AND ALIGN YOUR FACE", (x_start, y_start + ROI_H + 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

        cv2.imshow('ClockGuard CV Hub', frame)
        
        # admin leave will fix later
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            break

    capture.release()
    cv2.destroyAllWindows()

#bypass login
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue") 

class KioskHubApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ClockGuard Kiosk System")
        self.attributes("-fullscreen", True) 
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False)) 
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.current_frame = None
        
        #start screen 
        self.build_login_screen()

    def build_login_screen(self):
        if self.current_frame: self.current_frame.destroy()
        #settings for the login screen
        self.current_frame = ctk.CTkFrame(self, width=400, height=500, corner_radius=15)
        self.current_frame.grid(row=0, column=0, padx=20, pady=20)
        self.current_frame.grid_propagate(False)
        
        ctk.CTkLabel(self.current_frame, text="ClockGuard Admin", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 20))
        
        # match backend schema with username 
        self.username_entry = ctk.CTkEntry(self.current_frame, placeholder_text="Admin Username", width=300)
        self.username_entry.pack(pady=10)
        
        self.password_entry = ctk.CTkEntry(self.current_frame, placeholder_text="Password", show="*", width=300)
        self.password_entry.pack(pady=10)
        
        ctk.CTkButton(self.current_frame, text="Login", command=self.attempt_login, width=300).pack(pady=30)
        ctk.CTkButton(self.current_frame, text="Exit Application", fg_color="transparent", 
                      text_color="gray", hover_color="#333333", command=self.destroy).pack(pady=10)

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Error", "Please fill in all fields.")
            return

        print(f"\n[API] Attempting login for '{username}'...")

        # match schema plsplspplplsplsplspls
        payload = {
            "username": username,
            "password": password
        }
        
        try:
            # save cookie
            response = api_session.post(f"{BACKEND_URL}/auth/login", json=payload)
            
            if response.status_code == 200:
                print("[API] Login successful! Secure cookie saved to session.")
                self.build_hub_screen() 
                
            elif response.status_code == 401:
                #401
                messagebox.showerror("Login Failed", "Incorrect username or password")
                
            else:
                messagebox.showerror("Error", f"Server returned {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", "Could not connect to the backend. Is FastAPI running on port 8000?")

    def build_hub_screen(self):
        if self.current_frame: self.current_frame.destroy()
        
        self.current_frame = ctk.CTkFrame(self, width=500, height=400, corner_radius=15)
        self.current_frame.grid(row=0, column=0, padx=20, pady=20)
        self.current_frame.grid_propagate(False)
        
        ctk.CTkLabel(self.current_frame, text="Kiosk Hub", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=40)
        
        ctk.CTkButton(self.current_frame, text="Add New Employee", height=50, width=300, 
                      command=self.open_registration).pack(pady=15)
                      
        ctk.CTkButton(self.current_frame, text="Start Live Scanner", height=50, width=300, 
                      fg_color="green", hover_color="darkgreen", command=self.open_scanner).pack(pady=15)
                      
        # logout and not exit app
        ctk.CTkButton(self.current_frame, text="Logout", fg_color="transparent", 
                      text_color="gray", command=self.build_login_screen).pack(pady=20)

    def open_registration(self):
        #name (need to change into first and last name)
        dialog_name = ctk.CTkInputDialog(text="Enter the new employee's name:", title="Register (1/3)")
        emp_name = dialog_name.get_input()
        if not emp_name: return # Cancelled
        
        # emial
        dialog_email = ctk.CTkInputDialog(text=f"Enter email for {emp_name}:", title="Register (2/3)")
        emp_email = dialog_email.get_input()
        if not emp_email: return # Cancelled
        
        # rate
        dialog_rate = ctk.CTkInputDialog(text="Enter hourly rate (e.g., 25.50):", title="Register (3/3)")
        emp_rate_str = dialog_rate.get_input()
        if not emp_rate_str: return # Cancelled
        
        try:
            emp_rate = float(emp_rate_str)
        except ValueError:
            messagebox.showerror("Error", "Hourly rate must be a valid number!")
            return

        emp_data = {
            "name": emp_name,
            "email": emp_email,
            "hourly_rate": emp_rate
        }
        
        self.withdraw() 
        run_camera_loop(mode="register", emp_data=emp_data) 
        self.deiconify() 

    def open_scanner(self):
        self.withdraw() 
        run_camera_loop(mode="scanner") 
        self.deiconify()

if __name__ == "__main__":
    app = KioskHubApp()
    app.mainloop()