# ClockGuard 


---

## About the Project
**ClockGuard** is a lightning-fast, touchless facial recognition timeclock and automated payroll suite.

Unlike traditional systems that rely on insecure ID badges or manual spreadsheets, ClockGuard utilizes biometrics to perform real time facial verification on the client device. It securely communicates with its backend to log immutable attendance records, to automating the calculation of worked hours, including tips.

##  Tech Stack

| **Client** | Python, OpenCV, ResNet V1 | MiniFASNetV2 |
| **Backend** | FastAPI, Uvicorn | REST API |
| **Database** | PostgreSQL, Supabase | Relational Data & Vector Storage |
| **Deployment** | Render / Railway | CI/CD Pipeline for the backend |
---

##  Security & Privacy
ClockGuard stores 0 images
* We only store vector embeddings. It is hard to reverse engineer a face from those vectors if compromised. 
* Raw video feeds never leave the local device.
* All database logs are append only to prevent tampering.

## Project Structure
```
/docs       → Project documentation
/backend    → FastAPI Backend
/frontend   → React Frontend for admins to access
/vision     → Tkinter UI to access the scanner or register employee script


Created By: Dave Persaud (FOUNDER), Zachary Fernandez (FOUNDER), Andrew Yastangacal (BACKEND ENGINEER), Sabeeh Qureshi (FRONTEND DEVELOPER), and Roheemat Adebiyi (BACKEND ENGINEER)

Any Questions Please Contact dbp@njit.edu