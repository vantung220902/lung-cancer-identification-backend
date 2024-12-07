import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
from PIL import Image, ImageTk  # Requires the Pillow library
import predict
import random

selected_file_path = None


# Function to select an image
def select_image():
    global selected_file_path
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if file_path:
        selected_file_path = file_path
        image_label.config(text=f"Selected image: {os.path.basename(file_path)}")
        load_and_display_image(file_path, image_canvas)  # Load and display the selected image


# Function to load and display an image
def load_and_display_image(image_path, positionGui):
    print('image_path: ' + image_path)
    img = Image.open(image_path)
    img.thumbnail((200, 200))  # Resize the image for display
    img = ImageTk.PhotoImage(img)
    positionGui.create_image(0, 0, anchor=tk.NW, image=img)
    positionGui.image = img  # Store a reference to prevent garbage collection


# Function to predict pneumonia
def predict_pneumonia():
    # Implement your prediction logic here
    # Example: Load the image, preprocess it, and use your model for prediction
    # Display the prediction result in a label or messagebox
    global selected_file_path
    if selected_file_path:
        # Implement your prediction logic here
        # Example: Load the image, preprocess it, and use your model for prediction
        # Display the prediction result in a label or messagebox
        prediction, avg = predict.predictImage(selected_file_path)  # Example function call
        result_label.config(text=f"Predict result: {prediction}")
    else:
        messagebox.showwarning("Warning", "Please select an image first.")


def load_images(folder_path):
    image_files = os.listdir(folder_path)
    random_files = random.sample(image_files, 4)
    return [os.path.join(folder_path, img_file) for img_file in random_files]


def load_samples_images():
    # Load images from the specified folders
    normal_images = load_images("Dataset/train/normal")
    pneumonia_images = load_images("Dataset/train/opacity")

    for index, img_path in enumerate(pneumonia_images):
        pneumonia_images_canvas = tk.Canvas(root, width=200, height=200)
        pneumonia_images_canvas.grid(row=1, column=index + 2, padx=4, pady=10)
        load_and_display_image(img_path, pneumonia_images_canvas)  # Load and display pneumonia images

    for index, img_path in enumerate(normal_images):
        normal_images_canvas = tk.Canvas(root, width=200, height=200)
        normal_images_canvas.grid(row=3, column=index + 2, padx=4, pady=10)
        load_and_display_image(img_path, normal_images_canvas)


# Create the main window
root = tk.Tk()
root.title("Pneumonia Prediction App")

# Create buttons
select_button = tk.Button(root, text="Select Image", command=select_image)
predict_button = tk.Button(root, text="Predict Pneumonia", command=predict_pneumonia)

# Create labels
image_label = tk.Label(root, text="No image selected")
result_label = tk.Label(root, text="")

# Create canvas for displaying the image
image_canvas = tk.Canvas(root, width=200, height=200)

# Arrange widgets in the first column
select_button.grid(row=0, column=0, padx=10, pady=10)
image_canvas.grid(row=1, column=0, padx=10, pady=10)
image_label.grid(row=2, column=0, padx=10, pady=10)
predict_button.grid(row=3, column=0, padx=10, pady=10)
result_label.grid(row=4, column=0, padx=10, pady=10)

# Create a vertical separator
separator = ttk.Separator(root, orient='vertical')
separator.grid(row=0, column=1, rowspan=5, sticky='ns', padx=5)

pneumonia_label = tk.Label(root, text="Example Pneumonia images ")
normal_label = tk.Label(root, text="Example Normal images")

pneumonia_label.grid(row=0, column=2, columnspan=4, padx=10, pady=10)
normal_label.grid(row=2, column=2, columnspan=4, padx=10, pady=10)

other_button = tk.Button(root, text="Other Images", command=load_samples_images)
other_button.grid(row=4, column=2, columnspan=4, padx=10, pady=10)

load_samples_images()
# Start the GUI event loop
root.mainloop()
