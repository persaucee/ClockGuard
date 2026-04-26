# Feature Spec: Payroll Engine  
**Author:** Andrew Yastangacal
**Created:** 04/03/2026  
**Last Updated:** 04/03/2026  

---

## Overview  
The Payroll Engine is responsible for aggregating employee work sessions, calculating compensation, and managing payroll processing workflows.

It provides endpoints for:
- Generating payroll reports
- Processing payroll (marking sessions + sending emails)
- Viewing and editing payroll sessions
- Sending payroll emails manually

---

## Core Features  

### 1. Payroll Report (`GET /payroll/report`)
Generates a summarized payroll report across employees.

**Capabilities:**
- Can optionally filter by:
  - `start_date`
  - `end_date`
  - `processed` status
- Aggregates per employee:
  - Total hours worked
  - Total pay earned
  - Total tips
  - Number of sessions
- Groups results by employee

---

### 2. Payroll Processing (`POST /payroll/process`)

Processes unpaid payroll sessions and triggers email notifications.

**Modes of Operation:**
- By specific session IDs
- By date range
- All unprocessed sessions (default)

**Workflow:**
1. Fetch all employees in the organization
2. For each employee:
   - Retrieve unprocessed sessions
   - Apply filters (IDs or date range)
   - Sum:
     - Total hours
     - Total tips
   - Mark sessions as processed
3. Calculate total pay
4. Send Email to employee, showing estimated pay

### 3. Get Employee Sessions (`GET /payroll/{employee_id}`)

Retrieves all payroll sessions for a specific employee.

**Behavior:**
- Ensures organization-level access control
- Returns structured schema response
- Converts ORM objects → Pydantic models

---

### 4. Edit Payroll Session (`PUT /payroll/{session_id}`)

Allows updating a payroll session manually.

**Editable Fields:**
- Shift date
- Total hours
- Tip amount
- Total pay

---

## Goals  
- Centralize payroll operations into a single service layer
- Automate payroll calculation and email distribution

---