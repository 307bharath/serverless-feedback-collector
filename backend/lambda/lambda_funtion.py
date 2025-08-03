import json, boto3, uuid, base64, os
from datetime import datetime

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
ses = boto3.client('ses')

# Get environment variables
table = dynamodb.Table(os.environ['TABLE_NAME'])
bucket_name = os.environ['BUCKET_NAME']

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        message = body.get('message')
        file_data = body.get('file')
        filename = body.get('filename')

        feedback_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        s3_key = None

        # Validate input
        if not email or not message:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"error": "Missing fields"})
            }

        # Upload file to S3 if included
        if file_data and filename:
            s3_key = f"attachments/{feedback_id}/{filename}"
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=base64.b64decode(file_data)
            )

        # Store feedback in DynamoDB
        table.put_item(Item={
            'FeedbackID': feedback_id,
            'Email': email,
            'Message': message,
            'Timestamp': timestamp,
            'S3ObjectKey': s3_key or "None"
        })

        # Send confirmation email
        send_confirmation_email(email,message)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": "Feedback submitted successfully!"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }

# Helper function to send email via SES
def send_confirmation_email(user_email, user_message):
    try:
        response = ses.send_email(
            Source='saimouli352005@gmail.com',  # Must be SES-verified sender
            Destination={'ToAddresses': ['bharadwaja307@gmail.com']},  # Admin recipient
            Message={
                'Subject': {'Data': '📩 New Feedback Received'},
                'Body': {
                    'Text': {
                        'Data': (
                            f"Hello Admin,\n\n"
                            f"A new feedback has been submitted:\n\n"
                            f"From: {user_email}\n"
                            f"Message:\n{user_message}\n\n"
                            f"Regards,\nServerless Feedback System"
                        )
                    }
                }
            }
        )
        print("✅ Admin notification email sent.")
    except Exception as e:
        print("❌ SES Failed:", str(e))
