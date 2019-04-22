# TODO - rename this file
import datetime
import logging
from pytz import timezone

import boto3

logger = logging.getLogger(__name__)

UTC = timezone('UTC')
S3_OBJECT_TEMPLATE = 'raw-screenshots/{org}/{year}/{month}/{day}/{hour}/{minute}/screenshot.png'

def upload_to_s3(s3_client, local_path, bucket, object_name, metadata={}, content_type='image/png'):
    content = open(local_path, 'rb')

    # S3 Metadata needs to be string K/V pairs
    metadata_with_str_kvs = {str(k): str(v) for k, v in metadata.items()}
    response = s3_client.put_object(
        Bucket=bucket,
        Body=content,
        ContentType=content_type,
        Key=object_name,
        # Should these be tags or metadata?
        Metadata=metadata_with_str_kvs
    )
    logger.info('S3 response:', response)
    # Check for a response and for one expected field
    if response is None or response.get('ETag', None) is None:
        logger.info('No response attempting to put {}, continuing...'.format(object_name))
    else:
        logger.info('Cool, object {} to bucket {}'.format(object_name, bucket))

def parse_object_name(object_name):
    """
    object_name should look like 'wsj.com_1502568926.67.png', i.e.
    '{org}_{timestamp}.png'

    Return (name of news org, datetime of the screenshot)
    """
    # this is ugly and a little confusing, but will let us use this function again if the object
    # name is actually a full path
    if '/' in object_name:
        object_name = object_name.split('/')[-1]

    parts = object_name.split('_')

    if len(parts) != 2:
        logger.info('Having trouble with object named {}'.format(object_name))
        return None, None
    news_org = parts[0]
    timestamp = float(parts[1].split('.')[0])
    as_datetime = datetime.datetime.fromtimestamp(timestamp, UTC)

    return news_org, as_datetime

def get_s3_pathes_for_obj_prefix(s3_client, bucket, object_prefix):
    """
    s3_client
    bucket
    object_prefix - string, prefix used to search objects. Only objects w/ this prefix are processed

    """
    all_objects = []
    num_objects = 0
    more_objects = True
    next_token = None

    while more_objects:
        request_args = {
            'Bucket': bucket,
            'Prefix': object_prefix
        }
        if next_token is not None:
            request_args['ContinuationToken'] = next_token
        response = s3_client.list_objects_v2(**request_args)

        more_objects = response['IsTruncated']
        next_token = response.get('NextContinuationToken')

        for obj in response['Contents']:
            full_key_path = obj['Key']
            all_objects.append(full_key_path)
        if num_objects % 20 == 0:
            print('Have {} objects so far'.format(len(all_objects)))
            print('Last one was: {}'.format(full_key_path))


    return all_objects
