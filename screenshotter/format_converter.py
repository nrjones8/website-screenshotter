import os

import boto3
from PIL import Image

from s3_uploader import upload_to_s3

def convert_to_jpeg(input_path, output_path, log_names=True):
    original = Image.open(input_path)
    # https://github.com/python-pillow/Pillow/issues/2609#issuecomment-313841918
    converted = original.convert('RGB')
    converted.save(output_path)
    if log_names:
        print('Converted {} to jpeg and saved it to {}'.format(input_path, output_path))

def convert_from_s3_pngs(s3_client, bucket_name, source_object_name):
    original_file_path = '/tmp/temp_screenshot.png'
    new_file_path = '/tmp/temp_screenshot_as_jpeg.jpeg'
    s3_client.download_file(bucket_name, source_object_name, original_file_path)
    convert_to_jpeg(original_file_path, new_file_path)

    s3_object = s3_client.get_object(
        Bucket=bucket_name,
        Key=source_object_name
    )
    new_object_name = source_object_name.replace('.png', '.jpeg')

    source_metadata = s3_object['Metadata']
    jpeg_metadata = {k: v for k, v in s3_object['Metadata'].items()}
    jpeg_metadata['source'] = 'png_to_jpeg_conversion'

    try:
        upload_to_s3(
            s3_client,
            new_file_path,
            bucket_name,
            new_object_name,
            metadata=jpeg_metadata,
            content_type='image/jpeg'
        )
        # TODO - use a logger
        print('{} was source'.format(source_object_name))
        print('{} was the new path'.format(new_object_name))
    except e:
        print('Got an exception trying to upload to S3 - did not delete local files')
        raise e
    os.remove(original_file_path)
    print('Removed {}'.format(original_file_path))
    os.remove(new_file_path)
    print('Removed {}'.format(new_file_path))

if __name__ == '__main__':
    s3_client = boto3.client('s3')
    convert_from_s3_pngs(s3_client, 'news-screenshots-bucket', 'raw-screenshots/nytimes.com/2019/1/4/13/2/screenshot.png')
    print('Done')
