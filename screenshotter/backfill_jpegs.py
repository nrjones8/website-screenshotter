import os

import boto3

from format_converter import convert_from_s3_pngs
from news_orgs import WEBSITES
from s3_uploader import get_s3_pathes_for_obj_prefix, upload_to_s3

if __name__ == '__main__':
    s3_client = boto3.client('s3')
    bucket = 'news-screenshots-bucket'
    s3_path_prefixes = []

    for org in WEBSITES:
        s3_path_prefixes.append('raw-screenshots/{}/2019/'.format(org))

    s3_client = boto3.client('s3')

    num_failures = 0
    for prefix in s3_path_prefixes:
        matches = get_s3_pathes_for_obj_prefix(s3_client, bucket, prefix)

        for object_name in matches:
            print('Processing {}'.format(object_name))
            if object_name.endswith('png'):
                try:
                    convert_from_s3_pngs(
                        s3_client,
                        'news-screenshots-bucket',
                        object_name
                    )
                except Exception as e:
                    num_failures += 1
                    print('FAILURE! Failed on {}. Total of {} failures'.format(object_name, num_failures))
            else:
                print('Skipping {} because it is not a png'.format(object_name))
            print('---------')

    print('Done!')
