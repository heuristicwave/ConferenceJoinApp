import json
from PIL import Image, ImageDraw, ImageFont
import qrcode
import boto3
import os


def lambda_handler(event, context):
    # s3 -> download -> font, img -> temp
    s3 = boto3.resource('s3')
    s3.Bucket(os.environ['BUCKET_NAME']).download_file(
        'fonts/SymantecSans-Italic.otf', '/tmp/font.otf')
    s3.Bucket(os.environ['BUCKET_NAME']).download_file(
        'imgs/logo.png', '/tmp/logo.png')

    # records -> get -> table -> getItem
    records = event['Records']
    if records:
        user_id = records[0]['Sns']['Message']
        conf_type = records[0]['Sns']['Subject']

        # dynamodb get
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['TABLE_NAME'])

        r = table.get_item(
            Key={
                'user_id': user_id,
                'type': conf_type
            }
        )
        item = r['Item']
        phone_number = item.get('phone_number', '')
        company_name = item.get('company_name', '')
        user_name = item.get('user_name', '')

        # image build
        W, H = (400, 250)

        logo = Image.open('/tmp/logo.png')
        ttf = '/tmp/font.otf'

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=4,
        )

        qr.add_data(phone_number)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color='black', back_color='white')

        # merge
        img = Image.new("RGB", (W, H), color=(0, 0, 0))
        img.paste(logo, (15, 15), logo).convert('RGB')
        img.paste(qr_img, (15, 100))

        font_m = ImageFont.truetype(ttf, 15)
        font_b = ImageFont.truetype(ttf, 20)
        font_B = ImageFont.truetype(ttf, 22)

        draw = ImageDraw.Draw(img)

        draw.text((150, 110), user_name, fill='#000', font=font_b)
        draw.text((150, 140), f'From {company_name}', fill='#000', font=font_m)

        draw.rectangle((145, 170, 375, 205), fill='#f0f0f0')
        draw.text((150, 170), 'FULL CONFERENCE PASS',
                  fill='#1E8103', font=font_B)

        img.save(f'/tmp/signed.jpg', quality=100)

    return {
        'statusCode': 200,
        'event': event
    }
