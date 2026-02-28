import customtkinter as ctk
from tkinter import messagebox
import cv2
import time
import numpy as np
from keras_facenet import FaceNet

#global vars
embedder = None
face_cascade = None

def load_ai():
    global embedder, face_cascade
    if embedder is None:
        print("\n[SYSTEM] Loading classifier")
        embedder = FaceNet()
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        print("[SYSTEM] Done Loading\n")

#camera logic
def run_camera_loop(mode="scanner", emp_name=""):
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
                        
                        vector_512 = embedder.embeddings(samples)[0].tolist()
                        
                        # UI Feedback: Logged In!
                        cv2.rectangle(frame, (x_start, y_start), (x_start+ROI_W, y_start+ROI_H), (0, 255, 0), 4)
                        cv2.putText(frame, "LOGGED IN!", (x_start + 110, y_start + ROI_H // 2), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                        cv2.imshow('ClockGuard CV Hub', frame)
                        
                        # Freeze for 2 seconds so they can read it
                        cv2.waitKey(2000) 

                        print("\n[MOCK API] Sending Vector to /verify endpoint...")
                        
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
                            cv2.rectangle(frame, (x_start, y_start), (x_start+ROI_W, y_start+ROI_H), (255, 255, 255), -1)
                            
                            face_crop = roi_frame[y:y+h, x:x+w]
                            face_160x160 = cv2.resize(face_crop, (160, 160))
                            face_rgb = cv2.cvtColor(face_160x160, cv2.COLOR_BGR2RGB)
                            samples = np.expand_dims(face_rgb, axis=0)
                            
                            vector = embedder.embeddings(samples)[0]
                            captured_vectors.append(vector)
                            last_capture_time = time.time()
                            print(f"Captured frame {len(captured_vectors)}/{MAX_SCANS}")

                        if len(captured_vectors) >= MAX_SCANS:
                            avg_vector = np.mean(captured_vectors, axis=0)
                            final_vector = avg_vector / np.linalg.norm(avg_vector)
                            final_vector_list = final_vector.tolist()
                            
                            cv2.putText(frame, "REGISTRATION COMPLETE!", (x_start + 40, y_start + ROI_H // 2 + 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                            cv2.imshow('ClockGuard CV Hub', frame)
                            cv2.waitKey(2000)

                            print(f"\n[MOCK API] Uploading {emp_name} to Database...")
                            
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
        
        # skip this
        self.build_hub_screen()

    def build_hub_screen(self):
        if self.current_frame: self.current_frame.destroy()
        
        self.current_frame = ctk.CTkFrame(self, width=500, height=400, corner_radius=15)
        self.current_frame.grid(row=0, column=0, padx=20, pady=20)
        self.current_frame.grid_propagate(False)
        
        ctk.CTkLabel(self.current_frame, text="Kiosk Hub (Dev Mode)", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=40)
        
        ctk.CTkButton(self.current_frame, text="Add New Employee", height=50, width=300, 
                      command=self.open_registration).pack(pady=15)
                      
        ctk.CTkButton(self.current_frame, text="Start Live Scanner", height=50, width=300, 
                      fg_color="green", hover_color="darkgreen", command=self.open_scanner).pack(pady=15)
                      
        ctk.CTkButton(self.current_frame, text="Exit App", fg_color="transparent", 
                      text_color="gray", command=self.destroy).pack(pady=20)

    def open_registration(self):
        dialog = ctk.CTkInputDialog(text="Enter the new employee's name:", title="Register")
        emp_name = dialog.get_input()
        
        if emp_name:
            self.withdraw() 
            run_camera_loop(mode="register", emp_name=emp_name) 
            self.deiconify() 

    def open_scanner(self):
        self.withdraw() 
        run_camera_loop(mode="scanner") 
        self.deiconify() 

if __name__ == "__main__":
    app = KioskHubApp()
    app.mainloop()