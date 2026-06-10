# PROJECT_CONTEXT.md

## Project Name

Maintenance Wizard AI

## Hackathon

Tata Steel AI Hackathon 2026
Round 2 - Agentic AI Challenge

---

## Project Vision

Build an enterprise-grade Agentic AI maintenance assistant for steel manufacturing plants that helps maintenance engineers diagnose equipment failures, identify root causes, predict future breakdowns, assess operational risks, and generate actionable maintenance recommendations.

The system should behave like an intelligent maintenance engineer capable of reasoning over multiple information sources and providing explainable decisions.

---

## Problem Statement

Industrial maintenance teams deal with large volumes of:

* Equipment logs
* Sensor alerts
* Maintenance history
* SOP documents
* Equipment manuals
* Inspection reports

Finding the correct root cause and deciding the next maintenance action often requires significant manual effort.

The objective is to build an AI-powered decision-support platform that reduces downtime, improves maintenance planning, and increases operational efficiency.

---

## Primary Users

### Maintenance Engineer

Responsibilities:

* Diagnose equipment issues
* Investigate failures
* Plan maintenance actions

### Plant Supervisor

Responsibilities:

* Monitor equipment health
* Review risk assessments
* Approve maintenance actions

### Reliability Engineer

Responsibilities:

* Analyze recurring failures
* Improve maintenance strategy
* Reduce unplanned downtime

---

## Core Capabilities

### Equipment Diagnosis

The system should analyze:

* Error logs
* Sensor readings
* Historical incidents

Output:

* Probable root causes
* Supporting evidence
* Confidence score

---

### Predictive Maintenance

The system should:

* Detect anomalies
* Estimate failure probability
* Predict maintenance needs

Output:

* Predicted issue
* Risk level
* Suggested maintenance timeline

---

### Risk Assessment

The system should evaluate:

* Failure severity
* Operational impact
* Safety implications

Output:

* Risk score
* Priority ranking
* Criticality level

---

### Knowledge Retrieval

The system should search:

* Equipment manuals
* SOP documents
* Historical maintenance records

Output:

* Relevant sections
* Similar incidents
* Supporting documentation

---

### Maintenance Recommendations

The system should generate:

* Corrective actions
* Preventive actions
* Inspection checklists
* Spare-part recommendations

---

### Explainable AI

Every recommendation must include:

* Why the recommendation was made
* Data sources used
* Retrieved evidence
* Confidence level

No black-box decisions.

---

## Agentic AI Architecture

### Supervisor Agent

Responsibilities:

* Understand user requests
* Create execution plans
* Coordinate agents
* Aggregate final response

---

### Retrieval Agent

Responsibilities:

* Search manuals
* Search SOPs
* Search maintenance history
* Retrieve supporting evidence

Tools:

* Vector Database
* Semantic Search

---

### Diagnostic Agent

Responsibilities:

* Analyze symptoms
* Identify probable causes
* Perform root-cause analysis

Inputs:

* Sensor alerts
* Logs
* Retrieved knowledge

Outputs:

* Ranked causes
* Confidence scores

---

### Prediction Agent

Responsibilities:

* Detect anomalies
* Predict failures
* Estimate maintenance urgency

Outputs:

* Failure probability
* Time-to-failure estimate

---

### Risk Assessment Agent

Responsibilities:

* Calculate risk score
* Evaluate business impact
* Prioritize maintenance tasks

Outputs:

* Critical
* High
* Medium
* Low

---

### Recommendation Agent

Responsibilities:

* Generate maintenance plans
* Recommend actions
* Suggest inspections

Outputs:

* Action plan
* Recommended next steps

---

### Report Agent

Responsibilities:

* Create final engineer-friendly report
* Summarize findings
* Explain reasoning

Outputs:

* Structured report
* Executive summary

---

## Data Sources

### Equipment Logs

Fields:

* Timestamp
* Equipment ID
* Error Code
* Error Description

### Sensor Data

Fields:

* Temperature
* Vibration
* Pressure
* Current
* Voltage

### Maintenance Records

Fields:

* Equipment ID
* Failure Type
* Repair Action
* Repair Date

### SOP Documents

Content:

* Standard operating procedures
* Inspection instructions

### Equipment Manuals

Content:

* Manufacturer documentation
* Troubleshooting guides

---

## Suggested Technology Stack

Frontend:

* Next.js
* TypeScript
* TailwindCSS

Backend:

* FastAPI

Agent Framework:

* LangGraph

LLM:

* Gemini 2.5 Pro

Vector Database:

* FAISS

Embeddings:

* Sentence Transformers

Machine Learning:

* Scikit-Learn
* XGBoost

Database:

* PostgreSQL

Deployment:

* Docker

---

## Expected Workflow

1. User submits equipment issue.

2. Supervisor Agent creates execution plan.

3. Retrieval Agent gathers relevant information.

4. Diagnostic Agent performs root-cause analysis.

5. Prediction Agent estimates future failures.

6. Risk Agent evaluates severity.

7. Recommendation Agent creates maintenance plan.

8. Report Agent generates explainable report.

9. User provides feedback.

10. Feedback is stored for future learning.

---

## Success Metrics

* Reduced downtime
* Faster diagnosis
* Better maintenance planning
* Improved safety
* Higher equipment availability
* Explainable AI decisions
* Industrial scalability

---

## Important Requirement

This is not a chatbot.

This is a multi-agent industrial maintenance decision-support platform where specialized AI agents collaborate to diagnose, predict, assess risk, and recommend actions using real operational context.
