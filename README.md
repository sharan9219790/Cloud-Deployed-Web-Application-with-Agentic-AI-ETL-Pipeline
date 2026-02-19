# Cloud-Deployed Blog Application with Agentic AI & ETL Pipeline

## Overview

This project demonstrates a full-stack web application with secure cloud deployment, containerization, a local ETL pipeline, and a multi-agent LLM workflow.

Users can submit blog posts through a web interface. The application is containerized using Docker and deployed to AWS using Amazon ECR and ECS (Fargate). A local ETL pipeline processes blog submissions and LLM-generated metadata into a structured SQLite database.

This project integrates cloud infrastructure, security configuration, data engineering, and AI-based structured output generation.

---

## Architecture

### Frontend & Application Layer
- HTML + JavaScript blog submission form
- Client-side validation
- JSON serialization

### Containerization & Cloud Deployment
- Dockerized application (Nginx)
- Amazon ECR for image storage
- Amazon ECS (Fargate) for deployment
- Public IP access with controlled security group configuration

### Security Configuration
- IAM task execution role
- AWS Security Groups (HTTP port 80)
- Controlled public exposure
- No hardcoded credentials
- Input validation and structured data enforcement

### Agentic AI Pipeline
- Local LLM using Ollama (`smollm:1.7b`)
- Planner → Reviewer → Finalizer workflow
- Enforced constraints:
  - Exactly 3 topical tags
  - Summary ≤ 25 words
  - Strict JSON output

### ETL Pipeline (Local)
- Extract: Blog submissions from JSONL input
- Transform: Text cleanup, tag normalization, summary trimming, validation
- Load: SQLite database storage

---

## Technologies Used

- HTML
- JavaScript (ES6+)
- Python 3
- Docker
- AWS ECS (Fargate)
- Amazon ECR
- IAM
- Security Groups
- SQLite
- Ollama (Local LLM)

---

## Project Structure

HW1/
│── index.html
│── script.js
│── Dockerfile

HW1_agents/
│── agents_demo.py

HW1_etl/
│── etl_pipeline.py
│── data/
│── db/


---

## Running the Application Locally

### 1. Build Docker Image

```bash
docker build -t hw1-app .
2. Run Container
docker run --rm -p 8080:80 hw1-app
Open in browser:

http://localhost:8080
Deploying to AWS ECS
Push Docker image to Amazon ECR

Create ECS cluster (Fargate)

Create Task Definition

Configure IAM execution role

Configure Security Group (HTTP port 80)

Create Service (1 running task)

Access application via Public IP

Running the Agentic AI Workflow
python3 agents_demo.py --title "Example Title" --content "Example blog content..."
The script outputs:

Planner output

Reviewer output

Final strict JSON

Validation summary

Running the ETL Pipeline
python3 etl_pipeline.py --input data/submissions.jsonl --db db/blog.db
The pipeline:

Extracts blog data

Validates and normalizes fields

Enforces tag and summary constraints

Loads structured records into SQLite

Security Considerations
IAM execution role used for ECS tasks

Public access restricted to HTTP port 80 via Security Groups

No stored API keys or hardcoded credentials

Local LLM processing (no external API exposure)

Structured validation and normalization during ETL phase

Learning Outcomes
This project demonstrates:

End-to-end containerized deployment

AWS cloud infrastructure configuration

Cloud security basics (IAM + security groups)

Multi-agent LLM orchestration

Structured data validation

ETL pipeline design and implementation

Future Improvements
Add HTTPS via Application Load Balancer

Persist blog submissions to cloud database (RDS/DynamoDB)

Add authentication layer

Automate deployment with CI/CD pipeline

Add monitoring and logging

Author
Sharan P
