import streamlit as st
from pathlib import Path
import pickle as pkl
from PIL import Image
import os
import numpy as np
import pandas as pd
import cv2
import tensorflow as tf
from IPython.display import display
import matplotlib as mpl
import matplotlib.pyplot as plt
import tensorflow as tf
import tensorflow.keras as keras
import seaborn as sns
from skimage.io import imread, imsave
from skimage.transform import resize
from sklearn.model_selection import train_test_split
import tensorflow.keras.backend as K
import matplotlib.image as img
from tensorflow.keras.models import load_model




#Define Some Functions for prediction :

last_conv_layer_name = "Top_Conv_Layer"

def get_img_array(img, size = (224 , 224)):
    image = np.array(img)
    # image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    resized_image = cv2.resize(image, (224,224))
    resized_image = resized_image.reshape(-1,224,224,3)
    resized_image = np.array(resized_image)
    return resized_image
    # img = keras.utils.load_img(img_path, target_size=size)
    # array = keras.utils.img_to_array(img)
    # array = np.expand_dims(array, axis=0)
    # return array


def make_gradcam_heatmap(img_array, model , last_conv_layer_name = last_conv_layer_name, pred_index=None):
    # First, we create a model that maps the input image to the activations
    # of the last conv layer as well as the output predictions
    grad_model = keras.models.Model(
        model.inputs, [model.get_layer(last_conv_layer_name).output, model.output]
    )

    # Then, we compute the gradient of the top predicted class for our input image
    # with respect to the activations of the last conv layer
    with tf.GradientTape() as tape:
        last_conv_layer_output, preds = grad_model(img_array)
        if pred_index is None:
            pred_index = tf.argmax(preds[0])
        class_channel = preds[:, pred_index]

    # This is the gradient of the output neuron (top predicted or chosen)
    # with regard to the output feature map of the last conv layer
    grads = tape.gradient(class_channel, last_conv_layer_output)

    # This is a vector where each entry is the mean intensity of the gradient
    # over a specific feature map channel
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # We multiply each channel in the feature map array
    # by "how important this channel is" with regard to the top predicted class
    # then sum all the channels to obtain the heatmap class activation
    last_conv_layer_output = last_conv_layer_output[0]
    heatmap = last_conv_layer_output @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)

    # For visualization purpose, we will also normalize the heatmap between 0 & 1
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    return heatmap.numpy()

def save_and_display_gradcam(img, heatmap, cam_path="cam.jpg", alpha=0.4 , view = False):
    # Load the original image
    img = np.array(img)
    # img = keras.utils.load_img(img_path)
    # img = keras.utils.img_to_array(img)

    # Rescale heatmap to a range 0-255
    heatmap = np.uint8(255 * heatmap)

    # Use jet colormap to colorize heatmap
    jet = mpl.colormaps["jet"]

    # Use RGB values of the colormap
    jet_colors = jet(np.arange(256))[:, :3]
    jet_heatmap = jet_colors[heatmap]

    # Create an image with RGB colorized heatmap
    jet_heatmap = keras.utils.array_to_img(jet_heatmap)
    jet_heatmap = jet_heatmap.resize((img.shape[1], img.shape[0]))
    jet_heatmap = keras.utils.img_to_array(jet_heatmap)

    # Superimpose the heatmap on original image
    superimposed_img = jet_heatmap * alpha + img
    superimposed_img = keras.utils.array_to_img(superimposed_img)

    # Save the superimposed image
    superimposed_img.save(cam_path)

    # Display Grad CAM
    if view :
        display(Image(cam_path))

        
     
def decode_predictions(preds):
    classes = ['Glioma' , 'Meningioma' , 'No Tumor' , 'Pituitary']
    prediction = classes[np.argmax(preds)]
    return prediction



def make_prediction (img , model, last_conv_layer_name = last_conv_layer_name , campath = "cam.jpeg" , view = False):
    image = get_img_array(img)
    img_array = get_img_array(img, size=(224 , 224))
    preds = model.predict(img_array)
    heatmap = make_gradcam_heatmap(img_array, model, last_conv_layer_name)
    save_and_display_gradcam(img, heatmap , cam_path=campath , view = view)
    return [campath , decode_predictions(preds)]

# Prediction base function
def prediction():
    st.title("For Brain Tumor prediction, provide Brain X-ray image")
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if st.button("Predict"):
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Upload Image")

            # Load the Model
            model = load_model("./brain_tumor_prediction.h5")
            # file_path = "./brain_tumor_model.pkl"
            # with open(file_path, "rb") as file:
            #     model = pkl.load(file)


            # Prediction
            campath, prediction = make_prediction(image, model, campath="123.jpeg", view=False)
            st.title(prediction)
            test_img = img.imread(campath)
            st.image(test_img, caption="Predicted Image")


# main function
st.title("Welcome to our Medical Image Analysis website")

# Login Page
st.sidebar.title("First Login Here")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type='password')

if st.sidebar.button("Login"):
    if username == "amit" and password == "12345":
        st.success("Logged in as {}".format(username))
        st.session_state["logged_in"] = True
    else:
        st.error("Invalid Credentials")

if "logged_in" in st.session_state:
    st.sidebar.title("Select Detection Option")
    option = st.sidebar.selectbox("Select Option", ["Brain Tumor"])
    
    if option == "Brain Tumor":
        prediction()
    elif option == "Pneumonia Detection":
        pass
    elif option == "Lung Cancer Detection":
        pass
