import requests
import json
import sys
import re
import os
import cloudscraper
from slugify import slugify


class Skillshare(object):
    def __init__(
        self,
        cookie='\n"device_session_id=9488a019-fbdb-4b22-957b-83c244ccd69c; show-like-copy=0; YII_CSRF_TOKEN=aGFxOUtGOHRwYW9pb3FROEF0dEszbVZxeXJEb05PRWQSkeOgOjZCNMEufXqBephtlWYpi2WC1x2aPWb9Q5q2nA%3D%3D; visitor_tracking=utm_campaign%3D%26utm_source%3D%28direct%29%26utm_medium%3D%28none%29%26utm_term%3D%26referrer%3D%26referring_username%3D; first_landing=utm_campaign%3D%26utm_source%3D%28direct%29%26utm_medium%3D%28none%29%26utm_term%3D%26referrer%3D%26referring_username%3D; G_ENABLED_IDPS=google; __stripe_mid=9b2b4cb8-7eaa-4164-95d5-7ce103175a9cf456f9; __cf_bm=7e50f0077f1ce561a736e69c4ff4fa4c468827a7-1630118745-1800-AfPfznKdAJd+hT3XcLcvo+DjBYrofiD1iQvI76SCJ/7xlUL02DF1kLrCiPY3taKED1JP9D+ueU3TquUMChpW9LYPhdJ6r/9m7vGMN35LtXSv; __stripe_sid=02c55bb1-6a9f-4553-a5da-d404cdda62adbd25d1; g_state={&quot;i_p&quot;:1630126023659,&quot;i_l&quot;:1}; PHPSESSID=0a2751ee95ce89ff26cf04bb9c65b762; skillshare_user_=0a603dcc4f926238be6c4387f45dbaf44f79e467a%3A4%3A%7Bi%3A0%3Bs%3A8%3A%2221109653%22%3Bi%3A1%3Bs%3A25%3A%22graceadesina552%40gmail.com%22%3Bi%3A2%3Bi%3A7776000%3Bi%3A3%3Ba%3A4%3A%7Bs%3A8%3A%22username%22%3Bs%3A9%3A%22289054965%22%3Bs%3A10%3A%22login_time%22%3Bs%3A19%3A%222021-08-28%2002%3A47%3A07%22%3Bs%3A10%3A%22touch_time%22%3Bs%3A19%3A%222021-08-28%2002%3A47%3A34%22%3Bs%3A5%3A%22roles%22%3Bs%3A7%3A%22premium%22%3B%7D%7D"\n',
        download_path=os.path.join(os.path.dirname(__file__), "content"),
        pk='BCpkADawqM2OOcM6njnM7hf9EaK6lIFlqiXB0iWjqGWUQjU7R8965xUvIQNqdQbnDTLz0IAO7E6Ir2rIbXJtFdzrGtitoee0n1XXRliD-RH9A-svuvNW9qgo3Bh34HEZjXjG4Nml4iyz3KqF',
        brightcove_account_id=3695997568001,
    ):
        self.cookie = cookie.strip().strip('"')
        self.download_path = download_path
        self.pk = pk.strip()
        self.brightcove_account_id = brightcove_account_id
        self.pythonversion = 3 if sys.version_info >= (3, 0) else 2

    def is_unicode_string(self, string):
        if (self.pythonversion == 3 and isinstance(string, str)) or (self.pythonversion == 2 and isinstance(string, str)):
            return True

        else:
            return False

    def download_course_by_url(self, url):
        m = re.match(r'https://www.skillshare.com/classes/.*?/(\d+)', url)

        if not m:
            raise Exception('Failed to parse class ID from URL')

        self.download_course_by_class_id(m.group(1))

    def download_course_by_class_id(self, class_id):
        data = self.fetch_course_data_by_class_id(class_id=class_id)
        teacher_name = None

        if 'vanity_username' in data['_embedded']['teacher']:
            teacher_name = data['_embedded']['teacher']['vanity_username']

        if not teacher_name:
            teacher_name = data['_embedded']['teacher']['full_name']

        if not teacher_name:
            raise Exception('Failed to read teacher name from data')

        if self.is_unicode_string(teacher_name):
            teacher_name = teacher_name.encode('ascii', 'replace')

        title = data['title']

        if self.is_unicode_string(title):
            title = title.encode('ascii', 'replace')  # ignore any weird char

        base_path = os.path.abspath(
            os.path.join(
                self.download_path,
                slugify(teacher_name),
                slugify(title),
            )
        ).rstrip('/')

        if not os.path.exists(base_path):
            os.makedirs(base_path)

        for s in data['_embedded']['sessions']['_embedded']['sessions']:
            video_id = None
            if 'video_hashed_id' in s and s['video_hashed_id']:
                video_id = s['video_hashed_id'].split(':')[1]

            if not video_id:
                raise Exception('Failed to read video ID from data')

            s_title = s['title']

            if self.is_unicode_string(s_title):
                s_title = s_title.encode('ascii', 'replace')

            file_name = '{} - {}'.format(
                str(s['index'] + 1).zfill(2),
                slugify(s_title),
            )

            self.download_video(
                fpath='{base_path}/{session}.mp4'.format(
                    base_path=base_path,
                    session=file_name,
                ),
                video_id=video_id,
            )

            print('')

    def fetch_course_data_by_class_id(self, class_id):
        url = 'https://api.skillshare.com/classes/{}'.format(class_id)
        scraper = cloudscraper.create_scraper(
            browser={
                'custom': 'Skillshare/4.1.1; Android 5.1.1',
            },
            delay=10
        )

        res = scraper.get(
            url,
            headers={
                'Accept': 'application/vnd.skillshare.class+json;,version=0.8',
                'User-Agent': 'Skillshare/5.3.0; Android 9.0.1',
                'Host': 'api.skillshare.com',
                'Referer': 'https://www.skillshare.com/',
                'cookie': self.cookie,
            }
        )

        if not res.status_code == 200:
            raise Exception('Fetch error, code == {}'.format(res.status_code))

        return res.json()

    def download_video(self, fpath, video_id):
        meta_url = 'https://edge.api.brightcove.com/playback/v1/accounts/{account_id}/videos/{video_id}'.format(
            account_id=self.brightcove_account_id,
            video_id=video_id,
        )

        scraper = cloudscraper.create_scraper(
            browser={
                'custom': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3',
            },
            delay=10
        )

        meta_res = scraper.get(
            meta_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8',
                'Connection': 'keep-alive',
                'Accept': 'application/json;pk={}'.format(self.pk),
                'Origin': 'https://www.skillshare.com'
            }
        )

        if meta_res.status_code != 200:
            raise Exception('Failed to fetch video meta')

        if meta_res.json()['sources'][6]['container'] == 'MP4' and 'src' in meta_res.json()['sources'][6]:
            dl_url = meta_res.json()['sources'][6]['src']
            # break
        else:
            dl_url = meta_res.json()['sources'][1]['src']

        print('Downloading {}...'.format(fpath))

        if os.path.exists(fpath):
            print('Video already downloaded, skipping...')
            return

        with open(fpath, 'wb') as f:
            response = requests.get(dl_url, allow_redirects=True, stream=True)
            total_length = response.headers.get('content-length')

            if not total_length:
                f.write(response.content)

            else:
                dl = 0
                total_length = int(total_length)

                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" %
                                     ('=' * done, ' ' * (50 - done)))
                    sys.stdout.flush()

            print('')
