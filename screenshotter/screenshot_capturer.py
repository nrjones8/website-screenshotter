import datetime
import hashlib
import hmac
import logging
import os
import requests
import shutil
import time
import urllib

from s3_uploader import upload_to_s3

logger = logging.getLogger(__name__)

S3_OBJECT_TEMPLATE = 'raw-screenshots/{org}/{year}/{month}/{day}/{hour}/{minute}/screenshot.png'

class UrlboxCapturer(object):
    URL_TEMPLATE = 'https://api.urlbox.io/v1/{api_key}/{generated_token}/{format}?{query_string}'

    def __init__(self, api_key, api_secret, websites, destination_dir, s3_client, s3_bucket_name, write_to_s3, s3_object_template=S3_OBJECT_TEMPLATE):
        self.api_key = api_key
        self.api_secret = api_secret
        self.websites = websites
        self.destination_dir = destination_dir

        self.s3_client = s3_client
        self.s3_bucket_name = s3_bucket_name
        self.write_to_s3 = write_to_s3
        self.s3_object_template = s3_object_template

    def _build_urlbox_url(self, query_params):
        query_string = urllib.parse.urlencode(query_params, True)
        hmac_token = hmac.new(str.encode(self.api_secret), str.encode(query_string), hashlib.sha1)
        token = hmac_token.hexdigest().rstrip('')
        return self.URL_TEMPLATE.format(
            api_key=self.api_key, generated_token=token, format='png', query_string=query_string
        )

    def _download_single_screenshot(self, remote_url, local_path):
        # thanks http://stackoverflow.com/a/18043472
        response = requests.get(remote_url, stream=True)
        with open(local_path, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)

    def download_screenshots(self):
        # Get the current time here, and use the same time for naming all screenshots
        now_dt = datetime.datetime.now(datetime.timezone.utc)

        for website in self.websites:
            url = self._build_urlbox_url({
                'url': website,
                'delay': 5000,
                'ttl': 1 * 60,
            })

            if not os.path.exists(self.destination_dir):
                os.makedirs(self.destination_dir)
            now = time.time()
            object_template_data = {
                'org': website,
                'year': now_dt.year,
                'month': now_dt.month,
                'day': now_dt.day,
                'hour': now_dt.hour,
                'minute': now_dt.minute
            }
            # TODO - fix timezone!
            s3_object_name = S3_OBJECT_TEMPLATE.format(**object_template_data)

            # change thisss
            local_path = '{}/{}_{}.png'.format(self.destination_dir, website, now)
            # this is a janky way to do it, but S3 doesn't have built-in support for streaming large
            # files from memory to S3. This package seems to do it:
            # https://github.com/RaRe-Technologies/smart_open
            # but we can also just download the damn image, then delete the file after we're done
            self._download_single_screenshot(url, local_path)

            logger.info('Downloaded {} to {}'.format(website, local_path))
            metadata_dict = object_template_data.copy()
            metadata_dict.update({
                'exact_time_ms': now
            })
            if self.write_to_s3:
                upload_to_s3(
                    self.s3_client, local_path, self.s3_bucket_name, s3_object_name, metadata_dict
                )
                # we don't really care how efficient this is, it's not blocking anything
                # upload_to_s3(local_path)
                logger.info('Done with {}, saved to {}'.format(website, local_path))
            else:
                logger.info('Not actually saving to S3, would have saved to {}'.format(s3_object_name))
            time.sleep(5)