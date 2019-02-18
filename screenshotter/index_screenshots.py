import collections
import csv
import datetime

import boto3

from news_orgs import WEBSITES
from s3_uploader import get_s3_pathes_for_obj_prefix

BUCKET = 'news-screenshots-bucket'

ScreenshotMetadata = collections.namedtuple('ScreenshotMetadata', [
    # When it was taken
    'year',
    'month',
    'day',
    'hour',
    'minute',
    'exact_time_ms',
    'iso_time',

    # What website
    'org',

    # Where it's stored
    's3_bucket',
    'object_name'
])


def named_tups_to_csv(list_of_named_tups, outfile_name):
    with open(outfile_name, 'w') as f:
        writer = csv.DictWriter(f, ScreenshotMetadata._fields)
        writer.writeheader()
        for tup in list_of_named_tups:
            writer.writerow(tup._asdict())

    print('Wrote out to {}'.format(outfile_name))


def main():
    all_metadata = []
    s3_path_prefixes = []

    for org in WEBSITES:
        s3_path_prefixes.append('raw-screenshots/{}/2019/'.format(org))

    s3_client = boto3.client('s3')
    bucket = BUCKET

    for prefix in s3_path_prefixes:
        matches = get_s3_pathes_for_obj_prefix(s3_client, bucket, prefix)

        for object_name in matches:
            metadata = {
                'object_name': object_name,
                's3_bucket': bucket
            }
            full_object = s3_client.get_object(
                Bucket=bucket,
                Key=object_name
            )

            metadata.update(full_object['Metadata'])
            dt_object = datetime.datetime(
                year=int(full_object['Metadata']['year']),
                month=int(full_object['Metadata']['month']),
                day=int(full_object['Metadata']['day']),
                hour=int(full_object['Metadata']['hour']),
                minute=int(full_object['Metadata']['minute']),
                tzinfo=datetime.timezone.utc
            )
            metadata['iso_time'] = dt_object.isoformat()
            print('Got {}'.format(object_name))
            all_metadata.append(ScreenshotMetadata(**metadata))
            

    named_tups_to_csv(all_metadata, '/tmp/screenshot_index.csv')

if __name__ == '__main__':
    main()
