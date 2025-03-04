import streamlit as st
import time
import datetime
import gspread
import pandas as pd 
import numpy as np
import random
import uuid 
import streamlit_gsheets
from google.oauth2.service_account import Credentials
from streamlit.components.v1 import html
from streamlit_gsheets import GSheetsConnection

# Create a connection object
conn = st.connection("gsheets", type=GSheetsConnection)  
experiment_data = conn.read(worksheet="Sheet1", usecols=list(range(13)), ttl=5)
participant_data = conn.read(worksheet="Sheet2", usecols=list(range(12)), ttl=5)

if 'experiment_responses' not in st.session_state:
        st.session_state.experiment_responses = pd.DataFrame()

# Load the dataset (assuming it's in the same directory)
@st.cache_data(ttl=1800)  # Cache the data for 60 seconds
def load_statements():
    return pd.read_csv("hippocorpus_test_set.csv", sep=";")

# Define progress bar
total_steps = 22

def update_progress():
     if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
     if st.session_state.current_step < total_steps:
         st.session_state.current_step += 1

def show_progress_bar():
    if 'current_step' in st.session_state:
        progress = st.session_state.current_step / total_steps
        st.progress(progress)
    else:
        st.session_state.current_step = 0
        st.progress(0)

def scroll_to_top():
    # Javascript to scroll to top of page
    js = """
        <script>
            window.parent.document.querySelector('section.main').scrollTo(0, 0);
        </script>
    """
    html(js)

# Initialize progress tracking
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

# Retrieve Prolific ID from query parameters
if 'prolific_id' not in st.session_state:
    st.session_state.prolific_id = st.query_params.get("PROLIFIC_PID", ["no_prolific_id"])  

# Initialize participant ID if it doesn't exist
if 'participant_id' not in st.session_state:
    st.session_state.participant_id = str(uuid.uuid4())

# For example page
# Initialize session state to track the sub-page of the example
if 'example_sub_page' not in st.session_state:
    st.session_state.example_sub_page = 1

# Function to navigate between sub-pages
def go_to_next_page():
    if st.session_state.example_sub_page < 3:
        st.session_state.example_sub_page += 1
        st.rerun()
    else:
        update_progress()
        st.session_state.page = 'experiment'
        st.rerun()

def go_to_previous_page():
    if st.session_state.example_sub_page > 1:
        st.session_state.example_sub_page -= 1
        st.rerun()

# Define now the elements to display Confidence later on (this will avoid repetitions later on):
labels = ["Very confident",
            "Confident",
            "Moderately confident",
            "Poorly confident", 
            "Indecisive",
            "Poorly confident",
            "Moderately confident",
            "Confident",
            "Very confident"]

style = "font-size: 12px; text-align: center;"

def display_confidence_labels(labels, style):
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 1, 1, 1, 1.5, 1, 1, 1, 1])
    for col, label in zip([col1, col2, col3, col4, col5, col6, col7, col8, col9], labels):
            col.markdown(f"<div style='{style} color: grey'>{label}</div>", unsafe_allow_html=True)
       
# Define now the elements to display Truthful-Deceptive labels later on (this will avoid repetitions later on):
def display_truthful_deceptive_labels():
    space = st.columns(1)
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        st.markdown("<p style='color: grey; font-size: 0.9em;'><strong>Deceptive</strong></p>", unsafe_allow_html=True)
    with col3:
        st.markdown("<p style='text-align: right; color: grey; font-size: 0.9em;'><strong>Truthful</strong></p>", unsafe_allow_html=True)

####################################################################################################################

## Here starts the main part of the code for running the experiment
# Define Navigation pages
def welcome_page(): 
    show_progress_bar()

    st.title("Welcome to the _'UNMASK THE LIES'_ study")
    st.write("""In this study, we are investigating how people make decisions when evaluating the veracity of statements. 
             We will now give you detailed instructions. **Please read them carefully.**
             \nOnce you complete the experiment, you will be redirected to Prolific.""")
    
    if st.button("Next"):
        update_progress()
        st.session_state.page = 'consent'
        st.rerun()
    

def consent_page():
    show_progress_bar()

    st.title("Informed Consent")

    st.write("This study is conducted by researchers at Tilburg University (The Netherlands)")
    st.write("Name and email address of the principal investigator: Dr Bennett Kleinberg, bennett.kleinberg@tilburguniversity.edu")
    st.markdown(
    """
    The study was reviewed and approved by the university’s ethics committee.
    Please proceed if you agree to the following:

    - I confirm that I have read and understood the information provided for this study.
    - I understand that my participation is voluntary.
    - I understand that I remain fully anonymous, and that I will not be identifiable in any publications or reports on the results of this study.
    - I understand that the data collected in this survey might be made publicly available. I know that no personal information whatsoever will be included in this dataset and that my anonymous research data can be stored for the period of 10 years.
    - I understand that the results of this survey will be reported in academic publications or conference presentations.
    - I understand that I will not benefit financially from this study or from any possible outcome it may result in in the future.
    - I understand that I will be compensated for participation in this study as detailed in the task description on Prolific.
    - I am aware of who I should contact if I wish to lodge a complaint or ask a question.
    """, 
    unsafe_allow_html=True)

    st.write("""Please click on "Accept" if you want to give your consent and proceed with the experiment.
              Otherwise, click  on "Deny" and the experiment ends.""")
    
    col1, col2, col3 = st.columns([1,6,1])
    with col1:
        if st.button("Accept"):
            st.session_state.consent_data = "Accepted"
            update_progress()
            st.session_state.page = 'instructions'
            st.rerun()
    with col3:
        if st.button("Deny"):
            st.session_state.consent_data = "Denied"
            update_progress()
            st.session_state.page = 'end'
            st.rerun()

def instructions_page():
    show_progress_bar()

    st.title("Instructions")
    st.write(":book: In this experiment, you will read **twelve** short statements about past experiences that are either truthful or lies.")
    st.write("Your task is to guess whether each statement is truthful :white_check_mark: or a lie :lying_face:")
    st.write("These statements were randomly selected from a larger dataset where half of all statements are truthful, and half of them are lies.")

    st.write("To help you with your task, we provide you with the predictions of a lie detection algorithm based on artificial intelligence (AI) :robot_face:.")
    st.write("You'll see an example on the next pages.")
    
    st.write("**Please note that you should read the statements carefully, as after the task you will also have to take a quick quiz. The quiz serves to validate your participation.**")

    if st.button("Next"):
        update_progress()
        st.session_state.page = 'example'
        st.rerun()


def example_page():
    show_progress_bar()

    # Title
    st.title("Example Page")

    # Sub-page 1: Instructions and Placeholder Statement
    if st.session_state.example_sub_page == 1:
        st.write("""A statement will be displayed on your screen. You need to read the statement carefully.
                 For this example trial, the statement is just a placeholder.""")

        # Placeholder statement
        st.write("""**Statement:** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
                    Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.""")
    
    # Sub-page 2: AI Slider and Explanation
    elif st.session_state.example_sub_page == 2:
        st.write(":robot_face: **You will be provided with an algorithmic prediction for that statement.** :arrow_down:")
        
        st.slider("AI Judgment:", min_value=-50, max_value=+50, value=35, step=10, disabled=True) 
        st.columns(1)
        display_confidence_labels(labels, style) # Display confidence labels 
        display_truthful_deceptive_labels()  # Display true-false labels 
        
        st.write("""**Explanations:** This slider shows you that the more the judgment is close to **+50**, the more the AI lie-detector is **confident** that the statement is **truthful**.
            The more the judgment is close to **-50**, the more the AI lie-detector is **confident** that the statement is **deceptive**.
            When the slider is close to zero it means that the AI lie-detector doesn't really know whether the statement is truthful or deceptive.""")

        
    # Sub-page 3: Participant's Turn and Explanation
    elif st.session_state.example_sub_page == 3:
        st.write("""**Now that you've read the statement and visualized the AI judgment, it's YOUR turn!**""")
        st.write("""Let's have a go and try moving the slider to make YOUR judgment.
                    This is an example, so your choices have no consequences on this page.""")

        st.slider("Your judgment", min_value=-50, max_value=+50, value=0, step=1, disabled=False)
        display_confidence_labels(labels, style) # Display confidence labels 
        display_truthful_deceptive_labels() # Display true-false labels 

        st.write("""**Explanations:** As before, the more your judgment is close to **+50**, the more you are **confident** that the statement is **truthful**.
            The more your judgment is close to **-50**, the more you are **confident** that the statement is **deceptive**.
            When the slider is close to the zero it means that you don't really know whether the statement is truthful or deceptive.""")
 
    # Navigation Buttons
    col1, col2, col3 = st.columns([1.3, 6.4, 1.3])
    with col1:
        if st.session_state.example_sub_page > 1:
            if st.button("Previous"):
                update_progress()
                go_to_previous_page()
               
    with col3:
        if st.session_state.example_sub_page < 3:
            if st.button("Next"):
                update_progress()
                go_to_next_page()
                
        else:
            if st.button("Let's go"):
                update_progress()
                go_to_next_page()
               
def insert_attention_checks(statements):
    # Create attention check statements
    attention_check_1 = pd.DataFrame([{
        'truth-dec_pairID': 'attention_check_1',
        'text': """This is an attention check and serves to validate your participation. Please put the slider at the position -20. The rest of this statement is just a placeholder.
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
                Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.""",
        'condition': 'attention_check',
        'confidence': -20
    }])
    attention_check_2 = pd.DataFrame([{
        'truth-dec_pairID': 'attention_check_2',
        'text': """This is an attention check and serves to validate your participation. Please put the slider at the position 33. The rest of this statement is just a placeholder.
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
                Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.""",
        'condition': 'attention_check',
        'confidence': 33
    }])

    # Insert attention checks at random positions
    statements.insert(random.randint(0, len(statements)), attention_check_1)
    statements.insert(random.randint(0, len(statements)), attention_check_2)
    return statements 

def experiment_page():
    scroll_to_top()

   # Initialize session state attributes if not already initialized
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'accuracy_condition' not in st.session_state:
        random.seed(st.session_state.participant_id)  # Set a different seed each time
        conditions = random.choice(["accuracy_low", "accuracy_high"])
        st.session_state.accuracy_condition = conditions
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    if f'start_time_{st.session_state.current_index}' not in st.session_state:
        st.session_state[f'start_time_{st.session_state.current_index}'] = time.time()
    if 'slider_moved' not in st.session_state:
        st.session_state.slider_moved = False

    def adjust_ai_confidence(confidence, condition):
        if condition == "accuracy_low":
            if random.random() > 0.54:
                confidence = -confidence  # Flip the confidence
        elif condition == "accuracy_high":
            if random.random() > 0.89:
                confidence = -confidence  # Flip the confidence
        return confidence

    def is_prediction_correct(confidence, statement_condition):
        if statement_condition == "truthful" and confidence >= 0:
            return True
        elif statement_condition == "deceptive" and confidence < 0:
            return True
        return False

    # Load dataset and select 10 random statements once per session
    if 'statements' not in st.session_state:
        data = load_statements()
        selected_statements = []
        for unique_range in range(1, 11):
            statements_in_range = data[data['range'] == unique_range]
            if not statements_in_range.empty:
                selected_statement = statements_in_range.sample(1)
                selected_statements.append(selected_statement)
        
        # Insert attention checks
        selected_statements = insert_attention_checks(selected_statements)

        st.session_state.statements = pd.concat(selected_statements).sample(frac=1).reset_index(drop=True)
        st.session_state.current_index = 0  # Initialize index for the first statement
        st.session_state.submitted = False 
    
    statement_number = st.session_state.current_index + 1 

    # Get current statement based on the index
    statement_row = st.session_state.statements.iloc[st.session_state.current_index]
    
    # Store statement details in session state for consistent access
    st.session_state.statement_id = statement_row['truth-dec_pairID']
    st.session_state.statement_text = statement_row['text']
    st.session_state.statement_condition = statement_row['condition']
    st.session_state.statement_confidence_range = statement_row['confidence_range']

    
    # Adjust AI confidence based on experiment condition
    if f'ai_judgment_{st.session_state.current_index}' not in st.session_state:
        adjusted_confidence = adjust_ai_confidence(int(statement_row['confidence']), st.session_state.accuracy_condition)
        st.session_state[f'ai_judgment_{st.session_state.current_index}'] = adjusted_confidence
        st.session_state[f'correct_prediction_{st.session_state.current_index}'] = is_prediction_correct(adjusted_confidence, statement_row['condition'])
    
    # Retrieve the adjusted AI confidence and prediction correctness
    ai_judgment = st.session_state[f'ai_judgment_{st.session_state.current_index}']
    correct_prediction = st.session_state[f'correct_prediction_{st.session_state.current_index}']

    # Display the statement counter and progress bar
    total_statements = len(st.session_state.statements)    
    st.write(f"**Statement {statement_number} of {total_statements}**.")
    show_progress_bar()

    # Title
    st.title("Experiment Survey")
    
    # Display the statement
    st.write("Please read the following statement carefully:")
    st.write(f"**Statement {statement_number}**: \n{st.session_state.statement_text}")

    # Initialize trial-specific keys
    participant_judgment_key = f'participant_judgment_{st.session_state.current_index}'

    # Display condition-based AI slider message
    if st.session_state.accuracy_condition == 'accuracy_low':
        st.write(":robot_face: **An AI-based lie detector with 54% accuracy has provided the following judgment for this statement** :arrow_down:")
    else:
        st.write(":robot_face: **An AI-based lie detector with 89% accuracy has provided the following judgment for this statement** :arrow_down:")

    if st.session_state.statement_condition == 'attention_check':
        ai_judgment = int(statement_row['confidence'])  # Set AI judgment to the specified value for attention checks
    else:
        ai_judgment = st.session_state[f'ai_judgment_{st.session_state.current_index}']

    # AI's interactive slider
    st.slider("AI Judgment:", min_value=-50, max_value=+50, value=ai_judgment, step=1, disabled=True)
    display_confidence_labels(labels, style)  # Display confidence labels 
    display_truthful_deceptive_labels() # Display true-false labels 

    # Participant's interactive slider
    st.write(":sleuth_or_spy: **Please rate the statement** :arrow_down:")

    def slider_callback():
        st.session_state.slider_moved = True

    if participant_judgment_key not in st.session_state:
        st.session_state[participant_judgment_key] = 0  # Initialize to default

    participant_judgment = st.slider("Your Judgment:", 
                                    min_value=-50, 
                                    max_value=+50, 
                                    value=st.session_state[participant_judgment_key], 
                                    step=1, 
                                    key=participant_judgment_key,
                                    on_change=slider_callback)                       
    
    display_confidence_labels(labels, style)   # Display confidence labels 
    display_truthful_deceptive_labels() # Display true-false labels

    
    # Submit Button Logic
    if st.button("Submit"):
        # Show warning if the slider hasn't been moved
        if not st.session_state.slider_moved:
                st.warning("Please move the slider!", icon="⚠️")
                return # Prevent submission and navigation
            
        # Record duration of the current trial
        st.session_state[f'end_time_{st.session_state.current_index}'] = time.time()
        duration = st.session_state[f'end_time_{st.session_state.current_index}'] - st.session_state[f'start_time_{st.session_state.current_index}']
        st.session_state[f'duration_{st.session_state.current_index}'] = duration
        # Record date
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        response_data = pd.DataFrame(
            [
                {
                    'date': current_date,
                    'accuracy_condition': st.session_state.accuracy_condition,
                    'prolific_id': st.session_state.prolific_id,
                    'participant_id': st.session_state.participant_id,
                    'consent': st.session_state.consent_data,
                    'statement_id': st.session_state.statement_id,
                    'text': st.session_state.statement_text,
                    'statement_condition': st.session_state.statement_condition,
                    'confidence_range': st.session_state.statement_confidence_range,
                    'duration': duration,
                    'correct_prediction': correct_prediction,
                    'ai_judgment': ai_judgment,
                    'participant_judgment': participant_judgment,
                }
            ]
        )

        # Append response data to experiment_data in session state
        st.session_state.experiment_responses = pd.concat([st.session_state.experiment_responses, response_data], ignore_index=True)
        combined_data = pd.concat([experiment_data, st.session_state.experiment_responses], ignore_index=True)

        st.session_state.submitted = True 
        st.success("Your judgment has been recorded!")
        time.sleep(2)
        update_progress()

        # Automatically navigate to the next stimulus or page
        if st.session_state.current_index < len(st.session_state.statements) - 1:
            st.session_state.current_index += 1
            st.session_state.submitted = False  # Reset submission status for the next statement
            st.session_state.slider_moved = False  # Reset slider moved status for the next statement
            st.rerun()  
        else:
            conn.update(worksheet="Sheet1", data=combined_data)
            st.session_state.page = 'final_questions'
            st.rerun()

def final_questions():
    scroll_to_top()
    show_progress_bar()
        
    if 'attention_check_accuracy_selected' not in st.session_state:
        st.session_state.attention_check_accuracy_selected = False
    if 'algo_vs_avg_human_slider_moved' not in st.session_state:
        st.session_state.algo_vs_avg_human_slider_moved = False
    if 'algo_vs_yourself_slider_moved' not in st.session_state:
        st.session_state.algo_vs_yourself_slider_moved = False
    if 'ML_familiarity_slider_moved' not in st.session_state:
        st.session_state.ML_familiarity_slider_moved = False    
    
    def slider_callback(slider_name):
        st.session_state[slider_name] = True

    st.title("Final questions")
    st.write("Please reply to the following questions.")

    # Attention check for the Accuracy condition 
    st.write("1. In this experiment you were shown truthful or deceptive sentences accompanied by the prediction of an AI model. Do you remember how accurate this model was?")
    st.session_state.attention_check_accuracy = st.radio(" ", ["I don't remember", "28%", "54%", "77%", "89%", "93%"], on_change=slider_callback, args=("attention_check_accuracy_selected",))

    # AI vs Average Human
    st.write("2. How good do you think the **average human performance** is compared to the performance of the AI-based lie detector in predicting whether a statement is true or false?")
    st.session_state.algo_vs_avg_human = st.slider("", min_value=0, max_value=10, value=5, step=1, on_change=slider_callback, args=("algo_vs_avg_human_slider_moved",))
    col1, col2, col3, col4, col5, col6 = st.columns([1.5,1,1,1.5,1,1.5])
    with col1:
        st.markdown("<p style='color: grey; font-size: 0.9em;'><strong>Algotithm's performance is better</strong></p>", unsafe_allow_html=True)
    with col4:
        st.markdown("<p style='color: grey; font-size: 0.9em;'><strong>Equal</strong></p>", unsafe_allow_html=True)
    with col6:
        st.markdown("<p style='text-align: right; color: grey; font-size: 0.9em;'><strong>Human performance is better</strong></p>", unsafe_allow_html=True)
    
    # AI vs Participant
    st.write("3. How good do you think **your performance** is compared to the performance of the AI-based lie detector in distinguishing truth from lies?")
    st.session_state.algo_vs_yourself = st.slider(" ", min_value=0, max_value=10, value=5, step=1, on_change=slider_callback, args=("algo_vs_yourself_slider_moved",))
    col1, col2, col3, col4, col5, col6 = st.columns([1.5,1,1,1.5,1,1.5])
    with col1:
        st.markdown("<p style='color: grey; font-size: 0.9em;'><strong>Algotithm's performance is better</strong></p>", unsafe_allow_html=True)
    with col4:
        st.markdown("<p style='color: grey; font-size: 0.9em;'><strong>Equal</strong></p>", unsafe_allow_html=True)
    with col6:
        st.markdown("<p style='text-align: right; color: grey; font-size: 0.9em;'><strong>My performance is better</strong></p>", unsafe_allow_html=True)

    # Familiarity with ML 
    st.write("4. How familiar are you with AI-based algorithms?")
    st.session_state.ML_familiarity = st.slider("  ", min_value=0, max_value=10, value = 5, step=1, on_change=slider_callback, args=("ML_familiarity_slider_moved",))
    col1, col2, col3, col4, col5, col6 = st.columns([1.5,1,1,1.5,1,1.5])
    with col1:
        st.markdown("<p style='color: grey; font-size: 0.9em;'><strong>Not familiar at all</strong></p>", unsafe_allow_html=True)
    with col4:
        st.markdown("<p style='color: grey; font-size: 0.9em;'><strong>Neutral</strong></p>", unsafe_allow_html=True)
    with col6:
        st.markdown("<p style='text-align: right; color: grey; font-size: 0.9em;'><strong>Very familiar</strong></p>", unsafe_allow_html=True)

    if st.button("Next"):
        # Check if all required fields are filled and sliders have been moved
        if not st.session_state.attention_check_accuracy_selected:
            st.warning("Please select an option for question 1 before proceeding.", icon="⚠️")
        elif not st.session_state.algo_vs_avg_human_slider_moved:
            st.warning("Please move the slider to reply question 2 before proceeding.", icon="⚠️")
        elif not st.session_state.algo_vs_yourself_slider_moved:
            st.warning("Please move the slider to reply question 3 before proceeding.", icon="⚠️")
        elif not st.session_state.ML_familiarity_slider_moved:
            st.warning("Please move the slider to reply question 4 before proceeding.", icon="⚠️")
        else:
            update_progress()
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            questions_data = pd.DataFrame(
                [
                    {
                        'date': current_date,
                        'accuracy_condition': st.session_state.accuracy_condition,
                        'prolific_id': st.session_state.prolific_id,
                        'participant_id': st.session_state.participant_id,
                        'consent': st.session_state.consent_data,
                        'attention_check_accuracy': st.session_state.attention_check_accuracy,
                        'algo_vs_avg_human': st.session_state.algo_vs_avg_human,
                        'algo_vs_yourself': st.session_state.algo_vs_yourself,
                        'ML_familiarity': st.session_state.ML_familiarity
                    }
                ]
            )
        
            # Store response_data in session state
            st.session_state.questions_data = questions_data
            st.session_state.page = 'feedback'
            st.rerun()

def feedback_page():
    scroll_to_top()
    show_progress_bar()

    if 'motivation_check' not in st.session_state:
        st.session_state.motivation_check = False
    if 'difficulty_check' not in st.session_state:
        st.session_state.difficulty_check = False    

    def slider_callback(slider_name):
        st.session_state[slider_name] = True
            
    st.title("Feedback")
    st.write("Please provide us with feedback about the study. Your feedback is valuable to us and will help us improve our study.")
    
    st.write("**1. How much were you motivated to perform well?**")
    st.session_state.motivation_scale = st.slider("0 = Not at all, 10 = Very much", min_value=0, max_value=10, value=5, step=1, on_change=slider_callback, args=("motivation_check",))

    st.write("**2. How difficult did you find the study?**")
    st.session_state.difficulty_scale = st.slider("0 = Very easy, 10 = Very difficult", min_value=0, max_value=10, value=5, step=1, on_change=slider_callback, args=("difficulty_check",))
    
    st.write("**3. You can leave here any comment about this experiment (Optional).**")
    st.session_state.feedback = st.text_area("Feedback")

    st.write("Please click on the button below to submit your feedback.")
    
    if st.button("Submit Feedback"): 
        if not st.session_state.motivation_check:
            st.warning("Please move the slider to reply question 1 before proceeding.", icon="⚠️")
        elif not st.session_state.difficulty_check:
            st.warning("Please move the slider to reply question 2 before proceeding.", icon="⚠️")
        else:
                update_progress()
                feedback_data = pd.DataFrame(
                  [
                    {
                        "motivation": st.session_state.motivation_scale,
                        "difficulty": st.session_state.difficulty_scale,
                        "feedback": st.session_state.feedback
                     }
                   ]
                 )
        
                        
                # Retrieve response_data and questions_data from session state
                questions_data = st.session_state.questions_data
        
                # Concatenate all data into a single list
                combined_data = pd.concat([questions_data,feedback_data], axis=1)
                updated_df = pd.concat([participant_data, combined_data], ignore_index=True)
                conn.update(worksheet="Sheet2", data=updated_df)
        
                st.write("Thank you for your feedback.")
                st.session_state.page = 'end'
                st.rerun()
                 
def end_page():
    update_progress()
    show_progress_bar()
    st.title("End of Study")
    st.write("Thank you for participanting in our study. You have exited the study.")
    st.subheader("Debriefing")
    st.write("""This study investigated how people rely on AI judgments. 
            However, for this experiment the AI predictions were fictitious, meaning that we didn't train any model.
            We just manipulated the levels of accuracy and confidence to define at which point humans align the most with AI judgments. 
            If you have any questions, feel free to contact us at:  
            bennet.kleinberg@tilburguniversity.edu  
            r.loconte@tilburguniversity.edu""")
    st.write("Thank you for your valuable contribution.")
   
    if st.button("Return to Prolific"):
        prolific_home_url = "https://www.prolific.com"
        st.markdown(f"<a href='{prolific_home_url}' target='_blank'>Click here if you're not automatically redirected</a>", unsafe_allow_html=True)
        st.markdown(f'<meta http-equiv="refresh" content="0;url={prolific_home_url}">', unsafe_allow_html=True)


# Page Navigation Logic
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'

if st.session_state.page == 'welcome':
    welcome_page()
elif st.session_state.page == 'consent':
    consent_page()
elif st.session_state.page == 'instructions':
    instructions_page()
elif st.session_state.page == 'example':
    example_page()
elif st.session_state.page == 'experiment':
    experiment_page()
elif st.session_state.page == 'final_questions':
    final_questions()
elif st.session_state.page == 'feedback':
    feedback_page()
elif st.session_state.page == 'end':
    end_page()
