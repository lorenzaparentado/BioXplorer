import openai
import streamlit as st
import numpy as np


openai.api_key = "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"
global label
label = "dog"

def continue_conversation(user_input):
    
    messages = [
            {"role": "system", "content": 'Respond to this question in a concise manner and only answer to that topic anything beyond default to the cannot not answer'},
            {"role": "user", "content": user_input}
        ]

    gptResponse = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613", messages=messages)
    continuationResponse = gptResponse["choices"][0]["message"]["content"]

    return continuationResponse

prompt = st.text_input("input here")
st.markdown(continue_conversation(prompt))