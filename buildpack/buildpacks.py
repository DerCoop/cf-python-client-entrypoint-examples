"""
Example script to handle service brokers.
"""
import os
import argparse
import configparser
import logging as log
import pprint
import time

from cloudfoundry_client.client import CloudFoundryClient
from cloudfoundry_client.errors import InvalidStatusCode


class Buildpacks:
    def __init__(self, target_endpoint, username, passwd, dry_run=False):
        """Constructor for Buildpacks"""
        self.client = self.__login(target_endpoint, username, passwd)
        self.__dry_run = dry_run

    @staticmethod
    def __login(target_endpoint, username, passwd):
        """Method to login to the CF instance"""
        proxy = dict(http=os.environ.get('HTTP_PROXY', ''),
                     https=os.environ.get('HTTPS_PROXY', ''))
        client = CloudFoundryClient(target_endpoint, proxy=proxy, verify=False)
        client.init_with_user_credentials(username, passwd)
        return client

    def list_buildpacks(self):
        return self.client.v3.buildpacks.list()

    def get_buildpack(self, bp_id):
        return self.client.v3.buildpacks.get(bp_id)

    def remove_buildpack(self, bp_id):
        return self.client.v3.buildpacks.remove(bp_id)

    def create_buildpack(self, bp_name):
        return self.client.v3.buildpacks.create(bp_name, position=100)

    def update_buildpack(self, bp_id, bp_name):
        return self.client.v3.buildpacks.update(bp_id, bp_name, position=10)

    def upload_buildpack(self, bp_id, file_name):
        return self.client.v3.buildpacks.upload(bp_id, file_name)


def _parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--credentials-file',
                        action='store',
                        required=True,
                        help='the file with the cloud foundry credentials')
    parser.add_argument('--file',
                        action='store',
                        required=True,
                        help='the buildpack file')
    return parser.parse_args()


def main():
    args = _parse_args()
    credentials = configparser.ConfigParser()
    credentials.read(args.credentials_file)

    bps = Buildpacks(target_endpoint=credentials.get('LOGIN', 'target_endpoint'),
                     username=credentials.get('LOGIN', 'username'),
                     passwd=credentials.get('LOGIN', 'passwd'))

    bp_name = 'testBP'
    print('create buildpack \'{}\''.format(bp_name))
    bp = bps.create_buildpack(bp_name)
    pprint.pprint(bp)
    bp_id = bp['guid']
    try:
        print('id = {}'.format(bp_id))
        print('get one buildpack {}'.format(bp_id))
        pprint.pprint(bps.get_buildpack(bp_id))
        print('upload buildpack {}'.format(bp_id))
        pprint.pprint(bps.upload_buildpack(bp_id, args.file))
        # give the system some time to update all stuff
        time.sleep(5)
        print('update buildpack {}'.format(bp_id))
        pprint.pprint(bps.update_buildpack(bp_id, bp_name))
        print('get one buildpack {}'.format(bp_id))
        pprint.pprint(bps.get_buildpack(bp_id))
    finally:
        print('remove buildpack {}'.format(bp_id))
        print(bps.remove_buildpack(bp_id))
        # wait some time until the BP is removed, this may be a caching problem
        time.sleep(5)
        print('check if the bp is removed')
        try:
            bp_object = bps.get_buildpack(bp_id)
        except InvalidStatusCode as e:
            print('buildpack was removed')
        else:
            print('ERROR: failed to remove buildpack, please do it by hand')
            pprint.pprint(bp_object)


if __name__ == '__main__':
    main()

