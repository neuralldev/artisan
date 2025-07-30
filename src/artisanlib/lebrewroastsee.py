#
# ABOUT
# Lebrew RoastSee C1 support for Artisan

#ROASTSEE_C1_ADDRESS = "F084AA8F-3836-B9AA-2896-BD451B7579AF" 
#ROASTSEE_NAME = "RoastSee C1"  # Example name of the device
#ROASTSEE_UUID = "bc41e50b-91cd-4916-9152-02d52446ac3a" 
#ROASTSEE_C1_NOTIFY_UUID = "0000ff03-0000-1000-8000-00805f9b34fb"  #

import asyncio
import logging
from enum import IntEnum, unique
from typing import Optional, Union, List, Tuple, Final, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from bleak.backends.characteristic import BleakGATTCharacteristic  # pylint: disable=unused-import

try:
    from PyQt6.QtCore import pyqtSignal, pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import pyqtSignal, pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.ble_port import ClientBLE
from artisanlib.async_comm import AsyncIterable, IteratorReader
from artisanlib.scale import Scale, ScaleSpecs
from artisanlib.util import float2float


_log: Final[logging.Logger] = logging.getLogger(__name__)

LEBREW_DEVICES_NAMES = [
    ('RoastSee', 'RoastSee C1')
]

# LebrewBLE class for BLE communication with the Lebrew RoastSee C1 device
class LebrewBLE(ClientBLE): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    C1_NAME:Final[str] = 'RoastSee C1' # Name of the RoastSee C1 device    
    C1_SERVICE_UUID:Final[str] = 'bc41e50b-91cd-4916-9152-02d52446ac3a' # Service UUID for RoastSee C1
    C1_READ_NOTIFY_UUID:Final[str] = '0000ff03-0000-1000-8000-00805f9b34fb' #  Measurement
    HEADER1:Final[bytes]      = b'\x01' # Type of message expected

    connected_signal = pyqtSignal()     # issued on connect
    disconnected_signal = pyqtSignal()  # issued on disconnect
    color_changed_signal = pyqtSignal(float)  # issued on color change

    def __init__(self,  connected_handler:Optional[Callable[[], None]] = None,
                       disconnected_handler:Optional[Callable[[], None]] = None,
                       decimals:int=1):
        super().__init__()
        self._connected_handler = connected_handler
        self._disconnected_handler = disconnected_handler
        self.color_read: float = 0
        self.color_changed: bool = False
        self.is_connected: bool = False
        self.rounding: int = decimals
        self.add_device_description(self.C1_SERVICE_UUID, device_name=self.C1_NAME)
        self.add_notify(self.C1_READ_NOTIFY_UUID, self.notify_callback)
        self.add_read(self.C1_SERVICE_UUID, self.C1_READ_NOTIFY_UUID)
        self.add_write(self.C1_SERVICE_UUID, self.C1_READ_NOTIFY_UUID)

    def set_color(self, value) -> None:        
        self.color_read = value
    
    def is_new_color(self) -> bool:        
        return self.color_changed

    def getColor(self) -> float:
        self.color_changed = False
        data = self.read(self.C1_READ_NOTIFY_UUID)
        if data is None or len(data) < 3:
            return 0.0
        msg_type = data[0]                 # Premier octet : identifiant
        if msg_type != self.HEADER1:       # Type de message attendu
            return 0.0
        raw_value = (data[1] << 8) | data[2]
        self.color_read = round(raw_value / 100.0, self.rounding)  # round according to decimals sent by parent thread
        return self.color_read

    def notify_callback(self, _sender:'BleakGATTCharacteristic', data:bytearray) -> None:
        msg_type = data[0]                 # Premier octet : identifiant
        if msg_type != 0x01:       # Type de message attendu
            return
        raw_value = (data[1] << 8) | data[2]
        self.color_read = round(raw_value / 100.0, self.rounding)  # round according to decimals sent by parent thread
        self.color_changed = True
        self.color_changed_signal.emit(self.color_read)

    def isconnected(self) -> bool:
        connected_service_UUID, connected_device_name = self.connected()
        if (connected_service_UUID == self.C1_SERVICE_UUID and
            connected_device_name == self.C1_NAME):
            self.is_connected = True
        return self.is_connected

    def on_connect(self) -> None: # pylint: disable=no-self-use
        connected_service_UUID, connected_device_name = self.connected()
        if( connected_service_UUID == self.C1_SERVICE_UUID and
            connected_device_name == self.C1_NAME):
            if self._connected_handler is not None:
                self._connected_handler()
            self.is_connected = True
            self.connected_signal.emit()

    def on_disconnect(self) -> None: # pylint: disable=no-self-use
        if self._disconnected_handler is not None:
            self._disconnected_handler()
        self.is_connected = False
        self.disconnected_signal.emit()
#
#    def on_start(self) -> None:


class LebrewColorChecker(): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    C1_NAME:Final[str] = 'RoastSee C1'
    C1_SERVICE_UUID:Final[str] = 'bc41e50b-91cd-4916-9152-02d52446ac3a'
    C1_READ_NOTIFY_UUID:Final[str] = '0000ff03-0000-1000-8000-00805f9b34fb'    # Laser Measurements
    C1_DEVICE_UUID:Final[str] = 'F084AA8F-3836-B9AA-2896-BD451B7579AF'
    HEADER1:Final[bytes]      = b'\x01'

    def __init__(self, ident:Optional[str], decimals:int=1):
        super().__init__()
        self.lebrewble = LebrewBLE( )
        self.lebrew_devices: List[Tuple[str, str]] = []
        self.colorchecker_connected = False
        self.searchfor = self.C1_DEVICE_UUID
        self.scan()

    def scan(self) -> None:
        devices = self.lebrewble.scan()
        for d in devices:
            ble_device = d[0]
            adv_data = d[1]
            if self.C1_SERVICE_UUID.lower() in [s.lower() for s in getattr(adv_data, "service_uuids", [])]:
                if ble_device.name == self.C1_NAME:
                    if ble_device.name is not None:
                        self.lebrew_devices.append((ble_device.name, ble_device.address))
                    self.searchfor = ble_device.address
                    break

    def is_connected(self) -> bool:
        return self.colorchecker_connected

    def connect_colorchecker(self) -> None:
        self.colorchecker_connected = self.lebrewble.is_connected

    def disconnect_colorchecker(self) -> None:
        if self.lebrewble is not None:
                self.lebrewble.stop()
        self.colorchecker_connected = False

    def readability(self) -> float:
        return self.lebrewble.readability
