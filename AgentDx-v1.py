import streamlit as st
import threading, re, os
from PIL import Image, UnidentifiedImageError
# import torch # Not used in the current code snippet
from langgraph.graph import StateGraph
from typing import Dict, Any, List, Set
import requests, io, time
import uuid
import json # Added for parsing JSON responses

conversation_id = str(uuid.uuid4())

def generate_response(prompt, images=None):
    api_url = "YOUR_API_URL"
    auth_token = "YOUR_AUTH_TOKEN"

    headers = {"Authorization": f"Bearer {auth_token}"}
    files = {}
    processed_image_bytes_io = None  # To store the BytesIO object for later closing

    if images:  # images is expected to be a List[Image.Image]
        try:
            # Process the first image in the list if the list is not empty
            image_to_process = images[0]
            
            if not isinstance(image_to_process, Image.Image):
                error_msg = f"Error: Expected a PIL Image, but got {type(image_to_process)}"
                print(error_msg)
                yield error_msg
                return

            processed_image_bytes_io = io.BytesIO()
            image_to_process.save(processed_image_bytes_io, format="PNG")
            processed_image_bytes_io.seek(0)
            files["file"] = ("image.png", processed_image_bytes_io.getvalue(), "image/png")
        
        except IndexError: # images list was empty
            # This case should ideally be handled by `if images:` being false for an empty list.
            # If `images` could be an empty list and `if images:` still true, this handles `images[0]`.
            # However, Python's `if []:` is False. So `if images:` correctly guards.
            # This is more of a safeguard if `images` was not empty but `images[0]` failed.
            print("Error: Image list was empty or image could not be accessed.")
            # No yield here, as no image will be sent.
        except Exception as e:
            error_msg = f"Error processing image: {e}"
            print(error_msg)
            if processed_image_bytes_io:
                processed_image_bytes_io.close()
                processed_image_bytes_io = None # Avoid closing again in finally
            yield error_msg
            return

    data = {"text": prompt, "conversation_id": conversation_id}
    
    response_obj = None
    accumulated_response_text = ""

    try:
        response_obj = requests.post(api_url, headers=headers, files=files, data=data, stream=True)
        response_obj.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        for line in response_obj.iter_lines(decode_unicode=True):
            if line:  # Filter out empty lines (e.g., keep-alive newlines)
                try:
                    json_chunk = json.loads(line)
                    if isinstance(json_chunk, dict) and json_chunk.get("type") == "text":
                        content_piece = json_chunk.get("content", "")
                        if content_piece:  # Only process if content is not empty
                            accumulated_response_text += content_piece
                            yield content_piece  # Yield content_piece for streaming
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from line: '{line}'")
                    # Optionally, yield the raw line or a warning message if needed
                    # yield f"[Warning: Malformed data received]"
        
        # This return is part of the generator protocol. It's the value associated
        # with StopIteration when the generator is exhausted.
        return accumulated_response_text

    except requests.exceptions.RequestException as e:
        error_msg = f"Error: API request failed. {e}"
        print(error_msg)
        yield error_msg # Yield an error message for the UI
        # The generator will terminate after this yield.
    finally:
        if response_obj:
            response_obj.close()
        if processed_image_bytes_io:
            processed_image_bytes_io.close()


# Specialist Agent Definitions
def gynecologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a gynecologist, provide a detailed analysis of this case:

Medical Information:
{report}

Please provide your assessment in the following structured format:

1. RELEVANT GYNECOLOGICAL FINDINGS:
- List key symptoms and findings related to reproductive health
- Note any menstrual, hormonal, or reproductive system concerns

2. DIFFERENTIAL DIAGNOSIS:
- List possible gynecological conditions in order of likelihood

3. RECOMMENDED TESTS:
- Specify any required gynecological examinations or tests

4. TREATMENT RECOMMENDATIONS:
- Provide specific treatment options and recommendations
- Include any lifestyle modifications if applicable

5. FOLLOW-UP PLAN:
- Recommend follow-up timeline and monitoring requirements

Please be specific, concise, and focus only on gynecological aspects."""

    #response = generate_response(prompt.format(report=report), images)
    # Get streaming response and accumulate it
    #st.subheader("Gynaecologist's Assessment")
    full_response = "### Gynaecologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Gynecologist", "analysis": full_response})
    return state

def neurosurgeon_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a neurosurgeon, provide a detailed analysis of this case:
Medical Information:
{report}
Please provide your assessment in the following structured format:
1. NEUROLOGICAL SURGICAL FINDINGS:
- List key neurological symptoms requiring surgical intervention
- Note any structural abnormalities or lesions
- Evaluate severity and surgical urgency
2. DIFFERENTIAL DIAGNOSIS:
- List possible neurosurgical conditions in order of likelihood
- Identify conditions requiring immediate surgical intervention
3. RECOMMENDED TESTS:
- Specify required imaging studies (MRI, CT, angiogram)
- List necessary pre-operative assessments
4. TREATMENT RECOMMENDATIONS:
- Detail surgical approach and technique
- Outline risks and benefits of surgical intervention
- Include alternative treatment options if applicable
5. FOLLOW-UP PLAN:
- Specify post-operative care requirements
- Define rehabilitation protocol
- Set timeline for follow-up visits
Please be specific, concise, and focus only on neurosurgical aspects."""
    #st.subheader("Neurosurgeon's Assessment")
    full_response = "### Neurosurgeon's Assessment\n\n"

    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()

    state["agent_results"].append({"specialist": "Neurosurgeon", "analysis": full_response})
    return state

def radiation_oncologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a radiation oncologist, provide a detailed analysis of this case:
Medical Information:
{report}
Please provide your assessment in the following structured format:
1. ONCOLOGICAL FINDINGS:
- Evaluate tumor characteristics and staging
- Assess radiation therapy candidacy
- Note any previous radiation exposure
2. DIFFERENTIAL DIAGNOSIS:
- List possible radiotherapy-responsive conditions
- Evaluate tumor radio-sensitivity
3. RECOMMENDED TESTS:
- Specify required imaging for treatment planning
- Detail necessary radiation dose calculations
- List required pre-treatment assessments
4. TREATMENT RECOMMENDATIONS:
- Define radiation therapy protocol
- Specify dose fractionation schedule
- Detail radiation delivery technique
- Include supportive care measures
5. FOLLOW-UP PLAN:
- Set radiation therapy monitoring schedule
- Define post-treatment imaging timeline
- Specify long-term monitoring requirements
Please be specific, concise, and focus only on radiation oncology aspects."""
    #st.subheader("Radiation Oncologist's Assessment")
    full_response = "### Radiation Oncologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Radiation Oncologist", "analysis": full_response})
    return state

def psychiatrist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a psychiatrist, provide a detailed analysis of this case:
Medical Information:
{report}
Please provide your assessment in the following structured format:
1. PSYCHIATRIC FINDINGS:
- List key mental health symptoms and behaviors
- Note mood, affect, and cognitive function
- Assess risk factors and safety concerns
2. DIFFERENTIAL DIAGNOSIS:
- List possible psychiatric conditions in order of likelihood
- Consider comorbid conditions
3. RECOMMENDED TESTS:
- Specify required psychological assessments
- List necessary screening tools
- Detail required laboratory tests if applicable
4. TREATMENT RECOMMENDATIONS:
- Outline psychopharmacological interventions
- Detail psychotherapy recommendations
- Include lifestyle and support system modifications
5. FOLLOW-UP PLAN:
- Set therapy session frequency
- Define medication monitoring schedule
- Specify crisis intervention protocol
Please be specific, concise, and focus only on psychiatric aspects."""
    #st.subheader("Psychiatrist's Assessment")
    full_response = "### Psychiatrist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Psychiatrist", "analysis": full_response})
    return state

def interventional_cardiologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As an interventional cardiologist, provide a detailed analysis of this case:
Medical Information:
{report}
Please provide your assessment in the following structured format:
1. CARDIOVASCULAR FINDINGS:
- List key cardiac symptoms requiring intervention
- Note coronary anatomy and lesion characteristics
- Evaluate hemodynamic status
2. DIFFERENTIAL DIAGNOSIS:
- List possible conditions requiring cardiac intervention
- Assess urgency of intervention
3. RECOMMENDED TESTS:
- Specify required cardiac catheterization studies
- Detail necessary pre-procedure imaging
- List required pre-intervention assessments
4. TREATMENT RECOMMENDATIONS:
- Detail interventional approach (PCI, structural intervention)
- Specify device and technique selection
- Include antiplatelet/anticoagulation strategy
- Note post-procedure care requirements
5. FOLLOW-UP PLAN:
- Define dual antiplatelet therapy duration
- Set follow-up angiogram timeline if needed
- Specify cardiac rehabilitation protocol
Please be specific, concise, and focus only on interventional cardiology aspects."""
    #st.subheader("Interventional Cardiologist's Assessment")
    full_response = "### Interventional Cardiologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Interventional Cardiologist", "analysis": full_response})
    return state

def radiologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a radiologist, provide a detailed analysis of this case:

Medical Information:
{report}

Please structure your response as follows:

1. IMAGING FINDINGS (if images provided):
- Detailed description of any visible abnormalities
- Image quality and technical adequacy
- Comparison with any prior studies mentioned

2. INTERPRETATION:
- Systematic analysis of findings
- Anatomical structures involved
- Any concerning features or patterns

3. CLINICAL CORRELATION:
- How findings relate to patient's symptoms
- Potential clinical implications

4. RECOMMENDATIONS:
- Additional imaging studies if needed
- Optimal imaging protocols
- Follow-up imaging timeline

5. CONCLUSION:
- Clear, actionable summary of findings
- Key concerns and their clinical significance

Focus on imaging aspects and maintain radiological perspective throughout."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Radiologist's Assessment")
    full_response = "### Radiologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Radiologist", "analysis": full_response})
    return state

def oncologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As an oncologist, provide a comprehensive cancer risk assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. CANCER RISK ASSESSMENT:
- Evaluation of concerning symptoms/findings
- Risk factors identified
- Family history implications (if mentioned)

2. SUSPICIOUS FINDINGS:
- Analysis of any masses, lesions, or concerning symptoms
- Correlation with imaging (if available)
- Tumor markers or relevant lab values

3. DIFFERENTIAL DIAGNOSIS:
- Potential malignant conditions
- Benign alternatives to consider
- Risk stratification

4. RECOMMENDED WORKUP:
- Specific tests needed for diagnosis
- Biopsy recommendations if applicable
- Staging workup if needed

5. NEXT STEPS:
- Clear action plan
- Timeline for interventions
- Monitoring recommendations

Be precise and evidence-based in your assessment."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Oncologist's Assessment")
    full_response = "### Oncologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Oncologist", "analysis": full_response})
    return state

def pain_management_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a pain management specialist, analyze this case:

Medical Information:
{report}

Provide your assessment in this format:

1. PAIN EVALUATION:
- Pain characteristics (location, intensity, quality)
- Temporal patterns
- Aggravating/alleviating factors
- Impact on daily activities

2. UNDERLYING CAUSES:
- Primary pain generators
- Contributing factors
- Comorbid conditions affecting pain

3. TREATMENT PLAN:
- Immediate pain management strategies
- Long-term pain control options
- Non-pharmacological interventions
- Medication recommendations if needed

4. MONITORING PLAN:
- Pain assessment tools
- Follow-up schedule
- Red flags to watch for

5. LIFESTYLE MODIFICATIONS:
- Activity modifications
- Ergonomic recommendations
- Self-management strategies

Focus on comprehensive pain management approach."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Pain Specialist's Assessment")
    full_response = "### Pain Specialist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Pain Management", "analysis": full_response})
    return state

def gastroenterologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a gastroenterologist, provide a detailed analysis:

Medical Information:
{report}

Structure your response as follows:

1. GI SYMPTOMS ANALYSIS:
- Primary digestive complaints
- Associated symptoms
- Pattern and progression

2. DIFFERENTIAL DIAGNOSIS:
- Potential GI conditions
- Alarm symptoms identified
- Risk stratification

3. DIAGNOSTIC PLAN:
- Recommended GI workup
- Specific tests needed
- Endoscopic evaluation if needed

4. TREATMENT RECOMMENDATIONS:
- Immediate interventions
- Long-term management plan
- Dietary modifications
- Lifestyle changes

5. FOLLOW-UP PLAN:
- Monitoring schedule
- Warning signs to watch
- Criteria for urgent evaluation

Focus on digestive system aspects and related complications."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Gastroenterologist's Assessment")
    full_response = "### Gastroenterologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Gastroenterologist", "analysis": full_response})
    return state

def rheumatologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a rheumatologist, analyze this case:

Medical Information:
{report}

Provide analysis in this format:

1. RHEUMATOLOGICAL ASSESSMENT:
- Joint/muscle symptoms
- Pattern of involvement
- Morning stiffness
- Associated symptoms

2. DIFFERENTIAL DIAGNOSIS:
- Potential rheumatic conditions
- Inflammatory vs non-inflammatory
- Systemic involvement

3. DIAGNOSTIC WORKUP:
- Recommended blood tests
- Imaging studies needed
- Other specialized tests

4. TREATMENT PLAN:
- Anti-inflammatory measures
- Disease-modifying therapy if needed
- Joint protection strategies
- Physical therapy needs

5. MONITORING PLAN:
- Disease activity monitoring
- Complication surveillance
- Follow-up schedule

Focus on musculoskeletal and autoimmune aspects."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Rheumatologist's Assessment")
    full_response = "### Rheumatologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Rheumatologist", "analysis": full_response})
    return state

def psychologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a psychologist, provide a mental health assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. PSYCHOLOGICAL ASSESSMENT:
- Mental status observations
- Mood and affect
- Behavioral patterns
- Impact on daily functioning

2. DIAGNOSTIC CONSIDERATIONS:
- Potential psychological conditions
- Stress factors identified
- Coping mechanisms observed

3. RISK ASSESSMENT:
- Safety concerns
- Support system evaluation
- Coping capacity

4. TREATMENT RECOMMENDATIONS:
- Therapeutic interventions
- Coping strategies
- Lifestyle modifications
- Support resources

5. FOLLOW-UP PLAN:
- Recommended frequency
- Treatment goals
- Progress monitoring

Focus on psychological aspects and their interaction with physical symptoms."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Psychologist's Assessment")
    full_response = "### Psychologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Psychologist", "analysis": full_response})
    return state

def dentist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a dentist, provide a comprehensive dental analysis:

Medical Information:
{report}

Structure your assessment as follows:

1. DENTAL FINDINGS:
- Oral symptoms and complaints
- Dental pain characteristics
- Oral hygiene status
- Relevant medical history impact

2. DIAGNOSTIC ASSESSMENT:
- Potential dental conditions
- Oral health impact
- Complications risk

3. TREATMENT NEEDS:
- Immediate interventions required
- Preventive measures
- Long-term dental care plan

4. RECOMMENDATIONS:
- Specific dental procedures
- Oral hygiene instructions
- Dietary recommendations

5. FOLLOW-UP PLAN:
- Treatment timeline
- Monitoring schedule
- Emergency care criteria

Focus on oral health aspects and their systemic implications."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Dentist's Assessment")
    full_response = "### Dentist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)

    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Dentist", "analysis": full_response})
    return state


def orthopaedician_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As an orthopedic specialist, provide a detailed assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. MUSCULOSKELETAL ASSESSMENT:
- Location and nature of complaints
- Pain characteristics
- Movement limitations
- Associated symptoms

2. PHYSICAL FINDINGS:
- Range of motion
- Strength assessment
- Neurological aspects
- Gait analysis if relevant

3. DIFFERENTIAL DIAGNOSIS:
- Potential orthopedic conditions
- Injury patterns if applicable
- Degenerative considerations

4. TREATMENT PLAN:
- Immediate interventions
- Physical therapy needs
- Surgical considerations
- Assistive devices if needed

5. REHABILITATION PLAN:
- Exercise recommendations
- Activity modifications
- Recovery timeline
- Return to activity goals

Focus on musculoskeletal system and functional improvement."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Orthopaedician's Assessment")
    full_response = "### Orthopaedician's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Orthopaedician", "analysis": full_response})
    return state

def opthamologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As an ophthalmologist, provide a comprehensive eye assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. VISION ASSESSMENT:
- Visual symptoms
- Vision changes
- Eye pain or discomfort
- Associated symptoms

2. CLINICAL FINDINGS:
- Visual acuity concerns
- External eye examination
- Retinal considerations
- Neurological aspects

3. DIFFERENTIAL DIAGNOSIS:
- Potential eye conditions
- Vision threatening concerns
- Systemic disease impact

4. TREATMENT RECOMMENDATIONS:
- Immediate interventions
- Vision correction needs
- Medical/surgical options
- Preventive measures

5. FOLLOW-UP PLAN:
- Monitoring schedule
- Vision testing needs
- Emergency warning signs
- Vision protection strategies

Focus on ocular health and vision preservation."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Opthamologist's Assessment")
    full_response = "### Opthamologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Opthamologist", "analysis": full_response})
    return state

def cardiologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a cardiologist, provide a comprehensive cardiac assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. CARDIOVASCULAR ASSESSMENT:
- Cardiac symptoms
- Risk factors present
- Exercise tolerance
- Associated symptoms

2. CLINICAL CORRELATION:
- Cardiovascular findings
- Hemodynamic status
- Related systemic effects
- Risk stratification

3. DIFFERENTIAL DIAGNOSIS:
- Potential cardiac conditions
- Non-cardiac considerations
- Risk assessment

4. MANAGEMENT PLAN:
- Immediate interventions
- Medication recommendations
- Lifestyle modifications
- Risk factor management

5. MONITORING PLAN:
- Follow-up schedule
- Testing requirements
- Warning signs
- Prevention strategies

Focus on cardiovascular health and risk management."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Cardiologist's Assessment")
    full_response = "### Cardiologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Cardiologist", "analysis": full_response})
    return state

def neurologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a neurologist, provide a comprehensive neurological assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. NEUROLOGICAL ASSESSMENT:
- Mental status and consciousness
- Cranial nerve functions
- Motor system evaluation
- Sensory system findings
- Coordination and balance
- Reflexes and gait

2. SYMPTOM ANALYSIS:
- Temporal progression
- Pattern recognition
- Associated symptoms
- Aggravating/alleviating factors
- Impact on daily functioning

3. DIFFERENTIAL DIAGNOSIS:
- Primary neurological conditions
- Secondary neurological manifestations
- Urgent neurological concerns
- Systemic conditions with neurological impact

4. DIAGNOSTIC PLAN:
- Neuroimaging recommendations
- Neurophysiological studies needed
- Laboratory tests required
- Specialized neurological testing

5. TREATMENT RECOMMENDATIONS:
- Immediate interventions
- Medical management
- Preventive measures
- Rehabilitation needs
- Lifestyle modifications

6. FOLLOW-UP PLAN:
- Monitoring schedule
- Warning signs to watch
- Emergency action plan
- Long-term management strategy

Focus on nervous system function and neurological manifestations."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Neurologist's Assessment")
    full_response = "### Neurologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Neurologist", "analysis": full_response})
    return state

def nephrologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a nephrologist, provide a detailed renal assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. RENAL ASSESSMENT:
- Kidney function indicators
- Urinary symptoms
- Fluid status evaluation
- Blood pressure patterns
- Electrolyte balance
- Related systemic symptoms

2. RISK FACTOR ANALYSIS:
- Predisposing conditions
- Medication effects
- Family history impact
- Environmental factors
- Comorbidity influence

3. DIFFERENTIAL DIAGNOSIS:
- Primary kidney conditions
- Secondary renal involvement
- Acute vs. chronic considerations
- Systemic diseases affecting kidneys

4. DIAGNOSTIC WORKUP:
- Laboratory tests needed
- Imaging studies required
- Specialized renal testing
- Monitoring parameters

5. TREATMENT PLAN:
- Immediate interventions
- Medication adjustments
- Dietary recommendations
- Fluid management
- Blood pressure control

6. FOLLOW-UP STRATEGY:
- Monitoring frequency
- Key parameters to track
- Complications to watch
- Prevention strategies

Focus on renal function and systemic implications."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Nephrologist's Assessment")
    full_response = "### Nephrologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Nephrologist", "analysis": full_response})
    return state

def pulmonologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a pulmonologist, provide a comprehensive respiratory assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. RESPIRATORY ASSESSMENT:
- Breathing patterns
- Respiratory symptoms
- Exercise tolerance
- Sleep-related symptoms
- Environmental factors
- Associated systemic symptoms

2. PHYSICAL FINDINGS:
- Respiratory rate and effort
- Breath sounds
- Chest wall movement
- Oxygen saturation
- Use of accessory muscles
- Signs of respiratory distress

3. DIFFERENTIAL DIAGNOSIS:
- Primary lung conditions
- Airway diseases
- Parenchymal disorders
- Vascular lung disease
- Pleural conditions
- Systemic diseases with pulmonary involvement

4. DIAGNOSTIC PLAN:
- Pulmonary function testing
- Imaging requirements
- Blood gas analysis
- Sleep studies if needed
- Specialized respiratory testing

5. TREATMENT RECOMMENDATIONS:
- Immediate interventions
- Inhalation therapy
- Oxygen requirements
- Medical management
- Pulmonary rehabilitation
- Lifestyle modifications

6. FOLLOW-UP PROTOCOL:
- Monitoring schedule
- Home monitoring needs
- Warning signs
- Emergency action plan
- Long-term management strategy

Focus on respiratory function and systemic impact."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Pulmonologist's Assessment")
    full_response = "### Pulmonologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Pulmonologist", "analysis": full_response})
    return state

def ent_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As an ENT (Otolaryngologist), provide a comprehensive assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. ENT ASSESSMENT:
- Ear symptoms and findings
- Nose and sinus evaluation
- Throat and larynx status
- Head and neck examination
- Hearing and balance issues
- Voice and swallowing function

2. SYMPTOM ANALYSIS:
- Duration and progression
- Impact on daily activities
- Associated symptoms
- Aggravating/alleviating factors
- Previous treatments tried

3. DIFFERENTIAL DIAGNOSIS:
- Ear-related conditions
- Nasal/sinus pathologies
- Throat/laryngeal issues
- Head and neck concerns
- Systemic conditions affecting ENT

4. DIAGNOSTIC PLAN:
- Audiological testing needs
- Imaging requirements
- Endoscopic evaluation
- Special ENT investigations
- Laboratory tests

5. TREATMENT RECOMMENDATIONS:
- Immediate interventions
- Medical management
- Surgical considerations
- Preventive measures
- Voice/speech therapy needs

6. FOLLOW-UP PROTOCOL:
- Monitoring schedule
- Warning signs
- Hearing protection strategies
- Lifestyle modifications

Focus on ear, nose, throat, and related structures."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("ENT's Assessment")
    full_response = "### ENT's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "ENT", "analysis": full_response})
    return state

def allergist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As an allergist/immunologist, provide a detailed assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. ALLERGY ASSESSMENT:
- Allergic symptoms
- Trigger patterns
- Environmental factors
- Seasonal variations
- Impact on quality of life
- Family history of allergies

2. IMMUNE SYSTEM EVALUATION:
- History of infections
- Autoimmune manifestations
- Immune response patterns
- Vaccination history
- Previous allergy testing

3. DIFFERENTIAL DIAGNOSIS:
- Type of allergic conditions
- Non-allergic considerations
- Immune system disorders
- Cross-reactivity patterns
- Secondary complications

4. DIAGNOSTIC PLAN:
- Skin testing requirements
- Blood tests needed
- Challenge testing considerations
- Environmental assessment
- Immunological workup

5. TREATMENT STRATEGIES:
- Immediate relief measures
- Long-term management
- Immunotherapy options
- Environmental control
- Emergency protocols

6. PREVENTIVE PLAN:
- Trigger avoidance strategies
- Diet modifications
- Environmental controls
- Action plan for reactions
- Follow-up schedule

Focus on allergic conditions and immune system function."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Allergist's Assessment")
    full_response = "### Allergist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Allergist", "analysis": full_response})
    return state

def endocrinologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As an endocrinologist, provide a comprehensive hormonal assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. ENDOCRINE ASSESSMENT:
- Hormone-related symptoms
- Metabolic status
- Growth and development
- Energy levels
- Weight changes
- Temperature regulation

2. SYSTEM-SPECIFIC EVALUATION:
- Thyroid function
- Adrenal status
- Glucose metabolism
- Reproductive hormones
- Calcium homeostasis
- Pituitary function

3. DIFFERENTIAL DIAGNOSIS:
- Primary endocrine disorders
- Secondary endocrine conditions
- Metabolic complications
- Related systemic diseases
- Medication effects

4. DIAGNOSTIC WORKUP:
- Hormone level testing
- Dynamic testing needs
- Imaging requirements
- Metabolic evaluation
- Genetic testing considerations

5. TREATMENT PLAN:
- Hormone replacement needs
- Metabolic management
- Lifestyle modifications
- Dietary adjustments
- Medication recommendations

6. MONITORING PROTOCOL:
- Hormone level monitoring
- Metabolic tracking
- Complication surveillance
- Follow-up schedule
- Emergency protocols

Focus on endocrine system function and metabolic health."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Endocrinologist's Assessment")
    full_response = "### Endocrinologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Endocrinologist", "analysis": full_response})
    return state

def dermatologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a dermatologist, provide a detailed skin assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. SKIN ASSESSMENT:
- Lesion characteristics
- Distribution pattern
- Color changes
- Texture alterations
- Associated symptoms
- Skin appendage status

2. SYMPTOM ANALYSIS:
- Onset and progression
- Triggering factors
- Previous treatments
- Impact on daily life
- Associated conditions

3. DIFFERENTIAL DIAGNOSIS:
- Primary skin conditions
- Secondary skin manifestations
- Systemic diseases with cutaneous signs
- Infectious considerations
- Allergic reactions

4. DIAGNOSTIC PLAN:
- Skin examination findings
- Biopsy requirements
- Patch testing needs
- Laboratory workup
- Imaging considerations

5. TREATMENT RECOMMENDATIONS:
- Topical treatments
- Systemic medications
- Procedural interventions
- Skincare routine
- Preventive measures

6. FOLLOW-UP PROTOCOL:
- Monitoring schedule
- Photography documentation
- Skin protection strategy
- Warning signs
- Prevention plan

Focus on skin, hair, nails, and related structures."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Dermatologist's Assessment")
    full_response = "### Dermatologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Dermatologist", "analysis": full_response})
    return state

def urologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a urologist, provide a comprehensive urological assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. UROLOGICAL ASSESSMENT:
- Urinary symptoms
- Sexual health concerns
- Prostate status (if male)
- Pelvic symptoms
- Pain evaluation
- Related systemic symptoms

2. FUNCTIONAL EVALUATION:
- Voiding patterns
- Continence status
- Sexual function
- Pelvic floor status
- Quality of life impact

3. DIFFERENTIAL DIAGNOSIS:
- Urological conditions
- Anatomical considerations
- Functional disorders
- Oncological concerns
- Systemic disease impact

4. DIAGNOSTIC PLAN:
- Urinalysis needs
- Imaging studies
- Functional testing
- Cystoscopy considerations
- Laboratory workup

5. TREATMENT RECOMMENDATIONS:
- Medical management
- Surgical options
- Behavioral modifications
- Pelvic floor therapy
- Lifestyle changes

6. FOLLOW-UP PROTOCOL:
- Monitoring schedule
- PSA tracking (if male)
- Symptom diary needs
- Warning signs
- Prevention strategy

Focus on urological system and related functions."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Urologist's Assessment")
    full_response = "### Urologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Urologist", "analysis": full_response})
    return state

def hepatologist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a hepatologist, provide a detailed liver assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. LIVER ASSESSMENT:
- Liver-related symptoms
- Portal system status
- Metabolic factors
- Nutritional status
- Associated symptoms
- Risk factors present

2. SYSTEMIC EVALUATION:
- Hepatic manifestations
- Extra-hepatic signs
- Complications present
- Impact on other systems
- Quality of life effects

3. DIFFERENTIAL DIAGNOSIS:
- Primary liver conditions
- Secondary liver involvement
- Metabolic liver disease
- Vascular disorders
- Systemic conditions

4. DIAGNOSTIC WORKUP:
- Liver function tests
- Imaging requirements
- Fibroscan needs
- Biopsy considerations
- Additional testing

5. TREATMENT PLAN:
- Immediate interventions
- Long-term management
- Nutritional support
- Medication adjustments
- Lifestyle modifications

6. MONITORING PROTOCOL:
- Lab monitoring schedule
- Imaging follow-up
- Complication surveillance
- Warning signs
- Prevention strategies

Focus on liver function and related systems."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Hepatologist's Assessment")
    full_response = "### Hepatologist's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Hepatologist", "analysis": full_response})
    return state

def dietician_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    report = state["report"]
    images = state.get("images")
    prompt = """As a dietitian, provide a comprehensive nutritional assessment:

Medical Information:
{report}

Structure your analysis as follows:

1. NUTRITIONAL ASSESSMENT:
- Current dietary patterns
- Nutritional status
- Weight history
- Eating behaviors
- Dietary restrictions
- Nutritional deficiencies

2. METABOLIC EVALUATION:
- Energy requirements
- Macro/micronutrient needs
- Hydration status
- Metabolic conditions
- Impact of medications

3. DIETARY ANALYSIS:
- Current diet composition
- Eating patterns
- Food allergies/intolerances
- Cultural considerations
- Lifestyle factors

4. NUTRITIONAL DIAGNOSIS:
- Nutritional deficiencies
- Dietary imbalances
- Eating patterns
- Related medical conditions
- Lifestyle impact

5. INTERVENTION PLAN:
- Dietary modifications
- Meal planning
- Supplement recommendations
- Behavior modification
- Educational needs

6. MONITORING PROTOCOL:
- Weight tracking
- Dietary compliance
- Nutrient monitoring
- Progress evaluation
- Follow-up schedule

Focus on nutritional status and dietary management."""

    #response = generate_response(prompt.format(report=report), images)
    #st.subheader("Dietician's Assessment")
    full_response = "### Dietician's Assessment\n\n"
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["agent_results"].append({"specialist": "Dietician", "analysis": full_response})
    return state

def gp_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    GP agent analyzes medical history and determines which specialists to consult based on LLM output.
    Now with improved parsing and robust specialist detection.
    """
    report = state["report"]
    images = state.get("images")
    prompt ="""
You are a General Practitioner (GP) conducting a comprehensive patient assessment. Your task is to synthesize the provided medical history, current symptoms, and imaging findings (if available) to deliver structured clinical recommendations. You must prioritize clinically relevant specialist referrals based on the following hierarchy:
1. **Symptoms**: Determine the initial specialist(s) based on the patient's chief complaints and active symptoms.
2. **Medical History**: Identify additional specialists based on pre-existing conditions, chronic diseases, or risk factors.
3. **Imaging Findings**: Refine the referral list by including specialists who can address abnormalities detected in medical images.

**Key Considerations:**
1. **Holistic Correlation:**  
   - Explicitly link current symptoms to historical conditions AND imaging abnormalities (if present).  
   - Ensure findings from all sources (history, symptoms, and imaging) are integrated into the analysis.
			- Include all possible specialists based on the findings and analysis

2. **Image Rigor (If Imaging is Provided):**  
   - Perform a systematic analysis of the medical image before drawing conclusions by following the below approach:  
     - Classify the image by what you see.  
     - Identify all the key elements seen in the image.  
     - Extract all visible textual information in the image, including person identifiers, dates, labels (e.g., "L" and "R" for side indicators, annotations, or clinical notes), and all textual information. These will be your additional context that you need to factor in during your image analysis.  
     - Factor in relevant filename information if it provides context (e.g., modality, body region, patient identifiers, or clinical hints). If it is not in English, please translate to English to understand the same. Ignore filenames without meaningful information.  
     - Validate all user-provided information independently and avoid relying solely on it. Prioritize your analysis by examining the content and context of the image itself, including text within the image, visual elements, and any meaningful information derived from the image's file name. Focus on objective and evidence-based conclusions over user-supplied narratives or descriptions.  
     - Exercise caution when determining the sides of organs in medical images. Always prioritize labels within the image, if present, to identify left or right. If labels are not available, interpret the image based on the imaging modality's standard conventions (e.g., as viewed in radiology, left and right are from the patient's perspective, not the viewer's). Avoid assumptions based on the user's perspective or description.  
     - List all the key findings and interpret them individually for a complete understanding of this image.  
     - Determine their relevance to symptoms.  
     - Ensure findings contribute to specialist recommendations.  
     - Include radiologist in the list of required specialists if the provided image is a medical image.  
     - Treat image-derived findings as independent clinical evidence.  
     - Require specialist referral for any actionable imaging findings.

3. **Referral Precision:**  
   - Follow this hierarchical approach to determine specialists:  
     1. **Symptoms**: Start by identifying specialists based on the patient's chief complaints and active symptoms.  
     2. **Medical History**: Expand the list by considering pre-existing conditions, chronic diseases, or risk factors.  
     3. **Imaging Findings**: Refine the referral list by including specialists who can address abnormalities detected in medical images.  
   - Always include a radiologist if a medical image is provided.  
   - Map each specialist recommendation to specific findings in BOTH medical history AND imaging.  
   - Prioritize specialists who can address multiple conditions or findings.

---

### **Input Data:**
- **Medical History & Symptoms:** {report}  
- **Medical Imaging:** [Present/Absent]  

---

### **Response Protocol:**
Respond EXACTLY in this format:

---

#### **INITIAL ASSESSMENT:**

1. **Chief Complaints:**  
   - List active symptoms with duration/severity.  
   - Flag symptoms correlating with historical conditions.  

2. **Vital Signs & Physical Examination:**  
   - Report provided metrics OR note absent data.  
   - Highlight abnormal findings requiring monitoring.  

3. **Medical History Analysis:**  
   - For EACH pre-existing condition:  
     - Current stability status.  
     - Direct/exacerbating relationship to active symptoms.  
     - Risk factors for complications.  

4. **Imaging Analysis (ONLY if provided):**  
   - Follow this analytical sequence:  
     1. **Technical Assessment:**  
        - Modality/body region from metadata.  
        - Quality assessment (diagnostic utility).  
     2. **Content Analysis:**  
        - Anatomical structures visualized.  
        - Pathological findings with location/size.  
        - Textual markers (labels, annotations, L/R markers).  
     3. **Clinical Integration:**  
        - Differentiate acute vs chronic findings.  
        - Relate abnormalities to active symptoms.  
        - Identify findings requiring specialist review.  

5. **Initial Diagnosis:**  
   - Problem list formatted as:  
     - [Acute Condition] (Urgency Level).  
     - [Chronic Condition Exacerbation].  
     - [Imaging-Derived Finding] (if applicable).  
   - Flag critical diagnostic uncertainties.  

6. **Immediate Actions:**  
   - First-line pharmacological interventions.  
   - Safety-net advice for symptom escalation.  
   - Essential monitoring parameters.  

7. **Initial Management Plan:**  
   - Structured as:  
     - **Diagnostics:** Required tests with prioritization.  
     - **Therapeutics:** Medication adjustments.  
     - **Lifestyle:** Specific behavioral modifications.  

---

#### **REQUIRED SPECIALISTS:**
[List ONLY THE TOP 3 MOST CRITICAL SPECIALISTS using EXACTLY these specializations ]  
- gynecologist																		- oncologist            - psychiatrist
- pain_management															- gastroenterologist    - rheumatologist  
- psychologist																		- dentist               - orthopaedician  
- opthamologist																	- cardiologist          - neurologist  
- nephrologist																		- pulmonologist         - ent  
- allergist																					- endocrinologist       - dermatologist  
- urologist																					- hepatologist          - dietician  
- neurosurgeon																		- radiation_oncologist  
- interventional_cardiologist

If no specialists needed: REQUIRED SPECIALISTS: none  

---

#### **REFERRAL JUSTIFICATION:**
For EACH specialist:  
- Specific historical condition requiring their input.  
- Active symptom(s) needing their expertise.  
- Imaging finding(s) requiring review (if applicable).  
- Expected clinical outcome from consultation.  
    """    
    # Initialize full response
    #print("\n***GP's Initial Assessment***:")
    response_placeholder = st.empty()    
    #response_placeholder.subheader("General Practitioner's Initial Assessment")

    # Get streaming response and accumulate it
    response_generator = generate_response(prompt.format(report=report), images)
    full_response = "### General Practitioner's Initial Assessment\n\n"
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    #    #print(chunk, end='', flush=True)
    #    yield chunk
    response_placeholder.empty()
    # Store GP's analysis
    state["agent_results"].append({
        "specialist": "General Practitioner",
        "analysis": full_response
    })
    print("GP Agent Full response ",full_response)
    # Specialist name mappings for detection
    # "radiologist": ["radiologist", "radiological", "radiology"],
    specialist_mappings = {
        "gynecologist": ["gynecologist", "gynaecologist", "ob-gyn", "menstrual cramp"],
        "oncologist": ["oncologist"],
        "pain_management": ["pain management", "pain specialist"],
        "gastroenterologist": ["gastroenterologist", "gastrointestinal specialist", "gi specialist", "abdominal cramp", "stomach cramp"],
        "rheumatologist": ["rheumatologist"],
        "psychologist": ["psychologist"],
        "dentist": ["dentist","oral"],
        "orthopaedician": ["orthopaedician", "orthopedician", "muscle cramp", "leg cramp"],
        "opthamologist": ["opthamologist", "ophthalmologist"],
        "cardiologist": ["cardiologist", "cardiac specialist", "cardio","heart","chest"],
        "neurologist": ["neurologist","neuro"],
        "nephrologist": ["nephrologist", "kidney specialist", "nephro"],
        "pulmonologist": ["pulmonologist"],
        "ent": ["ent specialist", "ear nose throat specialist", "ear nose and throat", "otolaryngologist"],
        "allergist": ["allergist"],
        "endocrinologist": ["endocrinologist"],
        "dermatologist": ["dermatologist"],
        "urologist": ["urologist"],
        "hepatologist": ["hepatologist"],
        "dietician": ["dietician", "dietitian", "nutritionist","food specialist"],
        "neurosurgeon": ["neurosurgeon","neuro surgeon"],
        "radiation_oncologist":["radiation oncologist"],  
        "psychiatrist": ["psychiatrist"],
        "interventional_cardiologist":["interventional cardiologist","interventional_cardiologist"]
    }

    try:
        # Extract the REQUIRED SPECIALISTS section using regex
        response_lower = full_response.lower()

        # Extract the REQUIRED SPECIALISTS section using regex
        match = re.search(r"required specialists:.*?(?=\n---|\Z)", response_lower, re.DOTALL | re.IGNORECASE)
        if match:
              specialist_section = match.group(0)
              print("Extracted specialist section:", specialist_section) 
        else:
              specialist_section = response_lower
              print("Failed to extract specialist section, using full response")

        # Extract specialists from the section
        required_specialists = set()
        for standard_name, variations in specialist_mappings.items():
              for variant in variations:
                  # Use word boundaries to ensure exact matches
                  if re.search(rf"\b{re.escape(variant)}\b", specialist_section,re.IGNORECASE):
                        required_specialists.add(standard_name)

								# Always include radiologist if imaging is provided
        if images:  # Assuming `images` is a boolean indicating whether imaging was provided
              required_specialists.add("radiologist")

    except Exception as e:
								print(f"Error in specialist detection: {str(e)}")

    # Store detected specialists
    print("GP Identified Specialists ",required_specialists)
    state["required_specialists"] = list(required_specialists)
    #print("GP State ",state)
    #return specialist_agent(state, "General Physician", prompt_template)
    return state

def summarize_findings(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarize findings from all agents into a consolidated report.
    """
    images = state.get("images")
    report = state["report"]
    combined_analysis = "\n".join([f"{result['specialist']}: {result['analysis']}" 
                                 for result in state["agent_results"]])
    #prompt = f"SUMMARIZE the following specialist analysis into a comprehensive professional medical report in not more than 500 words:\n{combined_analysis}"
    prompt = f"""
You are a highly skilled medical analyst. Your task is to synthesize the following multi-specialist assessments into a **comprehensive, structured, and professional medical report** in no more than 500 words. 

### **Patient Case Summary**
- Extract and summarize key **symptoms, history, and findings** from the assessments.
- Highlight the **most critical conditions or concerns**.
- Clearly differentiate between **acute, chronic, and incidental findings**.

### **Specialist Assessments Included**
{combined_analysis}

### **Required Report Structure**
Your response should follow this format:

**1. Patient Overview:**  
   - Key medical history, presenting symptoms, and clinical concerns.  
   - Relevant imaging or diagnostic findings (if any).  

**2. Specialist Findings & Analysis:**  
   - Summarize core findings from each specialist.  
   - Clearly outline **consistent themes or contradictions** in the assessments.  

**3. Diagnosis & Differential Considerations:**  
   - List **likely diagnoses** based on the collective analysis.  
   - Include differential diagnoses if applicable.  

**4. Recommended Investigations & Tests:**  
   - Prioritized list of any pending diagnostic tests or imaging.  

**5. Treatment Plan & Next Steps:**  
   - Recommended medical, surgical, or therapeutic interventions.  
   - Any **urgent** actions needed.  
   - Follow-up plan and required specialist consultations.  

Ensure your summary is **concise, evidence-based, and actionable** with **no unnecessary repetition**.  
    """  

    #summary = generate_response(prompt,images)
    #st.subheader("FINAL ASSESSMENT REPORT (Summary)")
    response_placeholder = st.empty()    

    response_generator = generate_response(prompt.format(report=report), images)
    #full_response = ""
    full_response = "### FINAL ASSESSMENT REPORT (Summary)\n\n"
    for chunk in response_generator:
        full_response += chunk
        response_placeholder.markdown(full_response)
    response_placeholder.empty()
    state["final_report"] = full_response
    return state


def route_to_specialists(state: Dict[str, Any]) -> str:
    """
    Determines the next specialist to route to based on the GP's assessment.
    """
    required_specialists = state.get("required_specialists", [])
    visited_specialists = state.get("visited_specialists", set())
    
    print(f"\nRequired specialists: {required_specialists}")
    print(f"\nVisited specialists: {visited_specialists}")
    
    if all(spec in visited_specialists for spec in required_specialists):
        return "summarizer"
    
    for specialist in required_specialists:
        if specialist not in visited_specialists:
            return specialist
    
    return "summarizer"

def create_dynamic_medical_workflow():
    class AgentState(Dict[str, Any]):
        report: str
        images: List[Image.Image] = []
        agent_results: List[Dict[str, str]] = []
        required_specialists: List[str] = []
        visited_specialists: Set[str] = set()
        final_report: str = ""

    workflow = StateGraph(AgentState)
    
    # Add all specialist nodes
    specialists = {
        "orthopaedician": orthopaedician_agent,
        "opthamologist": opthamologist_agent,
        "dentist": dentist_agent,
        "cardiologist": cardiologist_agent,
        "gynecologist": gynecologist_agent,
        "radiologist": radiologist_agent,
        "oncologist": oncologist_agent,
        "pain_management": pain_management_agent,
        "gastroenterologist": gastroenterologist_agent,
        "rheumatologist": rheumatologist_agent,
        "psychologist": psychologist_agent,
        "neurologist": neurologist_agent,
        "nephrologist":nephrologist_agent,
        "pulmonologist":pulmonologist_agent,
        "ent":ent_agent,
        "allergist":allergist_agent, 
        "endocrinologist":endocrinologist_agent,
        "dermatologist":dermatologist_agent,
        "urologist":urologist_agent,
        "hepatologist":hepatologist_agent,
        "dietician":dietician_agent,
        "neurosurgeon": neurosurgeon_agent,
        "radiation_oncologist":radiation_oncologist_agent,  
        "psychiatrist": psychiatrist_agent,
        "interventional_cardiologist":interventional_cardiologist_agent,
    }
    
    # Add GP node
    workflow.add_node("gp", gp_agent)
    
    # Add specialist nodes with state update wrapper
    for name, agent in specialists.items():
        workflow.add_node(name, update_state_after_specialist(agent))
    
    # Add summarizer node
    workflow.add_node("summarizer", summarize_findings)
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "gp",
        route_to_specialists,
        {name: name for name in specialists.keys()} | {"summarizer": "summarizer"}
    )
    
    for name in specialists.keys():
        workflow.add_conditional_edges(
            name,
            route_to_specialists,
            {other: other for other in specialists.keys()} | {"summarizer": "summarizer"}
        )
    
    workflow.set_entry_point("gp")
    
    return workflow.compile()

def update_state_after_specialist(specialist_func):
    def wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
        response_generator = specialist_func(state)
        full_response = ""

        for chunk in response_generator:  # Collect the full response
            full_response += chunk

        # Ensure the generator's result is now fully processed
        if isinstance(response_generator, dict):
            state = response_generator  # Assign directly if already a dictionary
        else:
            state["agent_results"][-1]["analysis"] = full_response  # Store full response

        specialist_name = specialist_func.__name__.replace("_agent", "")
        state["visited_specialists"] = state.get("visited_specialists", set()) | {specialist_name}
        print(f"Visited {specialist_name}")
        return state  # Now a proper dictionary
    return wrapped



def render_sidebar():
	# Custom CSS to increase sidebar width
    st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 650px;
            max-width: 900px;
        }
    </style>
    """,
    unsafe_allow_html=True
    )
    st.sidebar.title("Medical Consultation System")
    st.sidebar.markdown("---")
    
    # Input medical report
    st.sidebar.subheader("Patient Information")
    medical_report = st.sidebar.text_area("Medical Report/Symptoms", height=200, 
                                          placeholder="Enter patient symptoms, medical history, etc.")
    
    # Upload medical images
    st.sidebar.subheader("Medical Images (Optional)")
    uploaded_file = st.sidebar.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
    
    # Start consultation button
    start_consultation = st.sidebar.button("Analyse", type="primary")
    
    # Clear results button
    if st.sidebar.button("Clear Results"):
        st.session_state.agent_results = []
        st.session_state.current_specialist = None
        st.session_state.processing = False
        st.session_state.final_report = ""
        st.session_state.required_specialists = []
        st.session_state.visited_specialists = set()
        st.session_state.streaming_text = ""
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.info("This system analyzes patient information and routes to appropriate specialists.")
    
    return medical_report, uploaded_file, start_consultation

def main():
    medical_workflow = create_dynamic_medical_workflow()
    
    st.title("Multi-Specialist Medical Diagnostic Assistant")
    st.markdown("This system analyzes patient information and provides specialist consultations.")
    
    # Initialize session state
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = None
    if 'medical_report' not in st.session_state:
        st.session_state.medical_report = ""
    if 'medical_images' not in st.session_state:
        st.session_state.medical_images = None

    # Render sidebar and get inputs
    medical_report, uploaded_file, start_consultation = render_sidebar()
    process_images = []
    if uploaded_file:
								try:
												image = Image.open(uploaded_file)
												process_images.append(image)
												st.image(image, caption=uploaded_file.name, width=150)
								except UnidentifiedImageError:
												st.error(f"Unsupported image format: {uploaded_file}")
								except Exception as e:
												st.error(f"Error opening file {uploaded_file}: {e}")    

    if start_consultation:
        st.session_state.medical_report = medical_report
        st.session_state.medical_images = process_images if process_images else None
								
        initial_state = {
												"report": medical_report,
												"images": st.session_state.medical_images,
												"agent_results": [],
												"required_specialists": [],
												"visited_specialists": set(),
												"final_report": ""
        }

								
								# Run medical workflow
        st.session_state.workflow_state = medical_workflow.invoke(initial_state)

								# Clear loader after processing
        #placeholder.empty()
        st.rerun()


    # Display Results AFTER processing is complete
    if st.session_state.workflow_state:
        display_results(st.session_state.workflow_state)


def display_results(workflow_state):
    """Display only final tabbed results after processing."""
    tab_names = ["GP Assessment"] + [
        spec.replace("_", " ").title() for spec in workflow_state["required_specialists"]
    ] + ["Final Summary"]
    
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        #st.subheader("General Practitioner's Initial Assessment")
        gp_analysis = next(
            (item["analysis"] for item in workflow_state["agent_results"] 
             if item["specialist"] == "General Practitioner"), ""
        )
        st.markdown(gp_analysis)
    
    for idx, specialist in enumerate(workflow_state["required_specialists"], 1):
        with tabs[idx]:
            #st.subheader(f"{specialist.replace('_', ' ').title()}'s Analysis")
            analysis = next(
                (item["analysis"] for item in workflow_state["agent_results"] 
                 if item["specialist"].lower() == specialist.replace("_", " ").lower()), 
                "Analysis pending..."
            )
            st.markdown(analysis)
    
    with tabs[-1]:
        #st.subheader("Consolidated Medical Report")
        summary = workflow_state.get("final_report", "")
        st.markdown(summary)
        
        if st.button("🔄 Regenerate Summary"):
            workflow_state = summarize_findings(workflow_state)
            st.rerun()

if __name__ == "__main__":
    main()