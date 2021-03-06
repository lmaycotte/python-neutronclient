# Copyright 2016 ZTE Corporation.
# All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
from mock import call

from osc_lib import exceptions
from osc_lib import utils

# TODO(abhiraut): Switch to osc-lib test utils
from openstackclient.tests import utils as tests_utils

from neutronclient.osc.v2.trunk import network_trunk as trunk
from neutronclient.tests.unit.osc.v2 import fakes as test_fakes
from neutronclient.tests.unit.osc.v2.trunk import fakes


def _get_id(client, id_or_name, resource):
    return id_or_name


class TestCreateNetworkTrunk(test_fakes.TestNeutronClientOSCV2):
    # The new trunk created
    _trunk = fakes.FakeTrunk.create_one_trunk()

    columns = (
        'admin_state_up',
        'id',
        'name',
        'port_id',
        'project_id',
        'status',
        'sub_ports',
    )
    data = (
        trunk._format_admin_state(_trunk['admin_state_up']),
        _trunk['id'],
        _trunk['name'],
        _trunk['port_id'],
        _trunk['project_id'],
        _trunk['status'],
        utils.format_list_of_dicts(_trunk['sub_ports']),
    )

    def setUp(self):
        super(TestCreateNetworkTrunk, self).setUp()
        mock.patch('neutronclient.osc.v2.trunk.network_trunk._get_id',
                   new=_get_id).start()
        self.neutronclient.create_trunk = mock.Mock(
            return_value={trunk.TRUNK: self._trunk})

        # Get the command object to test
        self.cmd = trunk.CreateNetworkTrunk(self.app, self.namespace)

    def test_create_no_options(self):
        arglist = []
        verifylist = []

        self.assertRaises(tests_utils.ParserException, self.check_parser,
                          self.cmd, arglist, verifylist)

    def test_create_default_options(self):
        arglist = [
            "--parent-port", self._trunk['port_id'],
            self._trunk['name'],
        ]
        verifylist = [
            ('parent_port', self._trunk['port_id']),
            ('name', self._trunk['name']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = (self.cmd.take_action(parsed_args))

        self.neutronclient.create_trunk.assert_called_once_with({
            trunk.TRUNK: {'name': self._trunk['name'],
                          'admin_state_up': self._trunk['admin_state_up'],
                          'port_id': self._trunk['port_id']}
        })
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.data, data)

    def test_create_full_options(self):
        subport = self._trunk['sub_ports'][0]
        arglist = [
            "--disable",
            "--parent-port", self._trunk['port_id'],
            "--subport", 'port=%(port)s,segmentation-type=%(seg_type)s,'
            'segmentation-id=%(seg_id)s' % {
                'seg_id': subport['segmentation_id'],
                'seg_type': subport['segmentation_type'],
                'port': subport['port_id']},
            self._trunk['name'],
        ]
        verifylist = [
            ('name', self._trunk['name']),
            ('parent_port', self._trunk['port_id']),
            ('add_subports', [{
                'port': subport['port_id'],
                'segmentation-id': str(subport['segmentation_id']),
                'segmentation-type': subport['segmentation_type']}]),
            ('disable', True),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = (self.cmd.take_action(parsed_args))

        self.neutronclient.create_trunk.assert_called_once_with({
            trunk.TRUNK: {'name': self._trunk['name'],
                          'admin_state_up': False,
                          'sub_ports': [subport],
                          'port_id': self._trunk['port_id']}
        })
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.data, data)

    def test_create_trunk_with_subport_invalid_segmentation_id_fail(self):
        subport = self._trunk['sub_ports'][0]
        arglist = [
            "--parent-port", self._trunk['port_id'],
            "--subport", "port=%(port)s,segmentation-type=%(seg_type)s,"
            "segmentation-id=boom" % {
                'seg_type': subport['segmentation_type'],
                'port': subport['port_id']},
            self._trunk['name'],
        ]
        verifylist = [
            ('name', self._trunk['name']),
            ('parent_port', self._trunk['port_id']),
            ('add_subports', [{
                'port': subport['port_id'],
                'segmentation-id': 'boom',
                'segmentation-type': subport['segmentation_type']}]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        try:
            self.cmd.take_action(parsed_args)
            self.fail('CommandError should be raised.')
        except exceptions.CommandError as e:
            self.assertEqual("Segmentation-id 'boom' is not an integer",
                             str(e))


class TestDeleteNetworkTrunk(test_fakes.TestNeutronClientOSCV2):
    # The trunk to be deleted.
    _trunks = fakes.FakeTrunk.create_trunks(count=2)

    def setUp(self):
        super(TestDeleteNetworkTrunk, self).setUp()

        mock.patch('neutronclient.osc.v2.trunk.network_trunk._get_id',
                   new=_get_id).start()
        self.neutronclient.delete_trunk = mock.Mock(return_value=None)

        # Get the command object to test
        self.cmd = trunk.DeleteNetworkTrunk(self.app, self.namespace)

    def test_delete_trunk(self):
        arglist = [
            self._trunks[0]['name'],
        ]
        verifylist = [
            ('trunk', [self._trunks[0]['name']]),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.neutronclient.delete_trunk.assert_called_once_with(
            self._trunks[0]['name'])
        self.assertIsNone(result)

    def test_delete_trunk_multiple(self):
        arglist = []
        verifylist = []

        for t in self._trunks:
            arglist.append(t['name'])
        verifylist = [
            ('trunk', arglist),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        calls = []
        for t in self._trunks:
            calls.append(call(t['name']))
        self.neutronclient.delete_trunk.assert_has_calls(calls)
        self.assertIsNone(result)

    def test_delete_trunk_multiple_with_exception(self):
        arglist = [
            self._trunks[0]['name'],
            'unexist_trunk',
        ]
        verifylist = [
            ('trunk',
             [self._trunks[0]['name'], 'unexist_trunk']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        get_mock_result = [self._trunks[0], exceptions.CommandError]
        trunk._get_id = (
            mock.MagicMock(side_effect=get_mock_result)
        )
        try:
            self.cmd.take_action(parsed_args)
            self.fail('CommandError should be raised.')
        except exceptions.CommandError as e:
            self.assertEqual('1 of 2 trunks failed to delete.', str(e))
        self.neutronclient.delete_trunk.assert_called_once_with(
            self._trunks[0]
        )


class TestShowNetworkTrunk(test_fakes.TestNeutronClientOSCV2):

    # The trunk to set.
    _trunk = fakes.FakeTrunk.create_one_trunk()

    columns = (
        'admin_state_up',
        'id',
        'name',
        'port_id',
        'project_id',
        'status',
        'sub_ports',
    )
    data = (
        trunk._format_admin_state(_trunk['admin_state_up']),
        _trunk['id'],
        _trunk['name'],
        _trunk['port_id'],
        _trunk['project_id'],
        _trunk['status'],
        utils.format_list_of_dicts(_trunk['sub_ports']),
    )

    def setUp(self):
        super(TestShowNetworkTrunk, self).setUp()

        mock.patch('neutronclient.osc.v2.trunk.network_trunk._get_id',
                   new=_get_id).start()
        self.neutronclient.show_trunk = mock.Mock(
            return_value={trunk.TRUNK: self._trunk})

        # Get the command object to test
        self.cmd = trunk.ShowNetworkTrunk(self.app, self.namespace)

    def test_show_no_options(self):
        arglist = []
        verifylist = []

        self.assertRaises(tests_utils.ParserException, self.check_parser,
                          self.cmd, arglist, verifylist)

    def test_show_all_options(self):
        arglist = [
            self._trunk['id'],
        ]
        verifylist = [
            ('trunk', self._trunk['id']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.neutronclient.show_trunk.assert_called_once_with(
            self._trunk['id'])
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.data, data)


class TestListNetworkTrunk(test_fakes.TestNeutronClientOSCV2):
    # Create trunks to be listed.
    _trunks = fakes.FakeTrunk.create_trunks(count=3)

    columns = (
        'ID',
        'Name',
        'Parent Port',
    )
    data = []
    for t in _trunks:
        data.append((
            t['id'],
            t['name'],
            t['port_id'],
        ))

    def setUp(self):
        super(TestListNetworkTrunk, self).setUp()
        mock.patch('neutronclient.osc.v2.trunk.network_trunk._get_id',
                   new=_get_id).start()
        self.neutronclient.list_trunks = mock.Mock(
            return_value={trunk.TRUNKS: self._trunks})

        # Get the command object to test
        self.cmd = trunk.ListNetworkTrunk(self.app, self.namespace)

    def test_trunk_list_no_option(self):
        arglist = []
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.neutronclient.list_trunks.assert_called_once_with()
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.data, list(data))


class TestSetNetworkTrunk(test_fakes.TestNeutronClientOSCV2):
    # Create trunks to be listed.
    _trunk = fakes.FakeTrunk.create_one_trunk()

    columns = (
        'admin_state_up',
        'id',
        'name',
        'port_id',
        'project_id',
        'status',
        'sub_ports',
    )
    data = (
        trunk._format_admin_state(_trunk['admin_state_up']),
        _trunk['id'],
        _trunk['name'],
        _trunk['port_id'],
        _trunk['project_id'],
        _trunk['status'],
        utils.format_list_of_dicts(_trunk['sub_ports']),
    )

    def setUp(self):
        super(TestSetNetworkTrunk, self).setUp()
        mock.patch('neutronclient.osc.v2.trunk.network_trunk._get_id',
                   new=_get_id).start()
        self.neutronclient.update_trunk = mock.Mock(
            return_value={trunk.TRUNK: self._trunk})
        self.neutronclient.trunk_add_subports = mock.Mock(
            return_value=self._trunk)

        # Get the command object to test
        self.cmd = trunk.SetNetworkTrunk(self.app, self.namespace)

    def test_set_network_trunk_name(self):
        arglist = [
            '--name', 'trunky',
            self._trunk['name'],
        ]
        verifylist = [
            ('name', 'trunky'),
            ('trunk', self._trunk['name']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        attrs = {
            'name': 'trunky',
        }
        self.neutronclient.update_trunk.assert_called_once_with(
            self._trunk['name'], {trunk.TRUNK: attrs})
        self.assertIsNone(result)

    def test_set_network_trunk_admin_state_up_disable(self):
        arglist = [
            '--disable',
            self._trunk['name'],
        ]
        verifylist = [
            ('disable', True),
            ('trunk', self._trunk['name']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        attrs = {
            'admin_state_up': False,
        }
        self.neutronclient.update_trunk.assert_called_once_with(
            self._trunk['name'], {trunk.TRUNK: attrs})
        self.assertIsNone(result)

    def test_set_network_trunk_admin_state_up_enable(self):
        arglist = [
            '--enable',
            self._trunk['name'],
        ]
        verifylist = [
            ('enable', True),
            ('trunk', self._trunk['name']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        attrs = {
            'admin_state_up': True,
        }
        self.neutronclient.update_trunk.assert_called_once_with(
            self._trunk['name'], {trunk.TRUNK: attrs})
        self.assertIsNone(result)

    def test_set_network_trunk_nothing(self):
        arglist = [self._trunk['name'], ]
        verifylist = [('trunk', self._trunk['name']), ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        attrs = {}
        self.neutronclient.update_trunk.assert_called_once_with(
            self._trunk['name'], {trunk.TRUNK: attrs})
        self.assertIsNone(result)

    def test_set_network_trunk_subports(self):
        subport = self._trunk['sub_ports'][0]
        arglist = [
            "--subport", 'port=%(port)s,segmentation-type=%(seg_type)s,'
            'segmentation-id=%(seg_id)s' % {
                'seg_id': subport['segmentation_id'],
                'seg_type': subport['segmentation_type'],
                'port': subport['port_id']},
            self._trunk['name'],
        ]
        verifylist = [
            ('trunk', self._trunk['name']),
            ('set_subports', [{
                'port': subport['port_id'],
                'segmentation-id': str(subport['segmentation_id']),
                'segmentation-type': subport['segmentation_type']}]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        self.neutronclient.trunk_add_subports.assert_called_once_with(
            self._trunk['name'], {'sub_ports': [subport]}
        )
        self.assertIsNone(result)


class TestListNetworkSubport(test_fakes.TestNeutronClientOSCV2):

    _trunk = fakes.FakeTrunk.create_one_trunk()
    _subports = _trunk['sub_ports']

    columns = (
        'Port',
        'Segmentation Type',
        'Segmentation ID',
    )
    data = []
    for s in _subports:
        data.append((
            s['port_id'],
            s['segmentation_type'],
            s['segmentation_id'],
        ))

    def setUp(self):
        super(TestListNetworkSubport, self).setUp()
        mock.patch('neutronclient.osc.v2.trunk.network_trunk._get_id',
                   new=_get_id).start()
        self.neutronclient.trunk_get_subports = mock.Mock(
            return_value={trunk.SUB_PORTS: self._subports})

        # Get the command object to test
        self.cmd = trunk.ListNetworkSubport(self.app, self.namespace)

    def test_subport_list(self):
        arglist = [
            '--trunk', self._trunk['name'],
        ]
        verifylist = [
            ('trunk', self._trunk['name']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.neutronclient.trunk_get_subports.assert_called_once_with(
            self._trunk['name'])
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.data, list(data))


class TestUnsetNetworkTrunk(test_fakes.TestNeutronClientOSCV2):

    _trunk = fakes.FakeTrunk.create_one_trunk()

    columns = (
        'admin_state_up',
        'id',
        'name',
        'port_id',
        'project_id',
        'status',
        'sub_ports',
    )
    data = (
        trunk._format_admin_state(_trunk['admin_state_up']),
        _trunk['id'],
        _trunk['name'],
        _trunk['port_id'],
        _trunk['project_id'],
        _trunk['status'],
        utils.format_list_of_dicts(_trunk['sub_ports']),
    )

    def setUp(self):
        super(TestUnsetNetworkTrunk, self).setUp()

        mock.patch('neutronclient.osc.v2.trunk.network_trunk._get_id',
                   new=_get_id).start()
        self.neutronclient.trunk_remove_subports = mock.Mock(
            return_value=None)

        # Get the command object to test
        self.cmd = trunk.UnsetNetworkTrunk(self.app, self.namespace)

    def test_unset_network_trunk_subport(self):
        subport = self._trunk['sub_ports'][0]
        arglist = [
            "--subport", subport['port_id'],
            self._trunk['name'],
        ]
        verifylist = [
            ('trunk', self._trunk['name']),
            ('unset_subports', [subport['port_id']]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.neutronclient.trunk_remove_subports.assert_called_once_with(
            self._trunk['name'],
            {trunk.SUB_PORTS: [{'port_id': subport['port_id']}]}
        )
        self.assertIsNone(result)

    def test_unset_subport_no_arguments_fail(self):
        arglist = [
            self._trunk['name'],
        ]
        verifylist = [
            ('trunk', self._trunk['name']),
        ]
        self.assertRaises(tests_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)
