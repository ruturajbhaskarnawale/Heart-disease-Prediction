# Import necessary libraries
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# --- Page Configuration and State Management ---
st.set_page_config(
    page_title="Heart Disease Predictor & Insights",
    page_icon="🩺",
    layout="wide"
)

# Initialize session state for theme, language, and prediction results
if 'theme' not in st.session_state:
    st.session_state.theme = 'Light'
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'last_prediction_results' not in st.session_state:
    st.session_state.last_prediction_results = None

# --- Custom CSS for Dynamic Theming ---
if st.session_state.theme == 'Dark':
    st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        .stMarkdown, .stSubheader, .stTitle, h1, h2, h3, h4, h5, h6 {
            color: #fafafa;
        }
        /* Custom dark-mode styles for cards, containers, and text */
        .st-emotion-cache-1r6dm7w {
            background-color: #1c1f24;
            color: #fafafa;
        }
        .st-emotion-cache-13k65yv {
            background-color: #1a1a1e;
        }
        .st-emotion-cache-1c73hqw {
            background-color: #262730;
        }
        .st-emotion-cache-p5m60o {
            color: #c9c9c9;
        }
        </style>
    """, unsafe_allow_html=True)
else: # Light theme
    st.markdown("""
        <style>
        .stApp {
            background-color: #f0f2f6;
            color: #262730;
        }
        .stMarkdown, .stSubheader, .stTitle, h1, h2, h3, h4, h5, h6 {
            color: #262730;
        }
        /* Custom light-mode styles for cards, containers, and text */
        .st-emotion-cache-1r6dm7w {
            background-color: #ffffff;
            color: #262730;
        }
        .st-emotion-cache-13k65yv {
            background-color: #ffffff;
        }
        .st-emotion-cache-1c73hqw {
            background-color: #e0e2e6;
        }
        .st-emotion-cache-p5m60o {
            color: #555555;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Multilingual Support Dictionary ---
translations = {
    'en': {
        'app_title': '❤️ Heart Disease Prediction',
        'app_intro': 'Enter the patient\'s details below to get a real-time prediction from our machine learning model.',
        'theme_label': 'App Controls',
        'theme_radio': 'Choose Theme',
        'lang_label': 'Language',
        'lang_selectbox': 'Choose a language',
        'tab_prediction': 'Prediction',
        'tab_whatif': 'What-If Analysis',
        'tab_insights': 'Model Insights',
        'tab_batch': 'Batch Prediction',
        'tab_recommendations': 'Recommendations',
        'tab_resources': 'Local Resources',
        'tab_trends': 'Trend Analysis',
        'model_info': 'Using **{}** model. Test set accuracy: **{:.2f}%**',
        'patient_details': 'Patient Details',
        'predict_button': 'Predict',
        'prediction_result': 'Prediction Result',
        'no_disease': '✅ Prediction: No heart disease detected.',
        'disease': '🚨 Prediction: Heart disease is likely.',
        'confidence': 'Confidence',
        'input_summary': 'Input Summary',
        'risk_gauge_title': 'Heart Disease Risk', # NEW
        'what_if_analysis_header': '🔬 **Interactive What-If Analysis**',
        'what_if_intro': 'See how changing a single feature affects the prediction probability in real-time.',
        'select_feature_what_if': 'Select a feature to analyze:',
        'plot_what_if_title': 'Prediction Probability vs. {}',
        'plot_what_if_yaxis': 'Probability of Heart Disease',
        'plot_current_value': 'Current Patient Value',
        'insights_title': '🔬 Model Insights',
        'insights_intro': 'This section provides a deeper look at the models and the dataset they were trained on.',
        'model_comparison_header': 'Model Comparison Dashboard',
        'model_comparison_intro': 'Compare the performance of different machine learning models.',
        'feature_importance_header': 'Feature Importance',
        'feature_importance_intro': 'The chart below shows which features were most important for the Random Forest model\'s predictions.',
        'feature_importance_title': 'Relative Feature Importance for Heart Disease Prediction',
        'dataset_distributions_header': 'Dataset Feature Distributions',
        'dataset_distributions_intro': 'These plots show the distribution of key features in the original training data.',
        'batch_title': '📂 Batch Prediction from CSV',
        'batch_intro': 'Upload a CSV file with patient data to get predictions for multiple records at once.',
        'upload_file': 'Choose a CSV file',
        'file_uploaded_success': 'File uploaded successfully!',
        'missing_cols_error': 'The uploaded CSV is missing the following required columns: {}',
        'batch_predicting_spinner': 'Making predictions for the uploaded data...',
        'batch_results_header': 'Prediction Results',
        'batch_results_intro': 'Predictions have been added to the table below.',
        'download_predictions': 'Download Predictions as CSV',
        'file_processing_error': 'An error occurred while processing the file: {}',
        'feature_glossary_header': '📚 **Feature Glossary**',
        'feature_glossary_intro': 'Here is a detailed explanation of each feature used in the prediction model.',
        'feature_descriptions': {
            'age': 'The patient\'s age in years. Age is a key risk factor for heart disease.',
            'sex': 'The patient\'s biological sex. (0 = female, 1 = male).',
            'chest_pain_type': 'The type of chest pain experienced, which can be a key symptom. (1: typical angina, 2: atypical angina, 3: non-anginal pain, 4: asymptomatic).',
            'resting_bp_s': 'Resting blood pressure in mm Hg. High blood pressure is a major risk factor.',
            'cholesterol': 'Serum cholesterol in mg/dl. High cholesterol levels can lead to plaque buildup in arteries.',
            'fasting_blood_sugar': 'Fasting blood sugar level. (1 = >120 mg/dl, 0 = <=120 mg/dl). High sugar levels can indicate diabetes, a major risk factor.',
            'resting_ecg': 'Resting electrocardiographic results. (0: normal, 1: ST-T wave abnormality, 2: left ventricular hypertrophy).',
            'max heart rate': 'The maximum heart rate achieved during a physical stress test. A lower maximum heart rate can sometimes indicate heart problems.',
            'exercise_angina': 'Whether exercise induced chest pain. (1 = yes, 0 = no).',
            'oldpeak': 'ST depression induced by exercise relative to rest. This is a measure of the heart\'s response to stress.',
            'st_slope': 'The slope of the peak exercise ST segment. (1: upsloping, 2: flat, 3: downsloping).',
            'target': 'The target variable, indicating the presence of heart disease. (0 = no disease, 1 = heart disease).',
            'smoke': 'Do you smoke? (1 = Yes, 0 = No)'
        },
        'hist_feature_label': 'Select Feature for Histogram',
        'hist_group_by_label': 'Group by (Color)',
        'hist_title': 'Distribution of {} Grouped by {}',
        'corr_heatmap_header': 'Feature Correlation Heatmap',
        'corr_heatmap_title': 'Correlation Matrix of All Features',
        'age_warning': 'Please enter a realistic age (18-100).',
        'bp_warning': 'A resting BP of 90-180 mm Hg is a common range. Please check.',
        'cholesterol_info': 'Cholesterol outside 120-300 mg/dl is less common.',
        'hr_info': 'A max heart rate of 100-200 bpm is typical during exercise.',
        'rec_title': 'Personalized Recommendations',
        'rec_intro_1': 'Based on your input and the model\'s prediction, here are some personalized health recommendations.',
        'rec_intro_2': 'A medical professional can provide a more accurate diagnosis and a personalized plan.',
        'rec_warning_nodata': 'Please go to the "Prediction" tab and make a prediction first to receive recommendations.',
        'rec_rule_1_cholesterol': 'Your **cholesterol** level is elevated. Consider a low-fat, high-fiber diet and consult with a doctor about managing your levels.',
        'rec_rule_2_bp': 'Your **resting blood pressure** is high. Regular exercise, a low-sodium diet, and stress management can help.',
        'rec_rule_3_hr': 'Your **maximum heart rate** is low for your age. This may indicate a need for further medical evaluation.',
        'rec_rule_4_smoke': 'Smoking significantly increases your risk of heart disease. **Quitting smoking** is one of the most important steps you can take for your heart health.',
        'rec_rule_5_disease': 'The model predicts a high likelihood of heart disease. **Please consult a cardiologist immediately** for a professional diagnosis and treatment plan.',
        'res_title': 'Local Health Resources',
        'res_intro': 'Find government programs, emergency services, and top hospitals for cardiac care in your area.',
        'res_select_city': 'Select your nearest city/state:',
        'res_section_emergency': '🚨 **Emergency Services**',
        'res_section_hospitals': '🏥 **Top Cardiac Hospitals**',
        'res_section_clinics_and_diagnostics': '🏥 **Specialized Clinics & Diagnostics**',
        'res_section_diet_and_rehab': '🍎 **Diet & Rehabilitation Centers**',
        'res_section_programs': '⚕️ **Government Health Programs**',
        'res_section_ngos': '🤝 **NGOs & Support Foundations**',
        'res_ambulance_all': 'General Emergency (Police, Fire, Ambulance): **112**',
        'res_ambulance_specific': 'For cardiac-specific ambulance services in major cities, contact major hospitals directly.',
        'res_info_ayushman': 'The **Ayushman Bharat PM-JAY** scheme provides health cover of up to ₹5 Lakhs for eligible families for secondary and tertiary care hospitalization, including heart diseases.',
        'res_info_npcdcs': 'The **National Programme for Prevention and Control of Cancer, Diabetes, Cardiovascular Diseases & Stroke (NPCDCS)** offers free screening and diagnosis at district and CHC levels.',
        'trends_title': '📈 Trend Analysis',
        'trends_intro': 'This section analyzes trends and patterns in the dataset, particularly across different age groups.',
        'trends_age_dist_header': 'Heart Disease Distribution by Age Group',
        'trends_age_dist_intro': 'This chart shows how the proportion of patients with heart disease changes with age.',
        'trends_age_risk_header': 'Heart Disease Risk by Age',
        'trends_age_risk_intro': 'The percentage of patients with heart disease per age group.',
        'trends_feature_by_age_header': 'Key Features Trends by Age',
        'trends_feature_by_age_intro': 'This plot shows the relationship between two selected features and age.'
    },
    'hi': {
        'app_title': '❤️ हृदय रोग भविष्यवाणी',
        'app_intro': 'मशीन लर्निंग मॉडल से वास्तविक समय में भविष्यवाणी पाने के लिए रोगी का विवरण दर्ज करें।',
        'theme_label': 'ऐप नियंत्रण',
        'theme_radio': 'थीम चुनें',
        'lang_label': 'भाषा',
        'lang_selectbox': 'एक भाषा चुनें',
        'tab_prediction': 'भविष्यवाणी',
        'tab_whatif': 'क्या-होता-अगर विश्लेषण',
        'tab_insights': 'मॉडल विश्लेषण',
        'tab_batch': 'बैच भविष्यवाणी',
        'tab_recommendations': 'सिफारिशें',
        'tab_resources': 'स्थानीय संसाधन',
        'tab_trends': 'ट्रेंड विश्लेषण',
        'model_info': '**{}** मॉडल का उपयोग। परीक्षण सेट सटीकता: **{:.2f}%**',
        'patient_details': 'रोगी का विवरण',
        'predict_button': 'भविष्यवाणी करें',
        'prediction_result': 'भविष्यवाणी परिणाम',
        'no_disease': '✅ भविष्यवाणी: कोई हृदय रोग नहीं पाया गया।',
        'disease': '🚨 भविष्यवाणी: हृदय रोग की संभावना है।',
        'confidence': 'आत्मविश्वास',
        'input_summary': 'इनपुट सारांश',
        'risk_gauge_title': 'हृदय रोग का खतरा', # NEW
        'what_if_analysis_header': '🔬 **इंटरैक्टिव क्या-होता-अगर विश्लेषण**',
        'what_if_intro': 'देखें कि एक विशेषता को बदलने से भविष्यवाणी की संभावना पर क्या असर पड़ता है।',
        'select_feature_what_if': 'विश्लेषण के लिए एक विशेषता चुनें:',
        'plot_what_if_title': 'भविष्यवाणी की संभावना बनाम {}',
        'plot_what_if_yaxis': 'हृदय रोग की संभावना',
        'plot_current_value': 'वर्तमान रोगी मान',
        'insights_title': '🔬 मॉडल विश्लेषण',
        'insights_intro': 'यह अनुभाग मॉडलों और डेटासेट पर एक गहरी नज़र डालता है।',
        'model_comparison_header': 'मॉडल तुलना डैशबोर्ड',
        'model_comparison_intro': 'विभिन्न मशीन लर्निंग मॉडलों के प्रदर्शन की तुलना करें।',
        'feature_importance_header': 'विशेषता का महत्व',
        'feature_importance_intro': 'नीचे दिया गया चार्ट दिखाता है कि रैंडम फॉरेस्ट मॉडल की भविष्यवाणियों के लिए कौन सी विशेषताएं सबसे महत्वपूर्ण थीं।',
        'feature_importance_title': 'हृदय रोग की भविष्यवाणी के लिए सापेक्ष विशेषता का महत्व',
        'dataset_distributions_header': 'डेटासेट विशेषता वितरण',
        'dataset_distributions_intro': 'ये प्लॉट मूल प्रशिक्षण डेटा में प्रमुख विशेषताओं का वितरण दिखाते हैं।',
        'batch_title': '📂 CSV से बैच भविष्यवाणी',
        'batch_intro': 'एक ही बार में कई रिकॉर्ड के लिए भविष्यवाणी पाने के लिए रोगी डेटा के साथ एक CSV फ़ाइल अपलोड करें।',
        'upload_file': 'एक CSV फ़ाइल चुनें',
        'file_uploaded_success': 'फ़ाइल सफलतापूर्वक अपलोड हुई!',
        'missing_cols_error': 'अपलोड किए गए CSV में निम्नलिखित आवश्यक कॉलम गायब हैं: {}',
        'batch_predicting_spinner': 'अपलोड किए गए डेटा के लिए भविष्यवाणी की जा रही है...',
        'batch_results_header': 'भविष्यवाणी परिणाम',
        'batch_results_intro': 'भविष्यवाणियाँ नीचे दी गई तालिका में जोड़ दी गई हैं।',
        'download_predictions': 'भविष्यवाणियों को CSV के रूप में डाउनलोड करें',
        'file_processing_error': 'फ़ाइल को संसाधित करते समय एक त्रुटि हुई: {}',
        'feature_glossary_header': '📚 **विशेषता शब्दावली**',
        'feature_glossary_intro': 'यहां भविष्यवाणी मॉडल में उपयोग की जाने वाली प्रत्येक विशेषता का विस्तृत विवरण दिया गया है।',
        'feature_descriptions': {
            'age': 'वर्षों में रोगी की उम्र। उम्र हृदय रोग के लिए एक प्रमुख जोखिम कारक है।',
            'sex': 'रोगी का जैविक लिंग। (0 = महिला, 1 = पुरुष)।',
            'chest_pain_type': 'अनुभव किए गए सीने में दर्द का प्रकार। (1: विशिष्ट एनजाइना, 2: एटिपिकल एनजाइना, 3: गैर-एनजाइनल दर्द, 4: स्पर्शोन्मुख)।',
            'resting_bp_s': 'आराम करने पर रक्तचाप मिमी एचजी में। उच्च रक्तचाप एक प्रमुख जोखिम कारक है।',
            'cholesterol': 'सीरम कोलेस्ट्रॉल मिलीग्राम/डीएल में। उच्च कोलेस्ट्रॉल का स्तर धमनियों में प्लाक बिल्डअप का कारण बन सकता है।',
            'fasting_blood_sugar': 'उपवास में रक्त शर्करा का स्तर। (1 = >120 मिलीग्राम/डीएल, 0 = <=120 मिलीग्राम/डीएल)। उच्च शर्करा स्तर मधुमेह का संकेत दे सकते हैं, जो एक प्रमुख जोखिम कारक है।',
            'resting_ecg': 'आराम करने पर इलेक्ट्रोकार्डियोग्राफिक परिणाम। (0: सामान्य, 1: एसटी-टी तरंग असामान्यता, 2: बाएं वेंट्रिकुलर हाइपरट्रॉफी)।',
            'max heart rate': 'शारीरिक तनाव परीक्षण के दौरान प्राप्त अधिकतम हृदय गति। कम अधिकतम हृदय गति कभी-कभी हृदय समस्याओं का संकेत दे सकती है।',
            'exercise_angina': 'क्या व्यायाम से सीने में दर्द हुआ। (1 = हाँ, 0 = नहीं)।',
            'oldpeak': 'आराम की तुलना में व्यायाम से प्रेरित एसटी डिप्रेशन। यह तनाव के प्रति हृदय की प्रतिक्रिया का एक माप है।',
            'st_slope': 'पीक व्यायाम एसटी सेगमेंट का ढलान। (1: ऊपर की ओर, 2: सपाट, 3: नीचे की ओर)।',
            'target': 'लक्ष्य चर, हृदय रोग की उपस्थिति का संकेत देता है। (0 = कोई बीमारी नहीं, 1 = हृदय रोग)।',
            'smoke': 'क्या आप धूम्रपान करते हैं? (1 = हाँ, 0 = नहीं)'
        },
        'hist_feature_label': 'हिस्टोग्राम के लिए विशेषता चुनें',
        'hist_group_by_label': 'द्वारा समूह (रंग)',
        'hist_title': '{} का वितरण {} द्वारा समूहीकृत',
        'corr_heatmap_header': 'विशेषता सहसंबंध हीटमैप',
        'corr_heatmap_title': 'सभी विशेषताओं की सहसंबंध मैट्रिक्स',
        'age_warning': 'कृपया एक यथार्थवादी आयु दर्ज करें (18-100)।',
        'bp_warning': '90-180 मिमी एचजी की आराम बीपी एक सामान्य सीमा है। कृपया जांच करें।',
        'cholesterol_info': '120-300 मिलीग्राम/डीएल के बाहर कोलेस्ट्रॉल कम आम है।',
        'hr_info': '100-200 बीपीएम की अधिकतम हृदय गति व्यायाम के दौरान सामान्य है।',
        'rec_title': 'व्यक्तिगत सिफारिशें',
        'rec_intro_1': 'आपके इनपुट और मॉडल की भविष्यवाणी के आधार पर, यहाँ कुछ व्यक्तिगत स्वास्थ्य सिफारिशें दी गई हैं।',
        'rec_intro_2': 'एक चिकित्सा पेशेवर अधिक सटीक निदान और एक व्यक्तिगत योजना प्रदान कर सकता है।',
        'rec_warning_nodata': 'कृपया सिफारिशें प्राप्त करने के लिए "भविष्यवाणी" टैब पर जाएं और पहले एक भविष्यवाणी करें।',
        'rec_rule_1_cholesterol': 'आपका **कोलेस्ट्रॉल** का स्तर बढ़ा हुआ है। कम वसा, उच्च फाइबर आहार पर विचार करें और अपने स्तरों को प्रबंधित करने के बारे में एक डॉक्टर से परामर्श लें।',
        'rec_rule_2_bp': 'आपका **आराम करते समय रक्तचाप** उच्च है। नियमित व्यायाम, कम सोडियम आहार और तनाव प्रबंधन मदद कर सकते हैं।',
        'rec_rule_3_hr': 'आपकी **अधिकतम हृदय गति** आपकी उम्र के लिए कम है। यह आगे के चिकित्सा मूल्यांकन की आवश्यकता का संकेत दे सकता है।',
        'rec_rule_4_smoke': 'धूम्रपान आपके हृदय रोग के जोखिम को काफी बढ़ाता है। **धूम्रपान छोड़ना** आपके हृदय स्वास्थ्य के लिए सबसे महत्वपूर्ण कदमों में से एक है।',
        'rec_rule_5_disease': 'मॉडल हृदय रोग की एक उच्च संभावना की भविष्यवाणी करता है। पेशेवर निदान और उपचार योजना के लिए **कृपया तुरंत एक हृदय रोग विशेषज्ञ से परामर्श लें**।',
        'res_title': 'स्थानीय स्वास्थ्य संसाधन',
        'res_intro': 'अपने क्षेत्र में हृदय संबंधी देखभाल के लिए सरकारी कार्यक्रम, आपातकालीन सेवाएं, और शीर्ष अस्पताल खोजें।',
        'res_select_city': 'अपने निकटतम शहर/राज्य का चयन करें:',
        'res_section_emergency': '🚨 **आपातकालीन सेवाएं**',
        'res_section_hospitals': '🏥 **शीर्ष हृदय अस्पताल**',
        'res_section_clinics_and_diagnostics': '🏥 **विशेषज्ञ क्लीनिक और निदान**',
        'res_section_diet_and_rehab': '🍎 **आहार और पुनर्वास केंद्र**',
        'res_section_programs': '⚕️ **सरकारी स्वास्थ्य कार्यक्रम**',
        'res_section_ngos': '🤝 **एनजीओ और समर्थन फाउंडेशन**',
        'res_ambulance_all': 'सामान्य आपातकाल (पुलिस, अग्निशमन, एम्बुलेंस): **112**',
        'res_ambulance_specific': 'प्रमुख शहरों में हृदय-विशिष्ट एम्बुलेंस सेवाओं के लिए, सीधे प्रमुख अस्पतालों से संपर्क करें।',
        'res_info_ayushman': 'आयुष्मान भारत पीएम-जेएवाई योजना पात्र परिवारों को हृदय रोगों सहित माध्यमिक और तृतीयक देखभाल अस्पताल में भर्ती के लिए ₹5 लाख तक का स्वास्थ्य कवर प्रदान करती है।',
        'res_info_npcdcs': 'राष्ट्रीय कैंसर, मधुमेह, हृदय रोग और स्ट्रोक रोकथाम और नियंत्रण कार्यक्रम (एनपीसीडीसीएस) जिला और सीएचसी स्तर पर मुफ्त स्क्रीनिंग और निदान प्रदान करता है।',
        'trends_title': '📈 ट्रेंड विश्लेषण',
        'trends_intro': 'यह अनुभाग डेटासेट में रुझानों और पैटर्न का विश्लेषण करता है, विशेष रूप से विभिन्न आयु समूहों में।',
        'trends_age_dist_header': 'आयु समूह द्वारा हृदय रोग वितरण',
        'trends_age_dist_intro': 'यह चार्ट दर्शाता है कि हृदय रोग वाले रोगियों का अनुपात उम्र के साथ कैसे बदलता है।',
        'trends_age_risk_header': 'उम्र के अनुसार हृदय रोग का जोखिम',
        'trends_age_risk_intro': 'प्रति आयु समूह हृदय रोग वाले रोगियों का प्रतिशत।',
        'trends_feature_by_age_header': 'उम्र के अनुसार प्रमुख विशेषता रुझान',
        'trends_feature_by_age_intro': 'यह प्लॉट दो चयनित विशेषताओं और उम्र के बीच संबंध को दर्शाता है।'
    },
    'mr': {
        'app_title': '❤️ हृदय रोग अंदाज',
        'app_intro': 'मशीन लर्निंग मॉडेलकडून रिअल-टाइम अंदाज मिळवण्यासाठी रुग्णाचे तपशील खाली एंटर करा.',
        'theme_label': 'ॲप नियंत्रणे',
        'theme_radio': 'थीम निवडा',
        'lang_label': 'भाषा',
        'lang_selectbox': 'एक भाषा निवडा',
        'tab_prediction': 'अंदाज',
        'tab_whatif': 'काय-तर विश्लेषण',
        'tab_insights': 'मॉडेल अंतर्दृष्टी',
        'tab_batch': 'बॅच अंदाज',
        'tab_recommendations': 'शिफारसी',
        'tab_resources': 'स्थानिक संसाधने',
        'tab_trends': 'प्रवृत्ती विश्लेषण',
        'model_info': '**{}** मॉडेलचा वापर. चाचणी संचाची अचूकता: **{:.2f}%**',
        'patient_details': 'रुग्णाचे तपशील',
        'predict_button': 'अंदाज करा',
        'prediction_result': 'अंदाज परिणाम',
        'no_disease': '✅ अंदाज: हृदय रोग आढळला नाही.',
        'disease': '🚨 अंदाज: हृदय रोग होण्याची शक्यता आहे.',
        'confidence': 'आत्मविश्वास',
        'input_summary': 'इनपुट सारांश',
        'risk_gauge_title': 'हृदय रोगाचा धोका', # NEW
        'what_if_analysis_header': '🔬 **परस्परसंवादी काय-तर विश्लेषण**',
        'what_if_intro': 'एखादे वैशिष्ट्य बदलल्यास अंदाजाच्या संभाव्यतेवर कसा परिणाम होतो ते रिअल-टाइममध्ये पहा.',
        'select_feature_what_if': 'विश्लेषण करण्यासाठी एक वैशिष्ट्य निवडा:',
        'plot_what_if_title': 'अंदाजाची संभाव्यता विरुद्ध {}',
        'plot_what_if_yaxis': 'हृदय रोग होण्याची संभाव्यता',
        'plot_current_value': 'सध्याचे रुग्णाचे मूल्य',
        'insights_title': '🔬 मॉडेल अंतर्दृष्टी',
        'insights_intro': 'हा विभाग मॉडेल आणि ज्या डेटासेटवर ते प्रशिक्षित केले गेले, त्यावर अधिक सखोल माहिती देतो.',
        'model_comparison_header': 'मॉडेल तुलना डॅशबोर्ड',
        'model_comparison_intro': 'विविध मशीन लर्निंग मॉडेल्सच्या कामगिरीची तुलना करा.',
        'feature_importance_header': 'वैशिष्ट्य महत्त्व',
        'feature_importance_intro': 'खालील चार्ट दर्शवितो की रँडम फॉरेस्ट मॉडेलच्या अंदाजांसाठी कोणती वैशिष्ट्ये सर्वात महत्त्वाची होती.',
        'feature_importance_title': 'हृदय रोगाच्या अंदाजासाठी सापेक्ष वैशिष्ट्य महत्त्व',
        'dataset_distributions_header': 'डेटासेट वैशिष्ट्य वितरण',
        'dataset_distributions_intro': 'हे प्लॉट मूळ प्रशिक्षण डेटातील प्रमुख वैशिष्ट्यांचे वितरण दर्शवितात.',
        'batch_title': '📂 CSV मधून बॅच अंदाज',
        'batch_intro': 'एकाच वेळी अनेक रेकॉर्डसाठी अंदाज मिळवण्यासाठी रुग्णाच्या डेटासह एक CSV फाइल अपलोड करा.',
        'upload_file': 'एक CSV फाइल निवडा',
        'file_uploaded_success': 'फाइल यशस्वीरित्या अपलोड झाली!',
        'missing_cols_error': 'अपलोड केलेल्या CSV मध्ये खालील आवश्यक कॉलम गहाळ आहेत: {}',
        'batch_predicting_spinner': 'अपलोड केलेल्या डेटासाठी अंदाज लावला जात आहे...',
        'batch_results_header': 'अंदाज परिणाम',
        'batch_results_intro': 'अंदाज खालील टेबलमध्ये जोडले गेले आहेत.',
        'download_predictions': 'अंदाज CSV म्हणून डाउनलोड करा',
        'file_processing_error': 'फाइलवर प्रक्रिया करताना एक त्रुटी आली: {}',
        'feature_glossary_header': '📚 **वैशिष्ट्य शब्दावली**',
        'feature_glossary_intro': 'येथे अंदाज मॉडेलमध्ये वापरल्या गेलेल्या प्रत्येक वैशिष्ट्याचे तपशीलवार स्पष्टीकरण दिले आहे.',
        'feature_descriptions': {
            'age': 'वर्षांमध्ये रुग्णाचे वय. वय हा हृदय रोगासाठी एक महत्त्वाचा धोका घटक आहे.',
            'sex': 'रुग्णाचे जैविक लिंग. (0 = स्त्री, 1 = पुरुष).',
            'chest_pain_type': 'अनुभवलेल्या छातीत दुखण्याचा प्रकार. (1: विशिष्ट एनजाइना, 2: ॲटिपिकल एनजाइना, 3: नॉन-एनजाइनल दुखणे, 4: लक्षण नसलेला).',
            'resting_bp_s': 'आराम करताना रक्तदाब मिमी एचजीमध्ये. उच्च रक्तदाब हा एक महत्त्वाचा धोका घटक आहे.',
            'cholesterol': 'सीरम कोलेस्ट्रॉल मिग्रॅ/डीएलमध्ये. उच्च कोलेस्ट्रॉल पातळीमुळे धमन्यांमध्ये प्लेक तयार होऊ शकतो.',
            'fasting_blood_sugar': 'उपाशीपोटी रक्तातील साखरेची पातळी. (1 = >120 मिग्रॅ/डीएल, 0 = <=120 मिग्रॅ/डीएल). उच्च साखरेची पातळी मधुमेह दर्शवू शकते, जो एक महत्त्वाचा धोका घटक आहे.',
            'resting_ecg': 'आराम करताना इलेक्ट्रोकार्डिओग्राफिक परिणाम. (0: सामान्य, 1: एसटी-टी तरंग विकृती, 2: डाव्या वेंट्रिकुलर हायपरट्रॉफी).',
            'max heart rate': 'शारीरिक तणाव चाचणी दरम्यान प्राप्त झालेली कमाल हृदय गती. कमी कमाल हृदय गती कधीकधी हृदयाच्या समस्या दर्शवू शकते.',
            'exercise_angina': 'व्यायामामुळे छातीत दुखणे झाले की नाही. (1 = होय, 0 = नाही).',
            'oldpeak': 'आरामाच्या तुलनेत व्यायामामुळे प्रेरित एसटी डिप्रेशन. हे तणावाच्या प्रतिसादात हृदयाची प्रतिक्रिया मोजते.',
            'st_slope': 'पीक व्यायाम एसटी सेगमेंटचा उतार. (1: वरच्या दिशेने, 2: सपाट, 3: खालच्या दिशेने).',
            'target': 'लक्ष्य चल, हृदय रोगाची उपस्थिती दर्शवते. (0 = रोग नाही, 1 = हृदय रोग).',
            'smoke': 'आपण धूम्रपान करता का? (1 = होय, 0 = नाही)'
        },
        'hist_feature_label': 'हिस्टोग्रामसाठी वैशिष्ट्य निवडा',
        'hist_group_by_label': 'द्वारे गट करा (रंग)',
        'hist_title': '{} चे वितरण {} द्वारे गट केलेले',
        'corr_heatmap_header': 'वैशिष्ट्य सहसंबंध हीटमॅप',
        'corr_heatmap_title': 'सर्व वैशिष्ट्यांची सहसंबंध मॅट्रिक्स',
        'age_warning': 'कृपया वास्तववादी वय प्रविष्ट करा (18-100).',
        'bp_warning': '90-180 मिमी एचजीचा विश्रांती बीपी सामान्य श्रेणीत आहे. कृपया तपासा.',
        'cholesterol_info': '120-300 मिग्रॅ/डीएलच्या बाहेर कोलेस्ट्रॉल कमी सामान्य आहे.',
        'hr_info': '100-200 बीपीएमची कमाल हृदय गती व्यायामादरम्यान सामान्य आहे.',
        'rec_title': 'वैयक्तिक शिफारसी',
        'rec_intro_1': 'आपल्या इनपुट आणि मॉडेलच्या अंदाजानुसार, येथे काही वैयक्तिक आरोग्य शिफारसी आहेत.',
        'rec_intro_2': 'एक वैद्यकीय व्यावसायिक अधिक अचूक निदान आणि एक वैयक्तिक योजना देऊ शकतो.',
        'rec_warning_nodata': 'कृपया "अंदाज" टॅबवर जाऊन प्रथम एक अंदाज करा, जेणेकरून शिफारसी मिळतील.',
        'rec_rule_1_cholesterol': 'आपली **कोलेस्ट्रॉल** पातळी वाढली आहे. कमी चरबीयुक्त, उच्च फायबर आहाराचा विचार करा आणि आपल्या पातळीचे व्यवस्थापन करण्याबद्दल डॉक्टरांचा सल्ला घ्या.',
        'rec_rule_2_bp': 'आपला **विश्रांतीच्या वेळेचा रक्तदाब** जास्त आहे. नियमित व्यायाम, कमी सोडियम आहार आणि तणाव व्यवस्थापन मदत करू शकतात.',
        'rec_rule_3_hr': 'आपली **कमाल हृदय गती** आपल्या वयासाठी कमी आहे. यामुळे पुढील वैद्यकीय मूल्यांकनाची आवश्यकता दर्शविली जाऊ शकते.',
        'rec_rule_4_smoke': 'धूम्रपान केल्याने हृदयरोगाचा धोका लक्षणीयरीत्या वाढतो. आपल्या हृदयाच्या आरोग्यासाठी **धूम्रपान सोडणे** हे सर्वात महत्त्वाचे पाऊल आहे.',
        'rec_rule_5_disease': 'मॉडेल हृदयरोगाची उच्च शक्यता दर्शवितो. व्यावसायिक निदान आणि उपचार योजनेसाठी **कृपया त्वरित हृदयरोग तज्ञाचा सल्ला घ्या**.',
        'res_title': 'स्थानिक आरोग्य संसाधने',
        'res_intro': 'आपल्या परिसरात हृदय काळजीसाठी सरकारी कार्यक्रम, आपत्कालीन सेवा आणि शीर्ष रुग्णालये शोधा.',
        'res_select_city': 'आपल्या जवळचे शहर/राज्य निवडा:',
        'res_section_emergency': '🚨 **आपत्कालीन सेवा**',
        'res_section_hospitals': '🏥 **शीर्ष हृदय रुग्णालये**',
        'res_section_clinics_and_diagnostics': '🏥 **विशेषज्ञ दवाखाने आणि निदान**',
        'res_section_diet_and_rehab': '🍎 **आहार आणि पुनर्वसन केंद्रे**',
        'res_section_programs': '⚕️ **सरकारी आरोग्य कार्यक्रम**',
        'res_section_ngos': '🤝 **एनजीओ आणि समर्थन फाउंडेशन**',
        'res_ambulance_all': 'सामान्य आपत्कालीन (पोलीस, अग्निशमन, रुग्णवाहिका): **112**',
        'res_ambulance_specific': 'प्रमुख शहरांमध्ये हृदय-विशिष्ट रुग्णवाहिका सेवांसाठी, थेट प्रमुख रुग्णालयांशी संपर्क साधा.',
        'res_info_ayushman': 'आयुष्मान भारत पीएम-जेएवाय योजना पात्र कुटुंबांसाठी हृदयरोगांसह दुय्यम आणि तृतीयक काळजी हॉस्पिटलायझेशनसाठी ₹5 लाख पर्यंतचे आरोग्य कवच प्रदान करते.',
        'res_info_npcdcs': 'राष्ट्रीय कर्करोग, मधुमेह, हृदय व रक्तवाहिन्यासंबंधी रोग आणि स्ट्रोक प्रतिबंध आणि नियंत्रण कार्यक्रम (एनपीसीडीसीएस) जिल्हा आणि सीएचसी स्तरावर विनामूल्य स्क्रीनिंग आणि निदान प्रदान करतो.',
        'trends_title': '📈 प्रवृत्ती विश्लेषण',
        'trends_intro': 'हा विभाग डेटासेटमधील प्रवृत्ती आणि पॅटर्नचे विश्लेषण करतो, विशेषतः विविध वयोगटांमध्ये.',
        'trends_age_dist_header': 'वय गटानुसार हृदय रोग वितरण',
        'trends_age_dist_intro': 'हा चार्ट दर्शवितो की हृदय रोग असलेल्या रुग्णांचे प्रमाण वयानुसार कसे बदलते.',
        'trends_age_risk_header': 'वयानुसार हृदय रोगाचा धोका',
        'trends_age_risk_intro': 'प्रति वय गट हृदय रोग असलेल्या रुग्णांची टक्केवारी.',
        'trends_feature_by_age_header': 'वयानुसार प्रमुख वैशिष्ट्य प्रवृत्ती',
        'trends_feature_by_age_intro': 'हा प्लॉट निवडलेल्या दोन वैशिष्ट्ये आणि वयामधील संबंध दर्शवितो.'
    }
}

# --- Resource Information Dictionary ---
local_resources = {
    'Mumbai': {
        'emergency': [
            {'name': 'General Emergency', 'number': '112'},
            {'name': 'Asian Heart Institute Ambulance', 'number': '+91-22-66986666'},
            {'name': 'Kokilaben Hospital Ambulance', 'number': '+91-22-42696969'},
        ],
        'hospitals': [
            'Asian Heart Institute',
            'Kokilaben Dhirubhai Ambani Hospital',
            'Fortis Hospital, Mulund',
            'P.D. Hinduja Hospital',
        ],
        'ngos': [
            'India Heart Foundation (http://indiaheartfoundation.in/)',
            'Heart Health India Foundation (https://hearthealthindia.org/)',
        ],
        'clinics_and_diagnostics': [
            'Metropolis Healthcare (Multiple locations)',
            'Dr. Lal PathLabs (Multiple locations)',
            'Advanced Cardiac Clinic, Bandra',
        ],
        'diet_and_rehab': [
            'Apollo Clinics (Dietitian services)',
            'Swaas Wellness',
        ],
    },
    'Delhi-NCR': {
        'emergency': [
            {'name': 'General Emergency', 'number': '112'},
            {'name': 'Fortis Escorts Heart Institute Ambulance', 'number': '+91-11-47135000'},
            {'name': 'Max Healthcare Ambulance', 'number': '+91-11-40554055'},
        ],
        'hospitals': [
            'Fortis Escorts Heart Institute',
            'Indraprastha Apollo Hospital',
            'Max Super Speciality Hospital',
            'Medanta – The Medicity, Gurugram',
        ],
        'ngos': [
            'Indian Heart Association (https://indianheartassociation.org/)',
            'Heart Care Foundation of India',
        ],
        'clinics_and_diagnostics': [
            'Dr. Lal PathLabs (Multiple locations)',
            'Metropolis Healthcare (Multiple locations)',
            'Aakash Healthcare, Dwarka',
        ],
        'diet_and_rehab': [
            'Vardaan Heart Clinic & Rehabilitation Centre',
            'Fitso (for exercise and fitness coaching)',
        ],
    },
    'Bengaluru': {
        'emergency': [
            {'name': 'General Emergency', 'number': '112'},
            {'name': 'Manipal Hospitals Ambulance', 'number': '1062'},
            {'name': 'Narayana Health Ambulance', 'number': '1057'},
        ],
        'hospitals': [
            'Narayana Institute of Cardiac Sciences',
            'Manipal Hospital, Old Airport Road',
            'Jayadeva Hospital',
            'Apollo Hospitals',
        ],
        'ngos': [
            'Indian Heart Association (https://indianheartassociation.org/)',
            'Heart Health India Foundation (https://hearthealthindia.org/)',
        ],
        'clinics_and_diagnostics': [
            'Aura Diagnostics, Koramangala',
            'Nightingale Diagnostics',
            'Manipal Cardiology Clinics',
        ],
        'diet_and_rehab': [
            'Fittr (online nutrition coaching)',
            'Apollo Hospitals Cardiac Rehab',
        ],
    },
    'Chennai': {
        'emergency': [
            {'name': 'General Emergency', 'number': '112'},
            {'name': 'Apollo Hospitals Ambulance', 'number': '1066'},
        ],
        'hospitals': [
            'Apollo Hospitals',
            'Fortis Malar Hospital',
            'MGM Healthcare',
            'MIOT International',
        ],
        'ngos': [
            'Indian Heart Association (https://indianheartassociation.org/)',
            'Heart Health India Foundation (https://hearthealthindia.org/)',
        ],
        'clinics_and_diagnostics': [
            'Dr. Lal PathLabs (Multiple locations)',
            'Medall Diagnostics',
        ],
        'diet_and_rehab': [
            'Chennai Heart Care',
        ],
    }
}

# --- Functions for Caching Data and Models ---
@st.cache_data
def load_data():
    """Loads the heart disease dataset."""
    try:
        df = pd.read_csv('heart_statlog_cleveland_hungary_final.csv')
        # Add 'smoke' column to the DataFrame with a default value of 0
        df['smoke'] = 0
        X = df.drop('target', axis=1)
        y = df['target']
        return X, y, df
    except FileNotFoundError:
        st.error(f"Error: The file 'heart_statlog_cleveland_hungary_final.csv' was not found. Please make sure it's in the same directory as the app.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        st.stop()

@st.cache_resource
def train_models(X, y):
    """Trains multiple classifiers and returns them with their cross-validation scores."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        'Random Forest': RandomForestClassifier(random_state=42),
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
        'Support Vector Machine': SVC(random_state=42, probability=True)
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')

        results[name] = {
            'model': model,
            'test_accuracy': accuracy,
            'cv_mean_accuracy': np.mean(cv_scores)
        }
    return results

# --- Recommendation Logic ---
def generate_recommendations(input_data, prediction_result):
    """Generates a list of rule-based recommendations based on input data."""
    rec = []
    # Rule 1: High Cholesterol
    if input_data['cholesterol'].iloc[0] > 240:
        rec.append(lang['rec_rule_1_cholesterol'])

    # Rule 2: High Resting BP
    if input_data['resting bp s'].iloc[0] > 140:
        rec.append(lang['rec_rule_2_bp'])

    # Rule 3: Low Max Heart Rate for Age (simple heuristic)
    if input_data['max heart rate'].iloc[0] < (220 - input_data['age'].iloc[0]) * 0.7:
        rec.append(lang['rec_rule_3_hr'])

    # Rule 4: Smoker
    if input_data['smoke'].iloc[0] == 1:
        rec.append(lang['rec_rule_4_smoke'])

    # Rule 5: Heart Disease Predicted
    if prediction_result == 1:
        rec.append(lang['rec_rule_5_disease'])

    return rec

# <<< NEW HELPER FUNCTION START >>>
def create_gauge_chart(probability, title_text, theme):
    """Creates a Plotly gauge chart for risk probability."""
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability,
        number={'valueformat': '.2%'},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title_text, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, 1], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': "#262730" if theme == 'Dark' else "#e0e2e6"},
            'steps': [
                {'range': [0, 0.4], 'color': 'green'},
                {'range': [0.4, 0.7], 'color': 'orange'},
                {'range': [0.7, 1], 'color': 'red'}
            ],
        }
    ))
    fig_gauge.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig_gauge
# <<< NEW HELPER FUNCTION END >>>


# --- Main Application Logic ---
X, y, df = load_data()
model_results = train_models(X, y)
selected_model_name = 'Random Forest'
model = model_results[selected_model_name]['model']
test_accuracy = model_results[selected_model_name]['test_accuracy']

# <<< MODIFIED SECTION START: SIDEBAR NAVIGATION >>>

# --- Sidebar for Global Controls & Navigation ---
st.sidebar.title('Global Controls')
theme_choice = st.sidebar.radio('Choose Theme', ['Light', 'Dark'])
if theme_choice != st.session_state.theme:
    st.session_state.theme = theme_choice
    st.rerun()

st.sidebar.subheader('Language')
lang_choice = st.sidebar.selectbox(
    'Choose a language',
    ('en', 'hi', 'mr'),
    format_func=lambda x: "English" if x == "en" else "हिन्दी" if x == "hi" else "मराठी"
)
if lang_choice != st.session_state.language:
    st.session_state.language = lang_choice
    st.rerun()

lang = translations[st.session_state.language]

# --- Sidebar Navigation Menu ---
st.sidebar.title("Navigation")
page_options = [
    lang['tab_prediction'],
    lang['tab_whatif'],
    lang['tab_insights'],
    lang['tab_batch'],
    lang['tab_recommendations'],
    lang['tab_resources'],
    lang['tab_trends']
]
selected_page = st.sidebar.radio("Go to", page_options, label_visibility="collapsed")

# <<< MODIFIED SECTION END: The st.tabs() call has been removed. >>>


# --- Main App Content (Conditionally Rendered based on Sidebar Selection) ---

# --- Page 1: Prediction Interface ---
if selected_page == lang['tab_prediction']:
    st.title(lang['app_title'])
    st.markdown(lang['app_intro'])

    st.info(lang['model_info'].format(selected_model_name, test_accuracy * 100))
    st.markdown("---")

    with st.expander(lang['feature_glossary_header'], expanded=False):
        st.markdown(lang['feature_glossary_intro'])
        for feature, desc in lang['feature_descriptions'].items():
            st.write(f"**{feature.replace('_', ' ').title()}**: {desc}")

    with st.form("heart_disease_form"):
        st.subheader(lang['patient_details'])

        col1, col2 = st.columns(2)

        with col1:
            age = st.slider("Age", min_value=1, max_value=120, value=50, step=1, help=lang['feature_descriptions']['age'])
            if not 18 <= age <= 100:
                st.warning(lang['age_warning'])

            sex = st.selectbox("Sex", options=[("Male", 1), ("Female", 0)], format_func=lambda x: x[0], help=lang['feature_descriptions']['sex'])
            chest_pain_type = st.selectbox("Chest Pain Type",
                                           options=[("Typical angina", 1), ("Atypical angina", 2),
                                                    ("Non-anginal pain", 3), ("Asymptomatic", 4)],
                                           format_func=lambda x: x[0], help=lang['feature_descriptions']['chest_pain_type'])
            resting_bp_s = st.number_input("Resting Blood Pressure (mm Hg)", min_value=80, max_value=200, value=120, step=1, help=lang['feature_descriptions']['resting_bp_s'])
            if not 90 <= resting_bp_s <= 180:
                st.warning(lang['bp_warning'])
            cholesterol = st.number_input("Cholesterol (mg/dl)", min_value=100, max_value=600, value=200, step=1, help=lang['feature_descriptions']['cholesterol'])
            if not 120 <= cholesterol <= 300:
                st.info(lang['cholesterol_info'])
            smoke = st.selectbox("Do you smoke?", options=[("No", 0), ("Yes", 1)], format_func=lambda x: x[0], help=lang['feature_descriptions']['smoke'])

        with col2:
            fasting_blood_sugar = st.selectbox("Fasting Blood Sugar > 120 mg/dl",
                                               options=[("False", 0), ("True", 1)],
                                               format_func=lambda x: x[0], help=lang['feature_descriptions']['fasting_blood_sugar'])
            resting_ecg = st.selectbox("Resting ECG",
                                       options=[("Normal", 0), ("ST-T wave abnormality", 1),
                                                ("Left ventricular hypertrophy", 2)],
                                       format_func=lambda x: x[0], help=lang['feature_descriptions']['resting_ecg'])
            max_heart_rate = st.number_input("Max Heart Rate Achieved", min_value=60, max_value=220, value=150, step=1, help=lang['feature_descriptions']['max heart rate'])
            if not 100 <= max_heart_rate <= 200:
                st.info(lang['hr_info'])
            exercise_angina = st.selectbox("Exercise Induced Angina",
                                           options=[("No", 0), ("Yes", 1)],
                                           format_func=lambda x: x[0], help=lang['feature_descriptions']['exercise_angina'])
            oldpeak = st.number_input("Oldpeak (ST depression induced by exercise)", min_value=-2.0, max_value=6.2, value=0.0, step=0.1, help=lang['feature_descriptions']['oldpeak'])
            st_slope = st.selectbox("ST Slope",
                                    options=[("Upsloping", 1), ("Flat", 2), ("Downsloping", 3)],
                                    format_func=lambda x: x[0], help=lang['feature_descriptions']['st_slope'])

        submitted = st.form_submit_button(lang['predict_button'], type="primary")

    if submitted:
        with st.spinner('Predicting...'):
            input_data = pd.DataFrame([[age, sex[1], chest_pain_type[1], resting_bp_s, cholesterol,
                                        fasting_blood_sugar[1], resting_ecg[1], max_heart_rate,
                                        exercise_angina[1], oldpeak, st_slope[1], smoke[1]]],
                                      columns=X.columns)
            prediction = model.predict(input_data)[0]
            prediction_proba = model.predict_proba(input_data)[0]

        st.session_state.last_prediction_results = {
            'input_data': input_data,
            'prediction': prediction,
            'prediction_proba': prediction_proba
        }

        st.markdown("---")
        st.subheader(lang['prediction_result'])

        col_result_text, col_result_gauge = st.columns(2)

        with col_result_text:
            if prediction == 0:
                st.success(lang['no_disease'])
                st.write(f"The model is **{prediction_proba[0]*100:.2f}%** confident that no heart disease is present.")
            else:
                st.error(lang['disease'])
                st.write(f"The model indicates a **{prediction_proba[1]*100:.2f}%** probability of heart disease.")

        # <<< MODIFIED SECTION START: CALLING GAUGE FUNCTION >>>
        with col_result_gauge:
            prob_disease = prediction_proba[1]
            fig_gauge = create_gauge_chart(
                prob_disease, 
                lang['risk_gauge_title'], 
                st.session_state.theme
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        # <<< MODIFIED SECTION END >>>

        st.subheader(lang['input_summary'])
        summary_df = pd.DataFrame({
            "Feature": ["Age", "Sex", "Chest Pain Type", "Resting BP", "Cholesterol", "Fasting BS", "Resting ECG", "Max Heart Rate", "Exercise Angina", "Oldpeak", "ST Slope", "Smoker"],
            "Value": [age, sex[0], chest_pain_type[0], resting_bp_s, cholesterol, fasting_blood_sugar[0], resting_ecg[0], max_heart_rate, exercise_angina[0], oldpeak, st_slope[0], smoke[0]]
        })
        st.table(summary_df)


# --- Page 2: What-If Analysis ---
# <<< MODIFIED SECTION START: NEW ADVANCED WHAT-IF TAB (FIXED) >>>
elif selected_page == lang['tab_whatif']:
    st.title(lang['what_if_analysis_header'])
    st.markdown("Compare the original patient's risk with a new 'what-if' scenario by changing the inputs below.")

    if 'last_prediction_results' not in st.session_state or st.session_state.last_prediction_results is None:
        st.info('Please go to the "Prediction" page and make a prediction first to use this feature.')
    else:
        # Get base results
        base_results = st.session_state.last_prediction_results
        base_input = base_results['input_data']
        base_prediction = base_results['prediction']
        base_proba = base_results['prediction_proba'][1] # Probability of disease

        # Define options for selectboxes
        sex_options = [("Female", 0), ("Male", 1)]
        cp_options = [("Typical angina", 1), ("Atypical angina", 2), ("Non-anginal pain", 3), ("Asymptomatic", 4)]
        fbs_options = [("False", 0), ("True", 1)]
        ecg_options = [("Normal", 0), ("ST-T wave abnormality", 1), ("Left ventricular hypertrophy", 2)]
        exang_options = [("No", 0), ("Yes", 1)]
        slope_options = [("Upsloping", 1), ("Flat", 2), ("Downsloping", 3)]
        smoke_options = [("No", 0), ("Yes", 1)]

        # Find the default index for each selectbox based on the base_input value
        def get_index(options_list, value):
            for i, (label, val) in enumerate(options_list):
                if val == value:
                    return i
            return 0 # Default to first index if not found

        # --- THIS IS THE CORRECTED SECTION ---
        # We now use X.columns[index] to get the correct column name from the loaded data
        
        # Order from Prediction tab: [age, sex, chest_pain_type, resting_bp_s, cholesterol, 
        #                           fasting_blood_sugar, resting_ecg, max_heart_rate, 
        #                           exercise_angina, oldpeak, st_slope, smoke]
        
        base_sex_idx = get_index(sex_options, base_input[X.columns[1]].iloc[0])
        base_cp_idx = get_index(cp_options, base_input[X.columns[2]].iloc[0])
        base_fbs_idx = get_index(fbs_options, base_input[X.columns[5]].iloc[0])
        base_ecg_idx = get_index(ecg_options, base_input[X.columns[6]].iloc[0])
        base_exang_idx = get_index(exang_options, base_input[X.columns[8]].iloc[0])
        base_slope_idx = get_index(slope_options, base_input[X.columns[10]].iloc[0])
        base_smoke_idx = get_index(smoke_options, base_input[X.columns[11]].iloc[0])


        col_base, col_whatif = st.columns(2)

        # --- Column 1: Base Prediction ---
        with col_base:
            st.header("Current Patient")
            
            if base_prediction == 0:
                st.success(lang['no_disease'])
            else:
                st.error(lang['disease'])
                
            fig_gauge_base = create_gauge_chart(
                base_proba, 
                f"Current {lang['risk_gauge_title']}", 
                st.session_state.theme
            )
            st.plotly_chart(fig_gauge_base, use_container_width=True)

            with st.expander("Show Current Inputs", expanded=False):
                # Rename index to be more readable
                display_df = base_input.T.rename(columns={0: 'Value'})
                display_df.index.name = "Feature"
                st.dataframe(display_df)

        # --- Column 2: What-If Scenario ---
        with col_whatif:
            st.header("What-If Scenario")

            with st.form("what_if_form"):
                st.subheader("Modify Patient Details")
                
                c1, c2 = st.columns(2)
                with c1:
                    # --- ALSO CORRECTED THIS SECTION ---
                    age_whatif = st.slider("Age", 1, 120, int(base_input[X.columns[0]].iloc[0]), 1, key="age_whatif")
                    sex_whatif = st.selectbox("Sex", options=sex_options, index=base_sex_idx, format_func=lambda x: x[0], key="sex_whatif")
                    cp_whatif = st.selectbox("Chest Pain Type", options=cp_options, index=base_cp_idx, format_func=lambda x: x[0], key="cp_whatif")
                    bp_whatif = st.number_input("Resting Blood Pressure", 80, 200, int(base_input[X.columns[3]].iloc[0]), 1, key="bp_whatif")
                    chol_whatif = st.number_input("Cholesterol", 100, 600, int(base_input[X.columns[4]].iloc[0]), 1, key="chol_whatif")
                    smoke_whatif = st.selectbox("Do you smoke?", options=smoke_options, index=base_smoke_idx, format_func=lambda x: x[0], key="smoke_whatif")

                with c2:
                    fbs_whatif = st.selectbox("Fasting Blood Sugar > 120 mg/dl", options=fbs_options, index=base_fbs_idx, format_func=lambda x: x[0], key="fbs_whatif")
                    ecg_whatif = st.selectbox("Resting ECG", options=ecg_options, index=base_ecg_idx, format_func=lambda x: x[0], key="ecg_whatif")
                    hr_whatif = st.number_input("Max Heart Rate Achieved", 60, 220, int(base_input[X.columns[7]].iloc[0]), 1, key="hr_whatif")
                    exang_whatif = st.selectbox("Exercise Induced Angina", options=exang_options, index=base_exang_idx, format_func=lambda x: x[0], key="exang_whatif")
                    oldpeak_whatif = st.number_input("Oldpeak", -2.0, 6.2, float(base_input[X.columns[9]].iloc[0]), 0.1, key="oldpeak_whatif")
                    slope_whatif = st.selectbox("ST Slope", options=slope_options, index=base_slope_idx, format_func=lambda x: x[0], key="slope_whatif")

                whatif_submitted = st.form_submit_button("Run What-If Scenario", type="primary")

            # --- Show What-If Results ---
            if whatif_submitted:
                with st.spinner('Calculating new prediction...'):
                    # Collect new data from what-if widgets
                    whatif_data = pd.DataFrame([[
                        age_whatif, sex_whatif[1], cp_whatif[1], bp_whatif, chol_whatif,
                        fbs_whatif[1], ecg_whatif[1], hr_whatif,
                        exang_whatif[1], oldpeak_whatif, slope_whatif[1], smoke_whatif[1]
                    ]], columns=X.columns)
                    
                    # Make new prediction
                    whatif_prediction = model.predict(whatif_data)[0]
                    whatif_proba = model.predict_proba(whatif_data)[0][1] # Probability of disease
                    
                    if whatif_prediction == 0:
                        st.success(f"✅ {lang['no_disease']}")
                    else:
                        st.error(f"🚨 {lang['disease']}")
                    
                    fig_gauge_whatif = create_gauge_chart(
                        whatif_proba, 
                        f"What-If {lang['risk_gauge_title']}", 
                        st.session_state.theme
                    )
                    st.plotly_chart(fig_gauge_whatif, use_container_width=True)

                    # Show a comparison
                    prob_change = whatif_proba - base_proba
                    st.metric(
                        label="Change in Risk Probability",
                        value=f"{whatif_proba:.2%}",
                        delta=f"{prob_change:+.2%}",
                        delta_color="inverse" # Red for increase, Green for decrease
                    )
# <<< MODIFIED SECTION END >>>

# --- Page 3: Model Insights ---
elif selected_page == lang['tab_insights']:
    st.title(lang['insights_title'])
    st.markdown(lang['insights_intro'])

    st.subheader(lang['model_comparison_header'])
    st.markdown(lang['model_comparison_intro'])

    comparison_data = []
    for name, res in model_results.items():
        comparison_data.append({
            'Model': name,
            'Test Accuracy': f"{res['test_accuracy']:.2f}",
            'Cross-Validation Accuracy': f"{res['cv_mean_accuracy']:.2f}"
        })
    comparison_df = pd.DataFrame(comparison_data)
    st.table(comparison_df)

    st.subheader(lang['feature_importance_header'])
    st.markdown(lang['feature_importance_intro'])

    feature_importances = pd.DataFrame({
        'feature': X.columns,
        'importance': model_results['Random Forest']['model'].feature_importances_
    }).sort_values('importance', ascending=True)

    fig_importance = px.bar(
        feature_importances,
        x='importance',
        y='feature',
        orientation='h',
        title=lang['feature_importance_title'],
        labels={'importance': 'Importance Score', 'feature': 'Feature'},
        color='importance',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    st.plotly_chart(fig_importance, use_container_width=True)

    st.subheader("Interactive Dataset Exploration")
    st.markdown("Select a feature and a group to visualize their distributions.")
    col1, col2 = st.columns(2)
    with col1:
        selected_feature_hist = st.selectbox(lang['hist_feature_label'], options=df.columns.drop('target').tolist())
    with col2:
        selected_hue_hist = st.selectbox(lang['hist_group_by_label'], options=['target', 'sex', 'chest_pain_type', 'smoke'])

    fig_hist = px.histogram(
        df,
        x=selected_feature_hist,
        color=selected_hue_hist,
        title=lang['hist_title'].format(selected_feature_hist.replace('_', ' ').title(), selected_hue_hist.replace('_', ' ').title()),
        barmode='overlay'
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader(lang['corr_heatmap_header'])
    fig_corr = px.imshow(
        df.corr(numeric_only=True),
        text_auto=True,
        aspect="auto",
        color_continuous_scale=px.colors.sequential.Viridis,
        title=lang['corr_heatmap_title']
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# --- Page 4: Batch Prediction from CSV ---
elif selected_page == lang['tab_batch']:
    st.title(lang['batch_title'])
    st.markdown(lang['batch_intro'])

    uploaded_file = st.file_uploader(lang['upload_file'], type="csv")

    if uploaded_file is not None:
        try:
            batch_df = pd.read_csv(uploaded_file)
            st.success(lang['file_uploaded_success'])

            required_cols = list(X.columns)
            if not all(col in batch_df.columns for col in required_cols):
                missing_cols = [col for col in required_cols if col not in batch_df.columns]
                st.error(lang['missing_cols_error'].format(missing_cols))
            else:
                batch_df = batch_df[required_cols]

                with st.spinner(lang['batch_predicting_spinner']):
                    predictions = model.predict(batch_df)
                    probabilities = model.predict_proba(batch_df)

                batch_df['Prediction'] = predictions
                batch_df['Probability (No Disease)'] = probabilities[:, 0]
                batch_df['Probability (Disease)'] = probabilities[:, 1]

                st.subheader(lang['batch_results_header'])
                st.write(lang['batch_results_intro'])
                st.dataframe(batch_df)

                csv_output = batch_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=lang['download_predictions'],
                    data=csv_output,
                    file_name="heart_disease_predictions.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(lang['file_processing_error'].format(e))

# --- Page 5: Recommendations ---
elif selected_page == lang['tab_recommendations']:
    st.title(lang['rec_title'])
    st.write(lang['rec_intro_1'])
    st.markdown("---")

    if st.session_state.last_prediction_results:
        results = st.session_state.last_prediction_results
        recommendations = generate_recommendations(results['input_data'], results['prediction'])

        if recommendations:
            for rec in recommendations:
                st.markdown(f"**-** {rec}")
        else:
            st.info("No specific health risks were flagged by the model based on your input. Continue to maintain a healthy lifestyle!")

        st.markdown("---")
        st.write(lang['rec_intro_2'])

    else:
        st.info(lang['rec_warning_nodata'])

# --- Page 6: Local Resources ---
elif selected_page == lang['tab_resources']:
    st.title(lang['res_title'])
    st.markdown(lang['res_intro'])

    selected_city = st.selectbox(lang['res_select_city'], list(local_resources.keys()))

    if selected_city:
        resources = local_resources[selected_city]

        st.markdown("---")
        st.header(lang['res_section_emergency'])
        for service in resources['emergency']:
            st.markdown(f"- **{service['name']}**: {service['number']}")

        st.markdown("---")
        st.header(lang['res_section_hospitals'])
        for hospital in resources['hospitals']:
            st.markdown(f"- **{hospital}**")

        if 'clinics_and_diagnostics' in resources:
            st.markdown("---")
            st.header(lang['res_section_clinics_and_diagnostics'])
            for item in resources['clinics_and_diagnostics']:
                st.markdown(f"- **{item}**")

        if 'diet_and_rehab' in resources:
            st.markdown("---")
            st.header(lang['res_section_diet_and_rehab'])
            for item in resources['diet_and_rehab']:
                st.markdown(f"- **{item}**")

        st.markdown("---")
        st.header(lang['res_section_programs'])
        st.markdown(lang['res_info_ayushman'])
        st.markdown(lang['res_info_npcdcs'])

        st.markdown("---")
        st.header(lang['res_section_ngos'])
        for ngo in resources['ngos']:
            st.markdown(f"- {ngo}")

# --- Page 7: Trend Analysis ---
elif selected_page == lang['tab_trends']:
    st.title(lang['trends_title'])
    st.markdown(lang['trends_intro'])
    st.markdown("---")

    # --- Trend 1: Heart Disease Distribution by Age Group ---
    st.subheader(lang['trends_age_dist_header'])
    st.write(lang['trends_age_dist_intro'])

    # Create age bins for analysis
    bins = [0, 29, 39, 49, 59, 69, 100]
    labels = ['<30', '30-39', '40-49', '50-59', '60-69', '70+']
    df_trends = df.copy()
    df_trends['age_group'] = pd.cut(df_trends['age'], bins=bins, labels=labels, right=False)

    fig_age_dist = px.histogram(
        df_trends,
        x='age_group',
        color='target',
        title=lang['trends_age_dist_header'],
        labels={'age_group': 'Age Group', 'count': 'Number of Patients'},
        category_orders={'age_group': labels},
        color_discrete_map={0: 'lightgreen', 1: 'salmon'}
    )
    st.plotly_chart(fig_age_dist, use_container_width=True)

    # --- Trend 2: Heart Disease Rate by Age Group ---
    st.subheader(lang['trends_age_risk_header'])
    st.write(lang['trends_age_risk_intro'])

    age_risk = df_trends.groupby('age_group')['target'].mean().reset_index()
    fig_age_risk = px.bar(
        age_risk,
        x='age_group',
        y='target',
        title=lang['trends_age_risk_header'],
        labels={'age_group': 'Age Group', 'target': 'Heart Disease Rate (%)'},
        color='target',
        color_continuous_scale='plasma'
    )
    fig_age_risk.update_layout(yaxis_tickformat=".2%", yaxis_range=[0,1])
    st.plotly_chart(fig_age_risk, use_container_width=True)

    # --- Trend 3: Interactive Feature Trend by Age Scatter Plot ---
    st.subheader(lang['trends_feature_by_age_header'])
    st.write(lang['trends_feature_by_age_intro'])

    col_1, col_2 = st.columns(2)
    with col_1:
        x_feature = st.selectbox("Select X-axis Feature", options=df_trends.columns.drop(['target', 'age_group']).tolist(), index=2)
    with col_2:
        y_feature = st.selectbox("Select Y-axis Feature", options=df_trends.columns.drop(['target', 'age_group']).tolist(), index=1)

    fig_scatter = px.scatter(
        df_trends,
        x=x_feature,
        y=y_feature,
        color='age_group',
        symbol='target',
        title=f"{x_feature.title()} vs. {y_feature.title()} by Age Group",
        labels={'age': 'Age', 'target': 'Heart Disease (0=No, 1=Yes)'},
        hover_data=['age', 'sex', 'cholesterol', 'resting bp s']
    )
    st.plotly_chart(fig_scatter, use_container_width=True)