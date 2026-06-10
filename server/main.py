"Project Name: AI Academic Tutor bot "
"Description: A streamlit-based educational platform featuring interactive AI chat, Retrieval-Augment Generation (RAG), study guide synthesis, dynamic flashcard creation, and customizable self-assessment quizzes."



import streamlit as st

# 1. APPLICATION AND PAGE CONFIGURATION
# Purpose: Sets up metadata and basic viewport settings for the web application.

st.set_page_config(
    page_title="Academic AI Tutor",
    page_icon="🎓",
    layout="wide"  # Leverage full horizontal screen space for side-by-side modules
)



# 2. STATE MANAGEMENT (SESSION STATE INITIALIZATION)
# Purpose: Streamlit architecture re-runs the entire script on user interaction.
# Storing variables in "st.session_state" ensures data persists between clicks.


# Keep track of the current chat message log
if "chat-history" not in st.session_state:
    st.session_state.chat_history = []


# Dictionary Store for saving past sessions: {"Title Key": [Array of Message Objects]}
if "saved_chats" not in st.session_state:
    st.session_state.saved_chats = {}


# Lists of dicts for user-generated flashcards (Contains a sample card for demo)
if "flashcards" not in st.session_state:
    st.session_state.flashcards = [{"front": "What does RAG stand for?", "back": "Retrieve-Augmented Generation"}]


# Quiz variable tracking custom question, active question pointer, and final score
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "current_quiz_idx" not in st.session_state:
    st.session_state.current_quiz_idx = 0
if "score" not in st.session_state:
    st.session_state.score = 0



# 3. SIDEBAR NAVIGATION & COLLAPSIBLE SAVED CHATS
# Purpose: Provides a persistent global control panel for navigating sections
# and managing cached conversation states.

with st.sidebar:
    st.title("🎓 AI Academic Tutor")

    # Global module navigation toggle
    app_mode = st.radio(
        "Select a Module:",
        ["A Tutor Chat", "Study GUide (RAG)", "Flashcards", "Quiz Mode"]
    )

    st.divider()

    # FEATURE: Collapsible Saved Chats
    # Uses 'st.expander' to collapse history, keeping the sidebar layout clean.
    with st.expander("💬 Collabsible Saved Chats", expanded=True):
        if st.session_state.saved_chats:
            # Iterates over dictionary keys to dynamically render reload buttons
            for chat_title in list(st.session_state.saved_chats.keys()):
                if st.button(chat_title, key=f"load_{chat_title}"):
                    st.session_state.chat_history = st.session_state.saved_chats[chat_title]
                else:
                    st.caption("No saved converstions yet.")

                st.write("----")


                # Action handler to capture and snapshot the active runtime chat log
                if st.button("💾 Save Current Chat Session", use_container_width=True):
                    if st.session_state.chat_history:
                        # String slice: Auto-creates a title using the first 25 characters of the user prompt
                        title_preview = st.session_state.chat_history[0]["content"][:25] + "..."
                        st.session_state.saved_chats[title_preview] = list(st.session_state.chat_history)
                        st.toast("Chat saved successfully!")
                        st.rerun() # Forces immediate visual update to show the new saved entry
                    else:
                        st.warning("Cannot save an empty chat.")


# 1. MODELES & CORE INTERFACES


# AI TUTOR CHAT 

if app_mode == "AI Tutor Chat":
    st.header("💬 AI Tutor Chat")

    # Iterates and renders the ongoing converstion history natively
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    
    # Listens for fresh user string input from the standard entry widget
    if user_query := st.chat_input("Ask a question about your course materials..."):
        # Append and display user query
        with st.chat_message("user"):
            st.write(user_query)
        st.session_state.chat_history.appned({"role": "user", "content": user_query})

        # Append and display dynamic assistant response placeholder
        with st.chat_message("assistant"):
            # NOTE FOR DEVELOPER/CURSOR: Hook your chosen LLM endpoint API response text here
            ai_response = f"This is where your Composer model will generate a real answer to: '{user_query}'."
            st.write(ai_response)
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})



# MODULE 2: STUDY GUIDE GENERATOR & INTERACTIVE RAG PIPELINE

elif app_mode == "Study Guide (RAG)":
    st.header("📚 Interactive Study Guide Generator")
    st.write("Upload lecture notes, PDFs, or slides to extract key concepts.")


    # Accepts binary document formats for text parsing pipeline
    uploaded_file = st.file_uploader("Drop your course ducuments here", type=["pdf", "txt"])
    
    if uploaded_file is not None:
        st.success("Document uploaded successfully!")

        # NOTE FOR DEVELOPER/CURSOR:  Place text extraction, embedding models (OpenAI/Ollama),
        # and vector vector-store operations (Chroma/ FAISS) here to swap mock data with live analysis.
        guide_header = "### 📖 Interactive Study Notes\n"
        guide_body = (
            "**Key Concept 1:** Retrieval-Augmented Generation (RAG)\n"
            "- It combines LLMs with an external knowledge base.\n\n"
            "**Key Concept 2:** Vector Databases\n"
            "- Used to index data chunks for rapid searching."
        )
        full_guide = guide_header + guide_body

        #FEATURE: Interactive Display
        st.markdown(full_guide)

        # FEATURE: Data Download Capability
        # Converts output dinamically into a text stream for instant file-system downloads
        st.download_button(
            label ="📥 Download Study Guide",
            data =full_guide,
            file_name="AI_Tutor_Study_Guide.txt",
            mime="text/plain",
            use_container_width=True
        )



# MODULE 3: FLASHCARDS (CREATION & ACCESS MANAGEMENT)

elif app_mode == "Flashcards":
    st.header("🗂️ Creating & Accessing Flashcards")


    # FEATURE: Flashcard Creation Layout
    with st.expander("Create New Flashcard", expanded=False):
        front = st.text_input("Front Side (Concept/Question):")
        back= st.text_input("Back Side (Definition/ Answer):")
        if st.button("Save Flashcard"):
            if front and back:
                #Appends input dictionary directly to persistent session state array 
                st.session_state.flashcards.append({"front": front, "back": back})
                st.success("Flashcard added!")
                st.rerun()

    # FEATURE: Flashcard Access Management
    if st.session_state.flashcards:
        st.write("### Reviewing Cards")
        # Slider works as an explicit deck indexing control mechanic
        card_idx = st.slider("Navigate Cards:", 0, len(st.session_state.flashcards) -1, 0)
        current_card = st.session_state.flashcards[card_idx]

        # Renders the question view natively
        st.info(f"**Front:** {current_card['front']}")

        # Evaluates hidden answer data state on explicit user click event triggers 
        if st.button("👀 Flip Card / Show Answer"):
            st.success(f"**Back:** {current_card['back']}")
        else:
            st.info("Your deck is currently empty. Expand the creatro box above to ass cards.")



# MODULE 4: QUIZ CAPABILITY (DYNAMIC SELF-ASSESSMENT)

elif app_mode == "Quiz Mode":
    st.header("🧠 Quiz Capability")


    # Structuring mock assessment database if array is empty
    if not st.session_state.quiz_questions:
        st.session_state.quiz_questions = [
            {"q": "What is the primary library used for this UI?", "options": ["Flask", "Streamlit", "Django"], "a": "Streamlit"},
            {"q": "Where does RAG fetch data from?", "options": ["An external vector database", "Pre-trained LLM weights only", "Hardcoded arrays"], "a": "An external vector database"}
        ]


    # Validates if pointer index is still within quiz data array bounds 
    if st.session_state.current_quiz_idx < len(st.session_state.quiz_questions):
        current_q = st.session_state.quiz_questions[st.session_state.current_quiz_idx]

        st.write(f"**Question {st.session_state.current_quiz_idx + 1}:**")
        st.subheader(current_q['q'])


        user_choice = st.radio("Choose one:", current_q['options'], key=f"quiz_opt_{st.session_state.current_quiz_idx}")

        
        if st.button("Submit Answer"):
            # Conditional evaluation engine grading user response against the correct answer key
            if user_choice == current_q['a']:
                st.success("Exellent! That is correct.")
                st.session_state.score += 1
            else:
                st.error(f"Not quite. The correct answer was: {current_q['a']}")

            
            # Increments poiter state to stagethe upcoming question index
            st.session_state.current_quiz_idx += 1
            st.button("Move to Next Question")

    else:
        # Final evaluation dashboard view triggered on array exhaustion
        st.balloons()
        st.subheader("🏁 Quiz Complete!")
        # Display clear metrics using standard st. metric KPI boxes
        st.metric(label="Your Score", value=f"{st.session_state.score} / {len(st.session_state.quiz_questions)}")

        #Reset routine restoring base scoring and indexing states
        if st.button("Retake Quiz!"):
            st.session_state.current_quiz_idx = 0
            st.session_state.score = 0
            st.rerun()


            








