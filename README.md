API Flow
Check if API is Running

Method: GET
Endpoint: https://api.qa.appraisal.datahouse.asia/
Response:
{
  "status": "OK",
  "message": "Hello World!"
}

Get Example Images
Method: GET
Endpoint: https://api.qa.appraisal.datahouse.asia/examples
Response:
{
    "normal_samples": [
    "https://public-storage.pat.datahouse.vn/Dataset/train/normal/Testne.jpeg",
    "https://public-storage.pat.datahouse.vn/Dataset/train/normal/IM-0757-0001.jpeg",
    "https://public-storage.pat.datahouse.vn/Dataset/train/normal/NORMAL2-IM-0635-0001.jpeg",
    "https://public-storage.pat.datahouse.vn/Dataset/train/normal/Test2ne.jpeg"
    ],
    "pneumonia_samples": [
    "https://public-storage.pat.datahouse.vn/Dataset/train/opacity/person976_virus_1651.jpeg",
    "https://public-storage.pat.datahouse.vn/Dataset/train/opacity/person957_virus_1629.jpeg",
    "https://public-storage.pat.datahouse.vn/Dataset/train/opacity/person81_virus_153.jpeg",
    "https://public-storage.pat.datahouse.vn/Dataset/train/opacity/person967_virus_1640.jpeg"
    ]
}
Generate Presigned URL

Method: GET
Endpoint: https://lung.pat.datahouse.vn/get-presigned-url
Request Query Parameters:
file_name: Path to the file + file name (e.g., Dataset/train/normal/{fileName})
file_type: Type of file (e.g., image/jpeg)
Response:
{
    "file_url": "https://public-storage.pat.datahouse.vn/Dataset/train/normal/Test2ne.jpeg",
    "presigned_url": "https://pat-public-storage-qa.s3.amazonaws.com/Dataset/train/normal/Test2ne.jpeg?AWSAccessKeyId=ASIA2WS5MLMGWBQCPVWA&Signature=2o7FnXEvtd%2BWo31%2BDD%2Bufyl9Vyk%3D&content-type=image%2Fjpeg&x-amz-security-token=IQoJb3JpZ2luX2VjEIv%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaDmFwLXNvdXRoZWFzdC0xIkcwRQIhAMH4uobuaGWVkBije5gahz98iPdXBqru5g0Gy6MfMSXFAiBpE5bk6IRFCe7OkOyHadTmpK9pfNSbGGkEX0C9UlMhkiqMBAhEEAAaDDczNTcwODk5NDMxNyIMTmQTNJd0t0ACzj8zKukD7c%2BGuXJw%2BkCzmH410WPUNGEjHXrsJkgRmhql17zPkJNpoFxSsV7tw7oV%2FRmcWfL%2Fe3caLoHQ11tWxgGBgSFX5L8jZPencaRqvQvEl89EpV2X9b%2FrdzJSGT8J%2Blej5C5rBI5gqiQmQWRFA8UtpJxEE7%2Byk8maViOdEKRbBpZp4BMWyKIkVtiWFRbNf2YKlUiUpTIqRkOARrWmCjUj05%2BHUQAILHKZ3%2FzmiTYgWF8%2FWYDacaqizh4kf0sTkWRikfqC0ap4mJHQAr2mBb6LekpdoxcL1c0CwtiGcM6ez5mf9qvUGhvMOQxuw66YBV1puMD33kn6%2FFJQ1WUpdlE57zKXGgceshfQJQAgQ5fw54ne592L%2B5N1gq3YnZgwhyEhkNsmyghr%2FzhGT1A0shCR1gkRlWozhKTD%2FLcwriJpBgKQ5JYwIuLY2nXyR8N9ln0EkqaxCLs9C3C8om1Hu1ZrvvMMKzVFkv%2BzDWcBzMpnBF%2BksdJiTDOGjQKtPxdUknp8%2BiSEIjiP4sUeK7EiD1qlJZKbhys0iiY4pEnVihNX6LmjWMOVXEl%2FCa0leynaSQJVmgJLZ%2FfZiabJRnHZ2nsPcINqz7Xf1EQrgoLGGCet4V6BcvRlbvYQSuf%2FSKMtIBHYQ60YwqwtS7jxKRh7MM3Z0LoGOqYB3m9mxkCl6Y2wt4698qdBVKgnay6uf9jnSVPljD4EmEcMfEu4%2Fn%2FZb5mLy6J1%2BsbmJPGtSDYy0AYHAePP5ZgbWeUtkRTY0OPPxqRUUqxKgkmYlIaPBx6PMKjIBup2vhfDwkj54bWl2zeoYKfKBr2HRa5FE6txuN83203BokLmpOIs1PQvmAi9k2K%2BYAuZTngUQ25sNXR4GvVZnhfFDmN40I3FnHWgzQ%3D%3D&Expires=1733574092"
}
Upload Selected File
Method: PUT
Endpoint: Use presigned_url from the previous step.
Request Body: Binary file (selected image).
Response: Success or Error based on upload status.

Predict from Uploaded Image
Method: POST
Endpoint: https://lung.pat.datahouse.vn/predict
Request Body:
json
Copy code
{
  "image_url": {file_url}
}
Response:
{
  "confidence": [
    [0.6112215518951416, 0.3887784481048584]
  ],
  "prediction": "Normal"
}

Predict Flow
Call https://api.qa.appraisal.datahouse.asia/examples to get example images.
When a file is selected from the mobile app:
Call https://lung.pat.datahouse.vn/get-presigned-url with file_name and file_type.
Use the presigned_url from the response to PUT the selected file (binary file).
Once the upload is successful:
Use the file_url from the presigned URL response as the image_url in the request body of https://lung.pat.datahouse.vn/predict.
Receive prediction and confidence from the API.

predict flow:
get-presigned-url -> {file_url, presigned_url} -> PUT presigned_url -> predict with body:{image_url:file_url}


