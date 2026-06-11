from fastapi import APIRouter, UploadFile
from server.services.flashcard_generator import generate_flashcards
from server.services.text_extraction import extract_text_from_pdf
 
router = APIRouter()
 
@router.post("/flashcards")
async def flashcard_endpoint(file: UploadFile):
    text = extract_text_from_pdf(file)
    flashcards = generate_flashcards(text)
    return {"flashcards": flashcards}

# Flashcard Manager
# File: Routers/flashcards.py
# Description: Code for creating and viewing student academic flashcards


import streamlit as st

def show_flashcards_interface():

    # Set up the section header
    st.header("Creating & Accessing Flashcards")


    # PART 1: CREATE NEW FLASHCARDS

    with st.expander("Create New Flashcard", expanded=False):
        # Get text inputs from the user for both sides of the card
        front = st.text_input("Front Side (Question):")
        back = st.text_input("Back Side (Answer):")


        # Save button logic
        if st.button("Save Flashcard"):
            if front and back:
                # Add the new card data to the persistent memory list
                st.session_state.flashcards.append({"front": front, "back": back})
                st.success("Flashcards added!")
                st.rerun() # Refresh the page to show the changes


    # PART 2: ACCESS & REVIEW FLASHCARDS

    # Only show this section if there are cards in the list
    if st.session_state.flashcards():
        st.write("### Reviewing Cards")


        # Use a slider to let the user select which card to view 
        card_idx = st.slider("Navigate Cards:", 0, len(st.session_state.flashcards)) - 1,
        current_card = st.session_state.flashcards[card_idx]


        # Always display the front side of the selected card 
        st.info(f"**Front:** {current_card['front']}")


        # Only display the back side if the user clicks the flip button 
        if st.button("Flip Card / Show Answers"):
            st.success(f"**Back:** {current_card['back']}")


    else:
        # Message shown if the flashcard list is empty
        st.info("Your deck is currently empty. Expand the creator box above to add carts.")
        


