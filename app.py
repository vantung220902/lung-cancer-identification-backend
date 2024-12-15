import datetime
from flask_bcrypt import Bcrypt
from flask import Flask, request, jsonify
from PIL import Image
import requests
from io import BytesIO
import predict
import users
import prediction_db
import psycopg2
import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import random
from dotenv import load_dotenv
import numpy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt, create_refresh_token

# Load environment variables from a .env file
load_dotenv()


app = Flask(__name__)
bcrypt = Bcrypt(app)

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_BUCKET_REGION = os.getenv("S3_BUCKET_REGION", "us-west-2")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

app.config['SECRET_KEY'] = SECRET_KEY
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(seconds=3600)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(seconds=3600)

jwt = JWTManager(app)

print("DATABASE_URL", os.getenv("DATABASE_URL"))

def get_database_connection():
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL is not set or empty.")

        conn = psycopg2.connect(db_url)
        print("Database connected successfully")
        return conn
    except psycopg2.OperationalError as e:
        print("OperationalError: Could not connect to the database.")
        print(e)
    except Exception as e:
        print("An unexpected error occurred.")
        print(e)


s3_client = boto3.client(
    's3',
    region_name=S3_BUCKET_REGION,
    # aws_access_key_id=AWS_ACCESS_KEY_ID,
    # aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


@app.route('/get-presigned-url', methods=['GET'])
@jwt_required()
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
@jwt_required()
def predict_pneumonia():
    data = request.json
    if not data or 'image_url' not in data:
        return jsonify({"error": "No image URL provided"}), 400

    image_url = data['image_url']

    try:
        conn = get_database_connection()
        response = requests.get(image_url)
        response.raise_for_status()
        user_id = get_jwt_identity()

        image = Image.open(BytesIO(response.content))

        temp_path = os.path.join("temp", "temp_image.jpg")
        os.makedirs("temp", exist_ok=True)
        image.save(temp_path)

        prediction, avg = predict.predictImage(
            temp_path)

        os.remove(temp_path)
        prediction_db.create_prediction(
            image_url=image_url,
            user_id=user_id,
            confidence=numpy.array(avg[0]).tolist(),
            prediction=prediction, conn=conn)
        return jsonify({"prediction": prediction, "confidence": numpy.array(avg[0]).tolist()})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to download image: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/examples', methods=['GET'])
@jwt_required()
def load_samples_images():
    normal_images = []
    pneumonia_images = []
    limit = 20
    try:

        paginator = s3_client.get_paginator('list_objects_v2')
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


@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        refresh_token = create_refresh_token(
            identity=current_user)

        return jsonify({
            "status": "OK",
            "access_token": access_token,
            "refresh_token": refresh_token,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/my/prediction', methods=['GET'])
@jwt_required()
def get_my_prediction():
    try:
        conn = get_database_connection()
        user_id = get_jwt_identity()
        predictions = prediction_db.find_prediction_by_user_id(
            user_id=user_id, conn=conn)
        conn.close()
        if predictions:
            return jsonify({
                "status": "OK",
                "prediction": predictions
            })

        return jsonify({'message': 'Get Me failed'}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    try:
        conn = get_database_connection()
        user_id = get_jwt_identity()
        found_user = users.find_user_by_id(
            id=user_id, conn=conn)
        conn.close()
        if found_user:
            return jsonify({
                "status": "OK",
                "username": found_user['username'],
                "full_name": found_user['full_name'],
                "id": found_user["id"]
            })

        return jsonify({'message': 'Get Me failed'}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "No username and password provided"}), 400
    try:
        conn = get_database_connection()
        found_user = users.find_user(username=data['username'],
                                     password=data['password'],
                                     conn=conn,
                                     bcrypt=bcrypt)
        conn.close()
        if found_user:
            access_token = create_access_token(identity=str(found_user["id"]))
            refresh_token = create_refresh_token(
                identity=str(found_user["id"]))
            return jsonify({
                "status": "OK",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "username": found_user['username'],
                "full_name": found_user['full_name'],
                "id": found_user["id"]
            })

        return jsonify({'message': 'Login Failed'}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'username' not in data or 'password' not in data or 'full_name' not in data:
        return jsonify({"error": "No username and password and full_name provided"}), 400

    try:
        conn = get_database_connection()
        users.create_user(
            username=data['username'],
            password=data['password'],
            full_name=data['full_name'],
            conn=conn,
            bcrypt=bcrypt)

        conn.close()
        return jsonify({
            "status": "OK",
            "message": "Register user successfully",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/migrate', methods=['GET'])
def migrate():
    try:
        conn = get_database_connection()
        cur = conn.cursor()
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        cur.execute('CREATE TABLE IF NOT EXISTS users(username character varying(255) NOT NULL,'
                    'password character varying(500) NOT NULL,'
                    'full_name character varying(255) NOT NULL,'
                    'id uuid NOT NULL DEFAULT uuid_generate_v4(),'
                    'CONSTRAINT pk_users PRIMARY KEY (id));')
        cur.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS ixuq_users_username ON "users"("username");')

        cur.execute('CREATE TABLE IF NOT EXISTS "prediction"(id serial NOT NULL DEFAULT,'
                    'image_url character varying(1000) NOT NULL,'
                    'prediction character varying(50)  NOT NULL,'
                    'confidence json NOT NULL,'
                    'created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,'
                    'user_id uuid NOT NULL,'
                    'CONSTRAINT pk_prediction PRIMARY KEY (id),'
                    'CONSTRAINT fk_prediction_users FOREIGN KEY (user_id) REFERENCES "users" (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION);')
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({
            "status": "OK",
            "message": "Migrate successfully",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
