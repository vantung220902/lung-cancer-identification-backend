# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create and set the working directory in the container
WORKDIR /app

ENV S3_BUCKET_REGION us-west-2
ENV S3_BUCKET_NAME pat-public-storage-qa
ENV CLOUDFRONT_DOMAIN public-storage.pat.datahouse.vn
# Copy the current directory contents into the container at /app
COPY . /app/

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install python3-opencv
RUN apt-get install libgl1 
# Install the required dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port that Flask will run on
EXPOSE 5000

# Define the command to run the application
CMD ["python", "app.py"]
