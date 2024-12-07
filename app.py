from flask import Flask, request, jsonify
from PIL import Image
import requests
from io import BytesIO
import predict
import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import random
from dotenv import load_dotenv
import numpy

# Load environment variables from a .env file
load_dotenv()


app = Flask(__name__)

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_BUCKET_REGION = os.getenv("S3_BUCKET_REGION", "us-west-2")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")


s3_client = boto3.client(
    's3',
    region_name=S3_BUCKET_REGION,
    # aws_access_key_id=AWS_ACCESS_KEY_ID,
    # aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


@app.route('/get-presigned-url', methods=['GET'])
def get_presigned_url():
    try:
        # Retrieve query parameters
        file_name = request.args.get('file_name')
        file_type = request.args.get('file_type')

        # Validate the query parameters
        if not file_name or not file_type:
            return jsonify({"error": "Invalid request, 'file_name' and 'file_type' are required"}), 400

        # Generate the presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': file_name,
                'ContentType': file_type
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )

        return jsonify({
            "presigned_url": presigned_url,
            "file_url": f"https://{CLOUDFRONT_DOMAIN}/{file_name}"
        })
    except NoCredentialsError:
        return jsonify({"error": "AWS credentials not found"}), 500
    except PartialCredentialsError:
        return jsonify({"error": "Incomplete AWS credentials"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/predict', methods=['POST'])
def predict_pneumonia():
    data = request.json
    if not data or 'image_url' not in data:
        return jsonify({"error": "No image URL provided"}), 400

    image_url = data['image_url']

    try:
        # Download the image from the URL
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an error if the download fails

        # Open the image
        image = Image.open(BytesIO(response.content))

        # Save temporarily to process (optional, can work directly with PIL image)
        temp_path = os.path.join("temp", "temp_image.jpg")
        os.makedirs("temp", exist_ok=True)
        image.save(temp_path)

        # Call your prediction function
        prediction, avg = predict.predictImage(
            temp_path)  # Example function call

        # Clean up the temporary file
        os.remove(temp_path)

        return jsonify({"prediction": prediction, "confidence": numpy.array(avg).tolist()})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to download image: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/examples', methods=['GET'])
def load_samples_images():
    normal_images = []
    pneumonia_images = []
    limit = 20
    try:

        paginator = s3_client.get_paginator('list_objects_v2')

        print("S3_BUCKET_NAME", S3_BUCKET_NAME)

        normal_parameter = {'Bucket': S3_BUCKET_NAME,
                            'Prefix': 'Dataset/train/normal'}

        for page in paginator.paginate(**normal_parameter):
            if 'Contents' in page:
                for obj in page['Contents']:
                    file_key = obj['Key']
                    cloudfront_url = f"https://{CLOUDFRONT_DOMAIN}/{file_key}"
                    normal_images.append(cloudfront_url)
            if len(normal_images) >= limit:
                break

        pneumonia_parameter = {'Bucket': S3_BUCKET_NAME,
                               'Prefix': 'Dataset/train/opacity'}

        for page in paginator.paginate(**pneumonia_parameter):
            if 'Contents' in page:
                for obj in page['Contents']:
                    file_key = obj['Key']
                    cloudfront_url = f"https://{CLOUDFRONT_DOMAIN}/{file_key}"
                    pneumonia_images.append(cloudfront_url)
            if len(pneumonia_images) >= limit:
                break

        normal_samples = random.sample(normal_images, 4)
        pneumonia_samples = random.sample(pneumonia_images, 4)

        return jsonify({
            "normal_samples": normal_samples,
            "pneumonia_samples": pneumonia_samples
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def greeting():
    try:
        return jsonify({
            "status": "OK",
            "message": "Hello World!",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
