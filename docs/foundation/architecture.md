```markdown
# Architecture Overview — ClockGuard
**Last Updated:** 03/23/2026

---

## System Diagram
![System Diagram](./assets/diagrams/system_flow.png "System Diagram")
## Components
| **Client** | Python, OpenCV, ResNet V1 | MiniFASNetV2 |
| **Backend** | FastAPI, Uvicorn | REST API |
| **Database** | PostgreSQL, Supabase | Relational Data & Vector Storage |
| **Deployment** | Render / Railway | CI/CD Pipeline for the backend |

## Data Flow
Employee Clock In/Out

Employee walks up to live scanner (provided admin logged in and live scanner is running), employee scans face and liveness detecter filters whether it is a real human scanning or a dupe (image or video of a person), then passed through ResNet V1 to create a 1x512 vector embed of the employees face. This is passed through the /verify endpoint where the backend queries employee vector embeddings and uses cosine similarity to find the closest match. If the similarity threshold is not met (no user in db) the scanner rejects the face, otherwise prompts the clock in/out logic. It queries the latest attendance log from that employee and does the opposite (if clocked in -> clock out, otherwise clock in). Audit log is created in the attendance_logs table in the DB

___
Employee Registration

Admin clicks register employee where they are prompted with boxes to fill in employee name, wage, email, etc. Then the scanner boots where MULTIPLE captures of the employees face will create multiple vector embeddings and then they will be averaged into one vector embedding, which is then send through the backend to create a new employee storing their information along with the vector embedding just created. They are then returned back to the home screen. 


---
Payroll Processing

Admin logs in onto the website. They navigate to payroll where they click process payroll (button). This then triggers the automated calculations of each employees pay and sends this to the backend to then send out automated emails to each employee's email with their "pay stub" including all of the information of how long they worked, wage and tips if there were any. 

## External Services / Integrations
- Google Authenticator (2FA)
- Gmail (SMTP automated emails for paystubs)
- Railway (Cloud Hosting for Sprint 5)

## Key Design Decisions
| Decision | Reason |
|----------|--------|
| Decoupled Architecture (Vision Pipeline + Web App) | By separating the computer vision pipeline from the manager dashboard, the pipeline acts as a secure edge device. This biometric pipline can run without the extra proccess of payroll calculations or database interactions. Also, if the Vision pipline is down for any reason (lets say maintenance), admins can still access the web app without any interference. |

| OpenCV DNN over Haar Cascades | Instead of haar cascade as a face detector, we used OpenCV's DNN (deep neural network), as it uses full color making it significantly more accurate in different lighting conditions (such as darker lightings in hospitality based companies) |

| FaceNet 512d + Supabase pgvector | Mathematical embeddings are extracted instead of saving raw images. This protects employee privacy and allows the database to instantly match faces using cosine similarity math directly within supabase |

| FastAPI Backend over Flask/Django | FastAPI has native async/wait support and its perfect for handling the biometric verications from the cv pipeline, while simultaniously handling WebSocket updates for the manager portal on the web app. 
```

---
