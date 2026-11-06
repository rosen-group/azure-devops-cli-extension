# ROSEN fork: opt-in allowlist for Azure DevOps Server hosts (AZURE_DEVOPS_EXT_ONPREM_HOSTS).

import os
import unittest
from unittest import mock

from azext_devops.dev.common import services
from azext_devops.dev.common.services import check_organization_in_azure, get_token_from_az_logins
from azext_devops.dev.common.uri import (canonicalize_azure_devops_organization_url,
                                         get_allowed_onprem_hosts,
                                         is_azure_devops_host,
                                         is_onprem_organization_url,
                                         organization_url_from_azure_devops_url,
                                         parse_azure_devops_git_remote)
from azext_devops.dev.common.vsts_git_url_info import _is_azure_devops_host

HOST = 'tfs.roseninspection.net'
ENV = {'AZURE_DEVOPS_EXT_ONPREM_HOSTS': HOST}


class TestOnPremAllowlist(unittest.TestCase):

    def test_disabled_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(canonicalize_azure_devops_organization_url('https://' + HOST + '/tfs/Coll'))
            self.assertFalse(check_organization_in_azure('https://' + HOST + '/tfs/Coll'))

    def test_accepts_allowlisted_host(self):
        with mock.patch.dict(os.environ, ENV, clear=True):
            for url, expected in [
                    ('https://tfs.roseninspection.net/tfs/Coll', 'https://tfs.roseninspection.net/tfs/Coll'),
                    ('https://TFS.RoseninSpection.net/tfs/Coll/', 'https://tfs.roseninspection.net/tfs/Coll'),
                    ('https://tfs.roseninspection.net:443/tfs/Coll', 'https://tfs.roseninspection.net/tfs/Coll'),
                    ('https://tfs.roseninspection.net/Coll', 'https://tfs.roseninspection.net/Coll')]:
                self.assertEqual(canonicalize_azure_devops_organization_url(url), expected)
            self.assertTrue(check_organization_in_azure('https://' + HOST + '/tfs/Coll'))
            self.assertTrue(is_onprem_organization_url('https://' + HOST + '/tfs/Coll'))

    def test_rejects_lookalikes_and_bad_forms(self):
        with mock.patch.dict(os.environ, ENV, clear=True):
            for url in [
                    'https://tfs.roseninspection.net.evil.com/tfs/Coll',
                    'https://evil.com/tfs.roseninspection.net',
                    'https://evil.com/tfs.roseninspection.net/tfs/Coll',
                    'https://user@tfs.roseninspection.net/tfs/Coll',
                    'https://tfs.roseninspection.net:8443/tfs/Coll',
                    'https://tfs.roseninspection.net%2eevil.com/tfs/Coll',
                    'http://tfs.roseninspection.net/tfs/Coll',
                    'https://tfs.roseninspection.net/',
                    'https://tfs.roseninspection.net',
                    'https://tfs.roseninspection.net/tfs/Coll/extra',
                    'https://tfs.roseninspection.net/tfs/../Coll',
                    'https://tfs.roseninspection.net//tfs/Coll',
                    'https://tfs.roseninspection.net/tfs/Coll?x=1',
                    'https://other.roseninspection.net/tfs/Coll']:
                self.assertIsNone(canonicalize_azure_devops_organization_url(url), url)
                self.assertFalse(is_onprem_organization_url(url), url)

    def test_env_parsing(self):
        value = ' TFS.One.net, bad_host ,*.wild.net,dev.azure.com,localhost,a.b..c,two.net '
        with mock.patch.dict(os.environ, {'AZURE_DEVOPS_EXT_ONPREM_HOSTS': value}, clear=True):
            self.assertEqual(get_allowed_onprem_hosts(), {'tfs.one.net', 'two.net'})

    def test_cloud_urls_unaffected(self):
        with mock.patch.dict(os.environ, ENV, clear=True):
            self.assertEqual(canonicalize_azure_devops_organization_url('https://dev.azure.com/org'),
                             'https://dev.azure.com/org')

    def test_auto_detect_stays_cloud_only(self):
        with mock.patch.dict(os.environ, ENV, clear=True):
            self.assertFalse(is_azure_devops_host(HOST))
            self.assertFalse(_is_azure_devops_host(HOST))
            self.assertIsNone(parse_azure_devops_git_remote('https://' + HOST + '/tfs/Coll/proj/_git/repo'))
            self.assertIsNone(organization_url_from_azure_devops_url('https://' + HOST + '/tfs/Coll'))

    def test_az_login_token_never_used_for_onprem(self):
        with mock.patch.dict(os.environ, ENV, clear=True), \
                mock.patch.object(services, 'Profile') as profile:
            self.assertEqual(get_token_from_az_logins('https://' + HOST + '/tfs/Coll', True), '')
            profile.assert_not_called()


if __name__ == '__main__':
    unittest.main()
