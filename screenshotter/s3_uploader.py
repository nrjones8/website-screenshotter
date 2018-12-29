# TODO - rename this file
import datetime
import logging
from pytz import timezone

import boto3

logger = logging.getLogger(__name__)

UTC = timezone('UTC')

def upload_to_s3(s3_client, local_path, bucket, object_name, metadata={}):
    content = open(local_path, 'rb')

    # S3 Metadata needs to be string K/V pairs
    metadata_with_str_kvs = {str(k): str(v) for k, v in metadata.items()}
    response = s3_client.put_object(
        Bucket=bucket,
        Body=content,
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
    # logger.info 'obj: {}, org: {}, ts string: {}. datetime: {}'.format(object_name, news_org, timestamp, as_datetime)

    return news_org, as_datetime

def get_s3_pathes_for_date_range(s3_client, bucket, object_prefix, start_date, end_date):
    """
    s3_client
    bucket
    object_prefix - string, prefix used to search objects. Only objects w/ this prefix are processed
    start_date - datetime
    end_date - datetime

    """
    all_objects = {}
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
            # The key includes the Prefix from above, but we really only want to "file" name. S3
            # objects aren't really files, but you get the idea
            final_name = full_key_path.split(object_prefix)[1]
            news_org, timestamp = parse_object_name(final_name)
            if news_org is None:
                logger.info('Skipping key "{}"'.format(full_key_path))
                continue

            if timestamp > start_date and timestamp < end_date:
                if news_org not in all_objects:
                    all_objects[news_org] = []
                all_objects[news_org].append(full_key_path)


    return all_objects


if __name__ == '__main__':
    logger.info('hey hai hello')
    # start_date = datetime.datetime(2017, 8, 9)
    # end_date = datetime.datetime(2017, 8, 10)
    # s3_client = boto3.client('s3')
    # matches = get_s3_pathes_for_date_range(
    #     s3_client, 'news-screenshots-bucket', 'raw-screenshots/screenshots/', start_date, end_date
    # )

    # # news org, s3 path, timestamp

    # for org, obj in matches.iteritems():
    #     logger.info org
    #     logger.info obj
    #     logger.info '--------'



