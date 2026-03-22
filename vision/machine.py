import customtkinter as ctk
from tkinter import messagebox
import cv2
import time
import numpy as np
from keras_facenet import FaceNet
import requests 
import threading


api_session = requests.Session()
BACKEND_URL = "http://localhost:8000"

embedder = None
face_cascade = None
#testing this out i dont know if it will work
class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, title="Kiosk Locked", text="Enter Admin Password to Exit:"):
        super().__init__()
        self.title(title)
        self.geometry("350x200")
        
        # Center the popup on the screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.winfo_screenheight() // 2) - (200 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.password = None
        
        ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=16)).pack(pady=(30, 10))
        
     
        self.entry = ctk.CTkEntry(self, show="*", width=250)
        self.entry.pack(pady=10)
        self.entry.focus()
        
        # Bind the Enter key to submit
        self.bind('<Return>', lambda event: self.submit())
        
        ctk.CTkButton(self, text="Submit", command=self.submit, width=250).pack(pady=15)
        
        # Make this popup block the rest of the app until it's closed
        self.grab_set()
        self.wait_window(self)
        
    def submit(self):
        self.password = self.entry.get()
        self.destroy()
        
    def get_input(self):
        return self.password
def load_ai():
    global embedder, face_net_dnn, liveness_net
    if embedder is None:
        print("\n[SYSTEM] Loading classifier")
        embedder = FaceNet()
        face_net_dnn = cv2.dnn.readNetFromCaffe("./models/deploy.prototxt", "./models/res10_300x300_ssd_iter_140000.caffemodel")
        liveness_net = cv2.dnn.readNetFromONNX("./models/2.7_80x80_MiniFASNetV2.onnx")
        print("[SYSTEM] Done Loading\n")
#===============
#camera logic
#================
# This is the antispoofer with lightweight MiniFASNetV2, lightweight CNN

def check_liveness(frame, x,y,w,h):
    scale = 2.7 #this scales to 80x80 from the face crop
    center_x, center_y = x + w//2, y + h//2 #center of the detected face
    new_w, new_h = int(w * scale), int(h * scale) #new dimensions

    start_x = max(0, center_x-new_w//2)
    start_y = max(0, center_y -new_h//2)
    end_x = min(frame.shape[1], center_x + new_w//2)
    end_y = min(frame.shape[0], center_y + new_h//2)

    face_crop = frame[start_y:end_y, start_x:end_x]

    if face_crop.size == 0:
        return False, 0.0
    blob = cv2.dnn.blobFromImage(face_crop, scalefactor=1.0, size=(80, 80), mean=(0, 0, 0), swapRB=False, crop=False)
    liveness_net.setInput(blob)
    preds = liveness_net.forward()
    raw_scores = preds[0]
    exp_scores = np.exp(raw_scores - np.max(raw_scores))
    softmax_scores = exp_scores / np.sum(exp_scores)
    
    label_index = np.argmax(softmax_scores)
    conf = softmax_scores[label_index]

    # MiniFASNetV2 uses Class 1 for Real Faces!
    is_live = (label_index == 1) and (conf > 0.50)
    
    # We now return the actual label_index so we can debug properly
    return is_live, conf, label_index
def run_camera_loop(mode="scanner", emp_data=None, is_locked=False,org_id=None):
    emp_name = emp_data["name"] if emp_data else ""
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
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        face_net_dnn.setInput(blob)
        detections = face_net_dnn.forward()
        faces = []
        match = None
        max_area = 0
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.60:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x1, y1) = box.astype("int")
                rel_x = x - x_start
                rel_y = y - y_start
                fw= x1 - x
                fh = y1 - y
                
                if rel_x > -50 and rel_y > -50 and rel_x + fw < ROI_W +50 and rel_y + fh < ROI_H + 50:
                   area = fw * fh
                   if area > max_area:
                        max_area = area
                        match = (rel_x, rel_y, fw, fh) 

        if match is not None:
            faces = [match]
        else: 
            faces = []
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
                        
                        is_live, conf = check_liveness(roi_frame, x, y, w, h)
                        if not is_live:
                            print(f"[DEBUG LIVENESS] Class: {2} | Confidence: {conf:.2f}")
                            cv2.imshow('ClockGuard CV Hub', frame)
                            cv2.waitKey(2000)
                            start_Time = None
                            break

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
                        payload = {"embedding": vector_512, "organization_id": org_id } #this is whats send through the /verify endpoint
                        def verify_backend():

                            try:
                                response = api_session.post(f"{BACKEND_URL}/employees/verify", json=payload)

                                if response.status_code == 200:
                                    data = response.json()
                                    employee = data.get("match", {}).get("name", "Unknown")
                                    similarity = data.get("similarity", 0.0)

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
                        threading.Thread(target=verify_backend).start()
                        cv2.rectangle(frame, (x_start, y_start), (x_start+ROI_W, y_start+ROI_H), (0, 255, 0), 4)
                        cv2.putText(frame, "PROCESSING...", (x_start + 80, y_start + ROI_H // 2), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)
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
                            is_live, conf = check_liveness(roi_frame, x, y, w, h)
                            if not is_live:
                                print("[SYSTEM] Liveness not detected")
                                cv2.putText(frame, f"Not Live: {conf:.2f}", (fx, fy - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                cv2.imshow('ClockGuard CV Hub', frame)
                                cv2.waitKey(2000)
                                continue
                            
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
                                "organization_id": org_id,
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
        
        #lockscreen
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            if not is_locked:
                print("[SYSTEM] Testing Mode: Exiting camera freely.")
                break
            else:
                
                print("[SYSTEM] Kiosk Locked: Requesting Admin override...")
                
                # start a password request
                pwd_dialog = PasswordDialog()
                entered_pwd = pwd_dialog.get_input()
                
                if entered_pwd:
                    # Bounce the password against the backend API to verify!
                    payload = {"username": "admin", "password": entered_pwd}
                    try:
                        resp = api_session.post(f"{BACKEND_URL}/auth/login", json=payload)
                        if resp.status_code == 200:
                            print("[API] Override Accepted. Returning to Hub.")
                            break # Breaks the camera loop
                        else:
                            messagebox.showerror("Access Denied", "Incorrect Admin Password")
                    except requests.exceptions.ConnectionError:
                        messagebox.showerror("Error", "Could not connect to auth server.")

    capture.release()
    cv2.destroyAllWindows()

#bypass login
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue") 

class KioskHubApp(ctk.CTk):
    def __init__(self, is_locked=False):
        super().__init__()
        print("[SYSTEM] loading ai models")
        load_ai()
        self.is_locked = is_locked
        self.title("ClockGuard Scanner System")
        #set lock mode
        if self.is_locked:
            self.attributes("-fullscreen", True)
            self.protocol("WM_DELETE_WINDOW", self.disable_event)  #detects for the event delete window and disables that event
            print("[SYSTEM] Booting in SECURE MODE")
        else:
            self.attributes("-fullscreen", True) 
            self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
            print("[SYSTEM] Booting in DEV MODE")
            
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.current_frame = None
        self.build_login_screen()

    def disable_event(self):
        pass

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
                data = response.json()
                self.current_admin = username
                self.org_id = data.get("organization_id")
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
        if not emp_email: return # d
        
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
        run_camera_loop(mode="register", emp_data=emp_data, is_locked=self.is_locked,org_id=self.org_id)
        self.deiconify() 

    def open_scanner(self):
        self.withdraw() 
        run_camera_loop(mode="scanner", is_locked=self.is_locked,org_id=self.org_id)
        self.deiconify()

if __name__ == "__main__":
    import tkinter as tk
    
    
    root = tk.Tk()
    root.withdraw()
    
    #ask for what boot node
    enable_kiosk = messagebox.askyesno(
        "Startup Configuration", 
        "Boot in SECURE KIOSK mode?\n\n(Select 'No' for Windowed Testing Mode)"
    )
    root.destroy()
    
    # boot selected app
    app = KioskHubApp(is_locked=enable_kiosk)
    app.mainloop()