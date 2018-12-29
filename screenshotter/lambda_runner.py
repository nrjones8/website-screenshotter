import boto3

import argparse
import logging
import os
import sys
import time

from news_orgs import WEBSITES
from s3_uploader import upload_to_s3
from screenshot_capturer import UrlboxCapturer


S3_BUCKET_NAME = 'news-screenshots-bucket'

logger = logging.getLogger(__name__)
log_format = '%(asctime)s %(message)s'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log_file', type=str, default=None)
    args = parser.parse_args()

    if args.log_file is None:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=log_format)
    else:
        # Just overwrite the last file, dealing with logrotate is annoying right now
        logging.basicConfig(filename=args.log_file, level=logging.INFO, format=log_format, filemode='w')

    s3_client = boto3.client('s3')

    urlbox_api_key = os.environ.get('URLBOX_API_KEY')
    if urlbox_api_key is None:
        logger.error('Missing API key, exiting...')
        sys.exit(1)

    urlbox_api_secret = os.environ.get('URLBOX_API_SECRET')

    if urlbox_api_secret is None:
        logger.error('Missing API secret, exiting...')
        sys.exit(1)

    downloader = UrlboxCapturer(
        urlbox_api_key,
        urlbox_api_secret,
        WEBSITES,
        '/tmp/website-screenshots',
        s3_client,
        S3_BUCKET_NAME,
        True
    )

    logger.info('Starting runner for websites: {}'.format(WEBSITES))
    downloader.download_screenshots()

if __name__ == '__main__':
    main()

