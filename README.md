# RoadOps AI

**A maintenance operations intelligence platform built with Microsoft Power Platform, Python, Streamlit, and local generative AI.**

RoadOps AI is an independent portfolio project that demonstrates how digital tools can simplify maintenance reporting, automate notifications, visualize operations, and provide AI-assisted access to information.

The project uses fictional road maintenance data and is not affiliated with or deployed by a real maintenance company.

## Features

### Maintenance Work Order Management
- Create and edit maintenance records through Microsoft Power Apps.
- Store work orders in a SharePoint list.
- Capture equipment issues, priority levels, site information, and work-order status.

### Workflow Automation
- Power Automate monitors newly created SharePoint work orders.
- High-priority work orders trigger an automated email notification.

### Maintenance Analytics
- Power BI dashboard for work-order status, priority, site and estimated costs.
- Python and Streamlit dashboard for interactive maintenance analytics.
- Searchable and filterable work-order explorer.

### AI Maintenance Assistant
- Local inference using Ollama and Qwen 2.5 3B.
- Retrieval-Augmented Generation (RAG) using a maintenance knowledge file.
- CSV-based work-order lookups for counts, priorities, and record statuses.
- Conversational answers to maintenance-related questions.

## Technology Stack

| Technology | Purpose |
|---|---|
| Microsoft Power Apps | Maintenance request interface |
| SharePoint Lists | Work-order data storage |
| Power Automate | High-priority email automation |
| Power BI | Operational analytics |
| Python | Data processing and application logic |
| Streamlit | Web dashboard and chatbot interface |
| Ollama + Qwen 2.5 3B | Local language model inference |
| Pandas | CSV data analysis |

## Architecture

**Microsoft Power Platform workflow**

Power Apps → SharePoint List → Power Automate notifications

SharePoint data → Power BI dashboard

**Python AI workflow**

SharePoint CSV export → Pandas → Streamlit dashboard and work-order queries

Maintenance knowledge file → Keyword retriever → Qwen model → Streamlit AI assistant

The Python application currently uses a manually exported CSV snapshot rather than a live Microsoft Graph connection.

## Getting Started

**Prerequisites:** Python 3.10+, Git, Ollama, and the Qwen 2.5 3B model.

1. Clone the repository and open its folder.
2. Create a virtual environment using `python3 -m venv .venv`.
3. Activate it with `source .venv/bin/activate` on macOS or Linux.
4. Install dependencies using `python -m pip install -r requirements.txt`.
5. Install Ollama and run `ollama pull qwen2.5:3b`.
6. Start Ollama, if it is not already running.
7. Add your own fictional SharePoint-compatible CSV as `data/workorders.csv`.
8. Start the application using `python -m streamlit run app.py`.

The application expects CSV columns including `Title`, `Site`, `AssetType`, `IssueType`, `Priority`, `Status`, and `EstimatedCostCAD`. Additional columns support detailed work-order information.

## Project Status

- Completed: Power Apps work-order interface
- Completed: SharePoint-backed records
- Completed: Power Automate high-priority email workflow
- Completed: Power BI maintenance dashboard
- Completed: Local Streamlit operations dashboard
- Completed: Qwen-powered assistant with basic keyword RAG
- Completed: Work-order questions using exported CSV data
- Future improvement: Authorized live SharePoint API integration
- Future improvement: Semantic document retrieval using embeddings
- Future improvement: Authentication, authorization, testing and production deployment

## Limitations

This is an educational demonstration, not a production maintenance or safety system.

The AI assistant cannot directly update SharePoint records, and the exported CSV requires manual refresh. Keyword retrieval may select irrelevant documents, and generated answers should not be treated as authoritative safety instructions.

The Microsoft Power Platform components require a separately configured Microsoft 365 environment and are not automatically deployed by the Python repository.

## About

Built as an independent computer science portfolio project to explore workflow automation, enterprise data integration, analytics, and generative AI.

**Project type:** Personal portfolio / educational demonstration.