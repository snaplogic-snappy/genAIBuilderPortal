import streamlit as st
import requests
import json
import pandas as pd
import time

# DEMO_METADATA - REQUIRED FOR SEARCH FUNCTIONALITY
DEMO_METADATA = {
    "categories": ["Technical", "Industry"],
    "tags": ["PII", "Data Privacy", "Healthcare", "Security", "Redaction", "Compliance", "HIPAA"]
}

# Page configuration
st.set_page_config(
    page_title="PII Redaction Agent",
    page_icon="🛡️",
    layout="wide"
)

# API Configuration - Set these values directly
URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/0_StanGPT/GenAI/Refined_Demo02_PersonalDataIdentifier_Task"
BEARER_TOKEN = "123456"
timeout = 30

# Page title and display
page_title = "PII Redaction Agent"
title = "🛡️ PII Redaction Agent"

st.title(title)

# Mock healthcare data for preview
MOCK_HEALTHCARE_DATA = [
  {
    "recordId": "REC_001",
    "patientId": "PID_98765",
    "firstName": "John",
    "lastName": "Smith",
    "dateOfBirth": "1985-03-15",
    "address": "123 Fake Street, Anytown, AN1 2BC",
    "phoneNumber": "07700900123",
    "email": "john.smith.demo@example.com",
    "nhsNumber": "1234567890",
    "appointmentDate": "2024-07-18",
    "hospitalId": "HOSP_A",
    "department": "Cardiology",
    "visitType": "Consultation",
    "specificDiagnosis": "Atrial Fibrillation",
    "attendingPhysician": "Dr. Emily Carter",
    "symptoms": ["Chest pain", "Shortness of breath"],
    "treatmentCategory": "Cardiovascular",
    "patientAgeRange": "30-40"
  },
  {
    "recordId": "REC_002",
    "patientId": "PID_12345",
    "firstName": "Jane",
    "lastName": "Doe",
    "dateOfBirth": "1992-11-20",
    "address": "456 Oak Avenue, Sometown, ST2 3DE",
    "phoneNumber": "07700900456",
    "email": "jane.doe.demo@example.com",
    "nhsNumber": "0987654321",
    "appointmentDate": "2024-07-19",
    "hospitalId": "HOSP_B",
    "department": "Oncology",
    "visitType": "Chemotherapy",
    "specificDiagnosis": "Stage 2 Breast Cancer",
    "attendingPhysician": "Dr. Ben Richards",
    "symptoms": ["Fatigue", "Lump detected"],
    "treatmentCategory": "Oncology",
    "patientAgeRange": "30-40"
  },
  {
    "recordId": "REC_003",
    "patientId": "PID_67890",
    "firstName": "Peter",
    "lastName": "Jones",
    "dateOfBirth": "1978-01-30",
    "address": "789 Pine Lane, Otherplace, OP3 4FG",
    "phoneNumber": "07700900789",
    "email": "peter.jones.demo@example.com",
    "nhsNumber": "1122334455",
    "appointmentDate": "2024-07-20",
    "hospitalId": "HOSP_A",
    "department": "Orthopedics",
    "visitType": "Follow-up",
    "specificDiagnosis": "Torn ACL",
    "attendingPhysician": "Dr. Sarah Lee",
    "symptoms": ["Knee pain", "Instability"],
    "treatmentCategory": "Musculoskeletal",
    "patientAgeRange": "40-50"
  },
  {
    "recordId": "REC_004",
    "patientId": "PID_54321",
    "firstName": "Mary",
    "lastName": "Williams",
    "dateOfBirth": "1965-06-10",
    "address": "101 Maple Drive, Anycity, AC4 5GH",
    "phoneNumber": "07700900101",
    "email": "mary.w.demo@example.com",
    "nhsNumber": "6677889900",
    "appointmentDate": "2024-07-21",
    "hospitalId": "HOSP_C",
    "department": "Neurology",
    "visitType": "Emergency",
    "specificDiagnosis": "Ischemic Stroke",
    "attendingPhysician": "Dr. David Chen",
    "symptoms": ["Facial drooping", "Arm weakness"],
    "treatmentCategory": "Neurological",
    "patientAgeRange": "50-60"
  },
  {
    "recordId": "REC_005",
    "patientId": "PID_11223",
    "firstName": "David",
    "lastName": "Brown",
    "dateOfBirth": "2001-09-05",
    "address": "212 Birch Road, Newville, NV5 6HI",
    "phoneNumber": "07700900212",
    "email": "david.brown.demo@example.com",
    "nhsNumber": "2233445566",
    "appointmentDate": "2024-07-22",
    "hospitalId": "HOSP_B",
    "department": "Dermatology",
    "visitType": "Check-up",
    "specificDiagnosis": "Severe Eczema",
    "attendingPhysician": "Dr. Laura Wilson",
    "symptoms": ["Skin rash", "Itching"],
    "treatmentCategory": "Dermatological",
    "patientAgeRange": "20-30"
  },
  {
    "recordId": "REC_006",
    "patientId": "PID_44556",
    "firstName": "Susan",
    "lastName": "Taylor",
    "dateOfBirth": "1959-02-14",
    "address": "333 Cedar Court, Oldtown, OT6 7JK",
    "phoneNumber": "07700900333",
    "email": "susan.t.demo@example.com",
    "nhsNumber": "7788990011",
    "appointmentDate": "2024-07-23",
    "hospitalId": "HOSP_A",
    "department": "Endocrinology",
    "visitType": "Routine",
    "specificDiagnosis": "Type 2 Diabetes",
    "attendingPhysician": "Dr. Michael Green",
    "symptoms": ["Increased thirst", "Frequent urination"],
    "treatmentCategory": "Endocrine",
    "patientAgeRange": "60-70"
  },
  {
    "recordId": "REC_007",
    "patientId": "PID_77889",
    "firstName": "Michael",
    "lastName": "Johnson",
    "dateOfBirth": "1988-08-25",
    "address": "444 Elm Street, Yourtown, YT7 8LM",
    "phoneNumber": "07700900444",
    "email": "michael.j.demo@example.com",
    "nhsNumber": "3344556677",
    "appointmentDate": "2024-07-24",
    "hospitalId": "HOSP_C",
    "department": "Gastroenterology",
    "visitType": "Procedure",
    "specificDiagnosis": "Crohn's Disease",
    "attendingPhysician": "Dr. Jessica White",
    "symptoms": ["Abdominal pain", "Diarrhea"],
    "treatmentCategory": "Gastrointestinal",
    "patientAgeRange": "30-40"
  },
  {
    "recordId": "REC_008",
    "patientId": "PID_99001",
    "firstName": "Linda",
    "lastName": "Martinez",
    "dateOfBirth": "1971-12-01",
    "address": "555 Spruce Avenue, Mytown, MT8 9NO",
    "phoneNumber": "07700900555",
    "email": "linda.m.demo@example.com",
    "nhsNumber": "8899001122",
    "appointmentDate": "2024-07-25",
    "hospitalId": "HOSP_B",
    "department": "Pulmonology",
    "visitType": "Test",
    "specificDiagnosis": "Chronic Obstructive Pulmonary Disease (COPD)",
    "attendingPhysician": "Dr. Robert Black",
    "symptoms": ["Wheezing", "Coughing"],
    "treatmentCategory": "Respiratory",
    "patientAgeRange": "50-60"
  },
  {
    "recordId": "REC_009",
    "patientId": "PID_22334",
    "firstName": "Robert",
    "lastName": "Garcia",
    "dateOfBirth": "1995-04-18",
    "address": "666 Willow Way, Histown, HT9 0PQ",
    "phoneNumber": "07700900666",
    "email": "robert.g.demo@example.com",
    "nhsNumber": "4455667788",
    "appointmentDate": "2024-07-26",
    "hospitalId": "HOSP_A",
    "department": "Psychiatry",
    "visitType": "Therapy",
    "specificDiagnosis": "Major Depressive Disorder",
    "attendingPhysician": "Dr. Olivia Grey",
    "symptoms": ["Low mood", "Loss of interest"],
    "treatmentCategory": "Mental Health",
    "patientAgeRange": "20-30"
  },
  {
    "recordId": "REC_010",
    "patientId": "PID_66778",
    "firstName": "Patricia",
    "lastName": "Rodriguez",
    "dateOfBirth": "1963-07-22",
    "address": "777 Redwood Close, Hertown, HR1 2RS",
    "phoneNumber": "07700900777",
    "email": "patricia.r.demo@example.com",
    "nhsNumber": "9900112233",
    "appointmentDate": "2024-07-27",
    "hospitalId": "HOSP_C",
    "department": "Rheumatology",
    "visitType": "Injection",
    "specificDiagnosis": "Rheumatoid Arthritis",
    "attendingPhysician": "Dr. William Gold",
    "symptoms": ["Joint swelling", "Stiffness"],
    "treatmentCategory": "Autoimmune",
    "patientAgeRange": "60-70"
  },
  {
    "recordId": "REC_011",
    "patientId": "PID_11122",
    "firstName": "James",
    "lastName": "Wilson",
    "dateOfBirth": "1980-05-12",
    "address": "888 Poplar Place, Ourtown, OT2 3TU",
    "phoneNumber": "07700900888",
    "email": "james.w.demo@example.com",
    "nhsNumber": "5566778899",
    "appointmentDate": "2024-07-28",
    "hospitalId": "HOSP_A",
    "department": "Urology",
    "visitType": "Consultation",
    "specificDiagnosis": "Kidney Stones",
    "attendingPhysician": "Dr. Chloe Brown",
    "symptoms": ["Severe back pain", "Nausea"],
    "treatmentCategory": "Urological",
    "patientAgeRange": "40-50"
  },
  {
    "recordId": "REC_012",
    "patientId": "PID_33445",
    "firstName": "Jennifer",
    "lastName": "Anderson",
    "dateOfBirth": "1998-10-03",
    "address": "999 Aspen Grove, Theirtown, TT3 4UV",
    "phoneNumber": "07700900999",
    "email": "jennifer.a.demo@example.com",
    "nhsNumber": "1122334400",
    "appointmentDate": "2024-07-29",
    "hospitalId": "HOSP_B",
    "department": "Allergy and Immunology",
    "visitType": "Testing",
    "specificDiagnosis": "Severe Peanut Allergy",
    "attendingPhysician": "Dr. Ethan Hunt",
    "symptoms": ["Hives", "Anaphylaxis risk"],
    "treatmentCategory": "Immunology",
    "patientAgeRange": "20-30"
  },
  {
    "recordId": "REC_013",
    "patientId": "PID_55667",
    "firstName": "Charles",
    "lastName": "Thomas",
    "dateOfBirth": "1975-03-28",
    "address": "121 Holly Lane, Lowtown, LT4 5VW",
    "phoneNumber": "07700901121",
    "email": "charles.t.demo@example.com",
    "nhsNumber": "6677889911",
    "appointmentDate": "2024-07-30",
    "hospitalId": "HOSP_C",
    "department": "Ophthalmology",
    "visitType": "Surgery",
    "specificDiagnosis": "Cataracts",
    "attendingPhysician": "Dr. Irene Adler",
    "symptoms": ["Blurry vision", "Glare"],
    "treatmentCategory": "Ophthalmological",
    "patientAgeRange": "40-50"
  },
  {
    "recordId": "REC_014",
    "patientId": "PID_77890",
    "firstName": "Jessica",
    "lastName": "Jackson",
    "dateOfBirth": "1982-06-19",
    "address": "232 Juniper Drive, Hightown, HT5 6WX",
    "phoneNumber": "07700901232",
    "email": "jessica.j.demo@example.com",
    "nhsNumber": "2233445522",
    "appointmentDate": "2024-07-31",
    "hospitalId": "HOSP_A",
    "department": "Obstetrics and Gynecology",
    "visitType": "Prenatal",
    "specificDiagnosis": "Gestational Diabetes",
    "attendingPhysician": "Dr. Grace O'Malley",
    "symptoms": ["High blood sugar", "Routine screening"],
    "treatmentCategory": "Obstetrics",
    "patientAgeRange": "40-50"
  },
  {
    "recordId": "REC_015",
    "patientId": "PID_99012",
    "firstName": "Daniel",
    "lastName": "White",
    "dateOfBirth": "2010-01-15",
    "address": "343 Sycamore Street, Middletown, MT6 7XY",
    "phoneNumber": "07700901343",
    "email": "daniel.w.demo@example.com",
    "nhsNumber": "7788990033",
    "appointmentDate": "2024-08-01",
    "hospitalId": "HOSP_B",
    "department": "Pediatrics",
    "visitType": "Vaccination",
    "specificDiagnosis": "Routine Immunization",
    "attendingPhysician": "Dr. Peter Pan",
    "symptoms": ["Healthy check-up"],
    "treatmentCategory": "Pediatric",
    "patientAgeRange": "10-20"
  },
  {
    "recordId": "REC_016",
    "patientId": "PID_12312",
    "firstName": "Nancy",
    "lastName": "Harris",
    "dateOfBirth": "1955-11-08",
    "address": "454 Sequoia Path, Oldville, OV7 8YZ",
    "phoneNumber": "07700901454",
    "email": "nancy.h.demo@example.com",
    "nhsNumber": "3344556644",
    "appointmentDate": "2024-08-02",
    "hospitalId": "HOSP_C",
    "department": "Geriatrics",
    "visitType": "Assessment",
    "specificDiagnosis": "Early-stage Alzheimer's",
    "attendingPhysician": "Dr. James Kirk",
    "symptoms": ["Memory loss", "Confusion"],
    "treatmentCategory": "Geriatric",
    "patientAgeRange": "60-70"
  },
  {
    "recordId": "REC_017",
    "patientId": "PID_34534",
    "firstName": "Mark",
    "lastName": "Martin",
    "dateOfBirth": "1991-07-07",
    "address": "565 Magnolia Court, Newcity, NC8 9ZA",
    "phoneNumber": "07700901565",
    "email": "mark.m.demo@example.com",
    "nhsNumber": "8899001144",
    "appointmentDate": "2024-08-03",
    "hospitalId": "HOSP_A",
    "department": "Infectious Disease",
    "visitType": "Emergency",
    "specificDiagnosis": "Pneumonia",
    "attendingPhysician": "Dr. Helen Cho",
    "symptoms": ["Fever", "Cough", "Difficulty breathing"],
    "treatmentCategory": "Infectious Disease",
    "patientAgeRange": "30-40"
  },
  {
    "recordId": "REC_018",
    "patientId": "PID_56756",
    "firstName": "Betty",
    "lastName": "Thompson",
    "dateOfBirth": "1948-04-21",
    "address": "676 Cypress Bend, Finaltown, FT9 0AB",
    "phoneNumber": "07700901676",
    "email": "betty.t.demo@example.com",
    "nhsNumber": "4455667755",
    "appointmentDate": "2024-08-04",
    "hospitalId": "HOSP_B",
    "department": "Nephrology",
    "visitType": "Dialysis",
    "specificDiagnosis": "End-Stage Renal Disease",
    "attendingPhysician": "Dr. Leonard McCoy",
    "symptoms": ["Fatigue", "Swelling in legs"],
    "treatmentCategory": "Nephrological",
    "patientAgeRange": "70-80"
  },
  {
    "recordId": "REC_019",
    "patientId": "PID_78978",
    "firstName": "Paul",
    "lastName": "Clark",
    "dateOfBirth": "1983-09-13",
    "address": "787 Fir Grove, Lastplace, LP1 2CD",
    "phoneNumber": "07700901787",
    "email": "paul.c.demo@example.com",
    "nhsNumber": "9900112255",
    "appointmentDate": "2024-08-05",
    "hospitalId": "HOSP_C",
    "department": "Sports Medicine",
    "visitType": "Rehabilitation",
    "specificDiagnosis": "Tennis Elbow",
    "attendingPhysician": "Dr. Ann Possible",
    "symptoms": ["Elbow pain", "Weak grip"],
    "treatmentCategory": "Musculoskeletal",
    "patientAgeRange": "40-50"
  },
  {
    "recordId": "REC_020",
    "patientId": "PID_90190",
    "firstName": "Karen",
    "lastName": "Lewis",
    "dateOfBirth": "1969-12-31",
    "address": "898 Hemlock Drive, Endpoint, EP2 3DE",
    "phoneNumber": "07700901898",
    "email": "karen.l.demo@example.com",
    "nhsNumber": "5566778866",
    "appointmentDate": "2024-08-06",
    "hospitalId": "HOSP_A",
    "department": "Hematology",
    "visitType": "Follow-up",
    "specificDiagnosis": "Iron-deficiency Anemia",
    "attendingPhysician": "Dr. Bruce Wayne",
    "symptoms": ["Tiredness", "Pale skin"],
    "treatmentCategory": "Hematological",
    "patientAgeRange": "50-60"
  }
]


st.markdown("""
### About This Demo
This PII Redaction Agent demonstrates automated detection and redaction of Personally Identifiable Information (PII) and Protected Health Information (PHI) in healthcare data. The agent identifies sensitive information like names, SSNs, addresses, phone numbers, and medical records, then provides redacted output for compliance with HIPAA and other privacy regulations.

**Key Features:**
- Automatic PII/PHI detection
- HIPAA-compliant redaction
- JSON input/output format
- Preview of sensitive data
- Compliance reporting
""")

# Input Data Preview Section
st.subheader("📋 Input Data Preview")

col_preview1, col_preview2 = st.columns([1, 4])
with col_preview1:
    show_preview = st.button("👀 Preview Healthcare Data", type="primary")
with col_preview2:
    if show_preview:
        hide_preview = st.button("🙈 Hide Preview", type="secondary")
    else:
        hide_preview = False

# Show preview data based on button state
if show_preview and not hide_preview:
    st.markdown("**Sample Healthcare Records (Contains PII/PHI):**")

    # Display as expandable sections
    with st.expander("📄 View Raw JSON Data", expanded=False):
        st.json(MOCK_HEALTHCARE_DATA)

    # Display as table for better readability
    with st.expander("📊 View as Data Table", expanded=False):
        df = pd.DataFrame(MOCK_HEALTHCARE_DATA)
        st.dataframe(df, use_container_width=True)


    st.warning("⚠️ **Notice**: This data contains sensitive PII/PHI and should be redacted before sharing.")

st.markdown("---")

# PII Redaction Processing Section
st.subheader("🛡️ PII Redaction Processing")

# Process PII Redaction
if st.button("🔒 Process PII Redaction", type="primary", use_container_width=True):
    if not URL or not BEARER_TOKEN:
        st.error("❌ Please configure API credentials in the script")
    else:
        with st.spinner("Processing PII redaction..."):
                try:
                    # API call to SnapLogic - Simple GET request
                    response = requests.get(
                        url=URL,
                        headers={'Authorization': f'Bearer {BEARER_TOKEN}'},
                        timeout=timeout
                    )

                    if response.status_code == 200:
                        result = response.json()

                        st.success("✅ PII Redaction completed successfully!")

                        st.markdown("---")
                        st.subheader("📋 API Response Results")

                        # Display API Results as Table
                        with st.expander("📊 Redacted Data Results", expanded=True):
                            st.markdown("**API Response Data:**")

                            # Try to display as table first (assuming it's a list of records)
                            if isinstance(result, list) and len(result) > 0:
                                try:
                                    df_result = pd.DataFrame(result)
                                    st.dataframe(df_result, use_container_width=True)


                                except Exception as e:
                                    st.error(f"Could not display as table: {str(e)}")
                                    st.json(result)
                            else:
                                # Display as JSON if not a list of records
                                st.json(result)

                        # Complete API Response Display
                        with st.expander("🔍 Complete API Response", expanded=False):
                            st.markdown("**Full response from the SnapLogic API:**")
                            st.json(result)

                        # Download Options
                        with st.expander("📥 Download Results", expanded=False):
                            result_json = json.dumps(result, indent=2)
                            st.download_button(
                                label="📄 Download API Results",
                                data=result_json,
                                file_name="pii_redaction_results.json",
                                mime="application/json",
                                use_container_width=True
                            )

                    else:
                        st.error(f"❌ Error while calling the SnapLogic API: {response.status_code}")
                        if response.text:
                            st.error(f"Response: {response.text}")

                except requests.RequestException as e:
                    st.error(f"❌ Network Error: {str(e)}")
                except json.JSONDecodeError as e:
                    st.error(f"❌ JSON Parsing Error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {str(e)}")

# Additional Information Section
st.markdown("---")

col_info1, col_info2 = st.columns([1, 1])

with col_info1:
    st.markdown("""
    ### 🔐 PII Types Detected
    - **Names** (First, Last, Full)
    - **Social Security Numbers**
    - **Phone Numbers**
    - **Email Addresses**
    - **Physical Addresses**
    - **Insurance Identifiers**
    - **Date of Birth**
    - **Emergency Contacts**
    """)

with col_info2:
    st.markdown("""
    ### 📋 Compliance Standards
    - **HIPAA** (Health Insurance Portability and Accountability Act)
    - **GDPR** (General Data Protection Regulation)
    - **CCPA** (California Consumer Privacy Act)
    - **SOX** (Sarbanes-Oxley Act)
    - **PCI DSS** (Payment Card Industry Data Security Standard)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>🛡️ PII Redaction Agent - Protecting sensitive information with SnapLogic Agent Creator</p>
    <p>⚠️ Always verify redaction results before sharing data in production environments</p>
</div>
""", unsafe_allow_html=True)