import os

import keras.models
import cv2
import numpy as np
import tensorflow as tf
import keras.preprocessing.image


def predict(image_path, model):
    im = cv2.imread(image_path)
    test_image = np.asarray(im)
    processed_test_image = process_image(test_image)
    processed_test_image = np.expand_dims(processed_test_image, axis=0)
    ps = model.predict(processed_test_image)
    print("Predict: ", ps)
    return ps


def process_image(image):
    image = tf.cast(image, tf.float32)
    image = tf.image.resize(image, (224, 224))
    image = image / 255
    image = image.numpy()
    return image


def predictImage(pathImage):

    folder_path = 'models/'
    files = os.listdir(folder_path)
    predictsModels = []

    for file_name in files:
        print("file_name :" + file_name)
        if file_name.endswith('.keras'):
            model_path = os.path.join(folder_path, file_name)
            print("model_path",model_path)
            loaded_model = keras.models.load_model(model_path)
            predictions = predict(image_path=pathImage, model=loaded_model)
            predictsModels.append(predictions)

    print("Result all models: ", predictsModels)
    avgPredicts = np.mean(predictsModels, axis=0)
    print("Avg: ", avgPredicts)
    class_idx = np.argmax(avgPredicts, axis=1)[0]
    class_labels = ["Normal", "Pneumonia"]
    predicted_class = class_labels[class_idx]

    return predicted_class, avgPredicts


if __name__ == '__main__':
    predictImage('/Dataset/val/opacity/person1398_bacteria_3548.jpeg')