# ClockGuard 


---

## About the Project
**ClockGuard** is a hybrid-cloud biometric pipeline designed to eliminate "buddy punching" and manual payroll errors. 

Unlike traditional legacy systems that rely on insecure ID badges or manual spreadsheets, ClockGuard utilizes biometrics to perform real-time facial verification on the client device. It securely communicates with a serverless backend to log immutable attendance records, to automating the calculation of billable hours.

##  System Architecture

1.  **(Client)** - Captures video feed via OpenCV.
    - Uses a Pre-Trained CNN (dlib/FaceNet) to extract 512-d embeddings.
    - Debouning to prevent duplicate calls
2.  **(API)**
    - Built with **FastAPI** (Python).
    - Handles state management (Determines if user is clocked in or out).
    - Validates requests.
3.  **(Storage)**
    - Hosted on **Supabase** (PostgreSQL).
    - Uses **pgvector** for similarity search.
##  Tech Stack

| **Client** | Python, OpenCV, Face_Recognition | Local biometric processing & UI |
| **Backend** | FastAPI, Uvicorn | REST API & Business Logic |
| **Database** | PostgreSQL, Supabase | Relational Data & Vector Storage |
| **ML Engine** | dlib / ResNet-34 | Pre-trained CNN for embedding generation |
| **Deployment** | Render / Railway | CI/CD Pipeline for the backend |

---

##  Security & Privacy
ClockGuard stores 0 images
* We only store vector embeddings. It is hard to reverse engineer a face from those vectors if compromised. 
* Raw video feeds never leave the local device.
* All database logs are append only to prevent tampering.

Created By: Dave Persaud, Zachary Fernandez, Andrew Yastangacal, 
