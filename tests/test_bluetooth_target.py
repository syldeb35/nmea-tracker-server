import os
import tempfile
import unittest
from unittest.mock import patch


_original_directory = os.getcwd()
_temp_directory = tempfile.TemporaryDirectory()
os.chdir(_temp_directory.name)
with patch('gevent.monkey.patch_all'), patch('dotenv.load_dotenv'):
    import nmea_server as server
os.chdir(_original_directory)


class BluetoothTargetTests(unittest.TestCase):
    def setUp(self):
        self.manager = server.BluetoothGPSManager()

    def test_configured_device_uses_spp_without_scanning(self):
        sdp = '''Service Name: NavCast NMEA
Service Class ID List:
  "Serial Port" (0x1101)
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 11
'''
        with patch.object(server, 'IS_LINUX', True), \
             patch.object(server, 'BLUETOOTH_TARGET_MAC', 'AA:BB:CC:DD:EE:FF'), \
             patch.object(self.manager, 'prepare_bluetooth_adapter', return_value=True), \
             patch.object(self.manager, 'scan_bluetooth_devices') as scan, \
             patch.object(self.manager, 'run_command', return_value=(True, sdp, '')) as command, \
             patch.object(self.manager, 'setup_rfcomm', return_value='/dev/rfcomm0') as bind, \
             patch.object(self.manager, 'test_gps_connection', return_value=True):
            self.assertEqual(self.manager.auto_discover_and_connect(), '/dev/rfcomm0')
            scan.assert_not_called()
            command.assert_called_once_with('sdptool browse AA:BB:CC:DD:EE:FF', 10)
            bind.assert_called_once_with('AA:BB:CC:DD:EE:FF', 11)

    def test_spp_service_class_selected_instead_of_spp_in_service_name(self):
        sdp = '''Service Name: CONTINUITY_MSG_SPP
Service RecHandle: 0x10012
Service Class ID List:
  UUID 128: 3a622e58-c035-4a26-928c-5601dde7c657
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 9

Service Name: NavCast NMEA
Service RecHandle: 0x10028
Service Class ID List:
  "Serial Port" (0x1101)
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 11
Profile Descriptor List:
  "Serial Port" (0x1101)
    Version: 0x0102
'''
        with patch.object(self.manager, 'run_command', return_value=(True, sdp, '')):
            self.assertEqual(self.manager.find_spp_channel('AA:BB:CC:DD:EE:FF'), 11)

    def test_missing_spp_channel_does_not_borrow_next_record_channel(self):
        sdp = '''Service Name: GPS
Service RecHandle: 0x10001
Service Class ID List:
  "Serial Port" (0x1101)
Protocol Descriptor List:
  "L2CAP" (0x0100)

Service Name: CONTINUITY_MSG_SPP
Service RecHandle: 0x10002
Service Class ID List:
  UUID 128: 3a622e58-c035-4a26-928c-5601dde7c657
Protocol Descriptor List:
  "RFCOMM" (0x0003)
    Channel: 9
'''
        with patch.object(self.manager, 'run_command', return_value=(True, sdp, '')):
            self.assertIsNone(self.manager.find_spp_channel('AA:BB:CC:DD:EE:FF'))

    def test_empty_target_retains_scanning(self):
        with patch.object(server, 'IS_LINUX', True), \
             patch.object(server, 'BLUETOOTH_TARGET_MAC', ''), \
             patch.object(self.manager, 'scan_bluetooth_devices', return_value=[]) as scan:
            self.assertIsNone(self.manager.auto_discover_and_connect())
            scan.assert_called_once()

    def test_invalid_target_never_reaches_shell(self):
        with patch.object(server, 'IS_LINUX', True), \
             patch.object(server, 'BLUETOOTH_TARGET_MAC', 'AA:BB;bad'), \
             patch.object(self.manager, 'run_command') as command:
            self.assertIsNone(self.manager.auto_discover_and_connect())
            self.assertIsNone(self.manager.find_spp_channel('AA:BB;bad'))
            command.assert_not_called()

    def test_unavailable_target_does_not_fall_back_to_scan(self):
        with patch.object(server, 'IS_LINUX', True), \
             patch.object(server, 'BLUETOOTH_TARGET_MAC', 'AA:BB:CC:DD:EE:FF'), \
             patch.object(self.manager, 'prepare_bluetooth_adapter', return_value=True), \
             patch.object(self.manager, 'find_spp_channel', return_value=None), \
             patch.object(self.manager, 'scan_bluetooth_devices') as scan:
            self.assertIsNone(self.manager.auto_discover_and_connect())
            scan.assert_not_called()

    def test_configured_target_does_not_reuse_unknown_rfcomm(self):
        with patch.object(server, 'BLUETOOTH_TARGET_MAC', 'AA:BB:CC:DD:EE:FF'), \
             patch.object(server.time, 'sleep'), \
             patch.object(self.manager, 'detect_existing_rfcomm') as existing, \
             patch.object(self.manager, 'auto_discover_and_connect', return_value=None) as connect:
            self.manager.maintain_connection()
            existing.assert_not_called()
            connect.assert_called_once()

    def test_changing_target_releases_previous_connection(self):
        self.manager.is_connected = True
        self.manager.target_mac = '11:22:33:44:55:66'
        self.manager.configured_mac = '11:22:33:44:55:66'
        self.manager.last_scan_time = server.time.time()
        with patch.object(server, 'BLUETOOTH_TARGET_MAC', 'AA:BB:CC:DD:EE:FF'), \
             patch.object(server.time, 'sleep'), \
             patch.object(self.manager, 'cleanup_rfcomm') as cleanup, \
             patch.object(self.manager, 'auto_discover_and_connect', return_value=None) as connect:
            self.manager.maintain_connection()
            cleanup.assert_called_once()
            connect.assert_called_once()
            self.assertFalse(self.manager.is_connected)

    def test_configuration_page_shows_target(self):
        with patch.object(server, 'BLUETOOTH_TARGET_MAC', 'AA:BB:CC:DD:EE:FF'), \
             patch.object(server, 'list_serial_ports', return_value=[]):
            response = server.app.test_client().get('/config.html')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'name="bluetooth_target_mac" value="AA:BB:CC:DD:EE:FF"', response.data)

    def test_api_persists_normalized_mac_and_rejects_invalid_input(self):
        client = server.app.test_client()
        with tempfile.TemporaryDirectory() as directory:
            previous = os.getcwd()
            try:
                os.chdir(directory)
                with patch.object(server, 'BLUETOOTH_TARGET_MAC', ''), \
                     patch.object(server, 'manage_threads'):
                    response = client.post('/api/config', data={'bluetooth_target_mac': 'aa:bb:cc:dd:ee:ff'})
                    self.assertEqual(response.status_code, 200)
                    with open('.env', encoding='utf-8') as config:
                        self.assertIn('BLUETOOTH_TARGET_MAC=AA:BB:CC:DD:EE:FF', config.read())
                    response = client.post('/api/config', data={'bluetooth_target_mac': 'invalid'})
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(server.BLUETOOTH_TARGET_MAC, 'AA:BB:CC:DD:EE:FF')
                    response = client.post('/api/config', data={'bluetooth_target_mac': ''})
                    self.assertEqual(response.status_code, 200)
                    with open('.env', encoding='utf-8') as config:
                        self.assertIn('BLUETOOTH_TARGET_MAC=\n', config.read())
            finally:
                os.chdir(previous)

    def test_auto_mode_starts_monitor(self):
        with patch.object(server, 'IS_LINUX', True), \
             patch.object(server, 'ENABLE_SERIAL', True), \
             patch.object(server, 'ENABLE_UDP', False), \
             patch.object(server, 'ENABLE_TCP', False), \
             patch.object(server, 'SERIAL_PORT', 'AUTO'), \
             patch.object(server, 'bluetooth_monitor_thread', None), \
             patch.object(server, 'serial_thread', None), \
             patch.object(server.threading, 'Thread') as thread:
            server.manage_threads()
            thread.assert_called_once_with(
                target=server.bluetooth_monitor,
                args=(server.bluetooth_monitor_stop,),
                daemon=True,
            )
            thread.return_value.start.assert_called_once()


if __name__ == '__main__':
    unittest.main()
