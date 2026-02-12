import cv2

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

#camera settings tuning (ensure its 60ps at 1080p)
capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
capture.set(cv2.CAP_PROP_FPS, 60)

#setting our region of interest (ROI) so it only scans within that area
ROI_W, ROI_H = 450, 550
x_start = (1920 - ROI_W) // 2
y_start = (1080 - ROI_H) // 2

while True:
    ret, frame = capture.read()
    if not ret: break

    # crop original frame based off the ROI
    roi_frame = frame[y_start:y_start+ROI_H, x_start:x_start+ROI_W]
    gray_roi = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)  # turn the fram into greyscale for better matching 

    # require a high confidence before it shows the ready to scan box
    faces = face_cascade.detectMultiScale(
        gray_roi, 
        scaleFactor=1.1, 
        minNeighbors=12, #how many times the face must overlap in the frames before it accepts a true detection
        minSize=(200, 200) #this removes just the eye detecting errors I was having
    )

    # Draw the Alignment
    cv2.rectangle(frame, (x_start, y_start), (x_start+ROI_W, y_start+ROI_H), (192, 192, 192), 2)
    cv2.putText(frame, "Please Align Face Within Box", (x_start, y_start - 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (192, 192, 192), 2)

    # logic
    if len(faces) > 0:
        for (x, y, w, h) in faces:
            # reverse back to full frames to get max accuracy
            fx, fy = x + x_start, y + y_start
            cv2.rectangle(frame, (fx, fy), (fx + w, fy + h), (0, 255, 0), 2)
            cv2.putText(frame, "Face Detected :D YIPPIEE", (fx, fy - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "HURRY UP AND ALIGN YOUR FACE", (x_start, y_start + ROI_H + 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

    cv2.imshow('Scanner Basics, Press q to exit', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

capture.release()
cv2.destroyAllWindows()