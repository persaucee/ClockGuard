# Sprint 4 Planning — ClockGuard
**Sprint Dates:** 03/24 – 04/02  
**Sprint Goal:** Successfully integrate the kiosk edge device, backend logic, and web dashboard to record a seamless, end-to-end midterm demonstration of a touchless clock-in and automated payroll processing.

---

## Tasks

| ID | Story / Task | Assignee | Priority | Status |
|----|--------------|----------|----------|--------|
| 69 | **Frontend - Implement "Tip Entry" UI:** As a manager, I want to manually input credit card tips so that they are added to the employee's final payroll calculation. | [Frontend Eng] | High | To Do |
| 70 | **Frontend - Implement Run Payroll Button:** As an admin, I want to click a 'Run Payroll' button so that wages are calculated and emails are triggered. | [Frontend Eng] | High | To Do |
| 71 | **Frontend - Integrate WebSockets to simulate Live Activity Feed:** As a manager, I want to see a live activity feed so that I know exactly when employees clock in without having to refresh the page. | [Frontend Eng] | High | To Do |
| 72 | **Frontend - Visual Security & Review Flags:** As an admin, I want to see visual warning flags on shifts so that I can review missed punches or failed liveness spoof attempts. | [Frontend Eng] | Medium | To Do |
| 73 | **Backend - Build /admin/process_payroll endpoint:** As the system, I need an endpoint to aggregate hours and tips so that final payroll data is written to the DB. | [Backend Eng] | High | To Do |
| 74 | **Backend - Update Payroll Calculator Math:** As the backend, I need updated math logic so that `Total Pay = (Total Hours * Hourly Rate) + Tips`. | [Backend Eng] | High | To Do |
| 75 | **Backend - Event Broadcaster:** As the system, I need a WebSocket broadcaster so that the frontend is instantly notified when a face is verified. | [Backend Eng] | High | To Do |
| 76 | **Vision - Add audio polish upon successful scan:** As an employee, I want to hear an audio chime upon a successful scan so that I have immediate confirmation my punch was recorded. | [Vision Eng] | Medium | To Do |
| 77 | **Vision - Prod boot script:** As an admin, I need a production startup script so that the kiosk application launches automatically and securely when the device powers on. | [Vision Eng] | Medium | To Do |
| 78 | **Database - Tip Engine Schema Engine:** As the database, I need a new tip column in the payroll table so that manual manager tip entries can be stored persistently. | [Database Eng] | High | To Do |
| 79 | **Database - Create "Weekly vs. Monthly" analytics views:** As a manager, I want analytical views so that I can visualize my labor costs easily on the dashboard. | [Database Eng] | Low | To Do |
| 80 | **Database - Develop DB Seed Script:** As a developer, I need a script to inject dummy data so that the dashboard looks like a real, active business for the midterm video. | [Database Eng] | High | To Do |

---

## Acceptance Criteria
- [ ] End-to-end integration is proven: Scanning a face on the Kiosk instantly updates the Web Dashboard via WebSockets.
- [ ] The "Tip Engine" workflow is fully functional (DB Schema -> UI Entry -> Backend Math).
- [ ] Running payroll successfully processes the math and generates an automated payload/email without crashing.
- [ ] The system has been seeded with realistic dummy data for the presentation.

---

## Dependencies / Blockers
- **Blocker:** Database Schema Update has to be completed before Frontend or Backend can start working on the tip engine.
- **Blocker:** Backend Event Broadcaster must be deployed before the Frontend can connect its Live Activity Feed.

## Notes
- **Midterm Video Deadline:** April 3rd! All features in this sprint must be in tact for demonstration in the midterm video.