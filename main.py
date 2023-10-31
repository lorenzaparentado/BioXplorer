import streamlit as st
from streamlit_option_menu import option_menu
import numpy as np
from keras.preprocessing import image
from keras.applications.vgg16 import VGG16, preprocess_input, decode_predictions
import openai
import streamlit as st
from streamlit_option_menu import option_menu
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import altair as alt
import certifi
import ssl
import geopy.geocoders
from geopy.geocoders import Nominatim

with open('api_key.txt', 'r') as file:
    api_key = file.read().strip()
  
openai.api_key = api_key
if not firebase_admin._apps:
  cred = credentials.Certificate(
      'C:\\Users\\loren\\OneDrive\\Desktop\\BioXplorer\\bioxplorer-firebase-adminsdk-6vcbl-de57cce6b8.json'
  )
  firebase_admin = firebase_admin.initialize_app(
      cred, {'databaseURL': 'https://bioxplorer-default-rtdb.firebaseio.com'})


def store_animal_location(address):
  ref = db.reference('/')
  geolocator = Nominatim(user_agent="appName")
  location = geolocator.geocode(address)

  if location:
    latitude = location.latitude
    longitude = location.longitude

    location_data = {"lat": latitude, "lon": longitude}

    new_location_ref = ref.child("animal_locations").push(location_data)

    return new_location_ref.key
  else:
    return None


def predict_image(img_path):
  summaryResponse = ""
  model = VGG16(weights='imagenet')
  img = image.load_img(img_path, target_size=(224, 224))
  x = image.img_to_array(img)
  x = np.expand_dims(x, axis=0)
  x = preprocess_input(x)
  predictions = model.predict(x, verbose=0)
  decoded_predictions = decode_predictions(
      predictions, top=1)

  global label
  label = decoded_predictions[0][0][1]
  label = label.replace("_", " ").title()
  confidence = decoded_predictions[0][0][2]
  ref = db.reference('/')
  dbLabel = ref.child("animals").push(label)
  
  if confidence >= 0.60:
    messages = [{
        "role":
        "system",
        "content":
        'You are a image detector, from this information create 3 concise points.'
    }, {
        "role": "user",
        "content": label
    }]

    gptResponse = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613",
                                               messages=messages)
    summaryResponse = gptResponse["choices"][0]["message"]["content"]

    out = [label, summaryResponse]
    return out
  else:
    return [
        "Animal not found!",
        "Sorry, we couldn't detect that animal. Please try again."
    ]


def continue_conversation(user_input, animal):

  messages = [{
      "role":
      "system",
      "content":
      f'Pretend you are a biologist-robot and ONLY know about {animal}. I want you to answer questions only about {animal} and you know nothing about other animals. I want your answers to be specific and concise while still being friendly. I also want you to use correct and proper grammar.'
  }, {
      "role": "user",
      "content": user_input
  }]

  gptResponse = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613",
                                             messages=messages)
  continuationResponse = gptResponse["choices"][0]["message"]["content"]

  return continuationResponse


def homePage():
  st.image("images/guy.png", caption="", use_column_width=True)
  st.markdown("---")
  st.markdown("""
        <div style="display: flex; justify-content: center;">
            <h1>Welcome to BioXplorer</h1>
        </div>
        <p>At BioXplore, we're  to providing you with an enriching and immersive experience in the world of animals. Whether you're an avid nature enthusiast or just starting your journey of discovery, we've got something special in store for you.</p>
        <div style="display: flex; justify-content: center;">
            <h1>Explore, Learn, and Interact</h1>
        </div>
        """,
              unsafe_allow_html=True)
  markdown_text = """
- **Discover with the Learning Chatbot:** Our Learning Chatbot is your friendly guide to the natural world. Ask questions, seek facts, and delve into the fascinating realms of animals. Learning has never been this interactive.

- **GPT Animal Detection:** Have an image of a specific animal? Simply submit the image, and our AI-powered GPT model will identify the animal and provide you with fascinating information. It's like having a personal nature encyclopedia right at your fingertips.

- **Contribute and Share:** We believe that knowledge is a collaborative endeavor. That's why we encourage you to be a part of our mission. Share your insights by submitting images and sighting locations, contributing to our growing database of species in our area.

- **Navigate with the Map API:** Explore the boundaries of New Brunswick campus and beyond. Our Map API lets you pinpoint locations, making your virtual journey through the natural world feel truly immersive. The coordinates you find will be stored in our database for future reference.
"""
  st.markdown(markdown_text)
  st.markdown("---")

def mapPage():
  st.header("View Animals on Map")

  st.subheader("Enter Animal Location (Address)")
  address = st.text_input("Address", key="animal_address")

  if st.button("Submit Address", key="submit_address"):
    if address:
      report_id = store_animal_location(address)
      if report_id is not None:
        st.success("Animal location submitted successfully!")
      else:
        st.error(
            "Failed to geocode the address. Please enter a valid address.")
    else:
      st.warning("Please enter an address.")

  ref = db.reference('/')
  location_data_ref = ref.child("animal_locations").get()

  if location_data_ref:
    location_data = location_data_ref.values()
    stored_df = pd.DataFrame(location_data)

    if not stored_df.empty:
      st.map(stored_df)
  else:
    st.info("No animal locations found in the database.")

def uploadPage():
  global uploaded_file
  uploaded_file = st.file_uploader("1. Drag an animal image here",
                                   type=["jpg", "png", "gif", "heic"])

  if uploaded_file is not None:
    st.write("File uploaded!")
    st.markdown("---")
    result = predict_image(uploaded_file)
    animal = result[0]
    facts = result[1]
    st.header(animal)
    st.markdown(facts)
    if animal != "Animal not found!":
      prompt = st.text_input(
          f"2. Have a question about {animal}s? Ask it here!")
      if prompt:
        st.markdown(continue_conversation(prompt, animal))
    st.markdown("---")

def evolutionPage():
    st.title('Animal Dropdown')
    ref = db.reference('animals')
    animals = ref.get()
    if animals:
        animal_names = list(animals.values())
    else:
        animal_names = []

    selected_animal = st.selectbox('Select an Animal', animal_names)

    st.write(f'You selected: {selected_animal}')

    milestones = {
        "15 million years ago": 15000000,
        "5 million years ago": 5000000,
        "2 million years ago": 2000000,
        "500,000 years ago": 500000,
        "Present": 0,
    }
    selected_milestone = st.select_slider("Select Milestone", options=list(milestones.keys()))

    if st.button("Get Evolution Facts"):
        age = milestones[selected_milestone]
        messages = [
            {"role": "system", "content": "give me facts about this animal from this time in terms of evoliuton and in 3 concise bullet points in as if you were talking to a 10 year old"},
            {"role": "user", "content": f"{selected_animal} {age}"}
        ]
        gptResponse = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613", messages=messages)
        summaryResponse = gptResponse["choices"][0]["message"]["content"]
        
        st.write(summaryResponse)

def contactPage():
  st.header("Contact Us")

  user_name = st.text_input("Your Name", key="contact_name")
  user_email = st.text_input("Your Email", key="contact_email")
  user_message = st.text_area("Your Message", key="contact_message")

  if st.button("Submit", key="contact_submit"):
    st.success("Thank you for contacting us! We will get back to you soon.")

  st.header("Helpful Links")

  st.write("https://www.animalalliancenj.org/")
  st.write("https://www.aacnj.org/")
  st.write("http://www.conservewildlifenj.org/")
  st.write("https://www.newjerseyhumanesociety.org/")
  st.write("http://www.wildlifecenterfriends.org/")
  
st.image("images/logo.png", caption="", use_column_width=True)

selected2 = option_menu(None, ["Home", "Upload", "Map", "Evolution", "Contact"],
                        icons=['house', 'cloud-upload', 'map', 'clock', 'person'],
                        menu_icon="cast",
                        default_index=0,
                        orientation="horizontal")
selected2

if selected2 == "Home":
  homePage()
elif selected2 == "Upload":
  uploadPage()
elif selected2 == "Map":
  mapPage()
elif selected2 == "Evolution":
  evolutionPage()
elif selected2 == "Contact":
  contactPage()

st.markdown("""
    <div style="display: flex; justify-content: center; padding: 10px; color: white;">
        <p>&copy; 2023 BioXplorer. All Rights Reserved.</p>
    </div>
    """,
            unsafe_allow_html=True)
