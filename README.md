# AgentDx - Multi-Specialist Medical Diagnostic Assistant

A **Streamlit-based interactive medical consultation system** that simulates multi-specialist medical diagnoses. It uses an agent-based workflow to assess patient reports and (optionally) medical images, providing structured analyses from relevant specialists, and consolidating them into a **comprehensive final report**.

## Features

- **General Practitioner (GP) Triage** – Initial holistic assessment to determine required specialists.
- **Multi-Specialist Analysis** – Routes the patient case to relevant specialists (e.g., Cardiologist, Neurologist, Radiologist, etc.).
- **Dynamic Workflow Routing** – Uses conditional logic to determine next steps based on earlier findings.
- **Medical Image Handling** – Optionally analyzes uploaded medical images alongside text reports.
- **Consolidated Summary** – Generates a structured, concise, professional final report.
- **Interactive UI** – User-friendly Streamlit interface with sidebar input and tabbed results.

## Specialists Supported

The system currently supports over **25 medical specializations**, including:

- Cardiologist, Neurologist, Pulmonologist, Nephrologist  
- Oncologist, Radiation Oncologist, Gynecologist  
- Orthopaedician, Rheumatologist, Gastroenterologist  
- Psychiatrist, Psychologist, Pain Management Specialist  
- Radiologist, Ophthalmologist, ENT, Dentist  
- Dermatologist, Urologist, Hepatologist, Dietician, Allergist, Endocrinologist  
- Neurosurgeon, Interventional Cardiologist  

## How It Works

1. **User Input** – Patient symptoms/history entered as free text, optional medical image upload.
2. **Initial GP Assessment** – Identifies key findings and recommends relevant specialists.
3. **Specialist Consultations** – Sequentially gathers detailed structured reports from each recommended specialist.
4. **Final Summary** – Consolidates all specialist findings into a single actionable report.

## Technology Stack

- **Frontend**: Streamlit for UI and interactivity
- **Backend Logic**: Python agent workflow powered by `langgraph`
- **Image Processing**: Pillow (`PIL`)
- **Networking**: `requests` for API calls
- **Data Handling**: JSON, Regex, Python Standard Libraries

