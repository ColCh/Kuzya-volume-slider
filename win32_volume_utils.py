import uuid

from ctypes import POINTER, cast
from pycaw.pycaw import (AudioUtilities, IAudioEndpointVolume,
                         IAudioEndpointVolumeCallback)
from comtypes import CLSCTX_ALL, COMObject

from win32_file_props import get_file_description

# winapi : https://docs.microsoft.com/en-us/windows/win32/api/endpointvolume/nf-endpointvolume-iaudioendpointvolume-setmastervolumelevelscalar
# https://docs.microsoft.com/en-us/windows/win32/api/audioclient/nf-audioclient-isimpleaudiovolume-getmastervolume
# https://docs.microsoft.com/en-us/windows/win32/api/audioclient/nn-audioclient-isimpleaudiovolume
# ctypes: https://docs.python.org/3/library/ctypes.html
# volume by process example: https://github.com/AndreMiras/pycaw/blob/develop/examples/volume_by_process_example.py
# py lib: https://github.com/AndreMiras/pycaw
# https://github.com/AndreMiras/pycaw/blob/v2016


def get_audio_endpoint_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return volume


def get_volume_sessions():
    return AudioUtilities.GetAllSessions()


def get_process_displayed_name(process):
    return get_file_description(process.exe()) or process.name()


sessions = dict()


def scan_volume_sessions():
    """
    scan volume sessions, report added and removed sessions
    """
    global sessions

    added_sessions = []
    removed_sessions = []
    other_sessions = []

    current_sessions = sessions
    sessions = dict()

    for session in get_volume_sessions():
        if (session.Identifier in current_sessions):
            del current_sessions[session.Identifier]
            sessions[session.Identifier] = session
            other_sessions.append(session)
            continue
        else:
            added_sessions.append(session)
            sessions[session.Identifier] = session
            continue

    removed_sessions = list(current_sessions.values())

    return {
        "added": added_sessions,
        "removed": removed_sessions,
        "other": other_sessions,
        "all": sessions,
    }


VOLUME_CONTROLLER_UUID_NAMESPACE = uuid.uuid4()


class VolumeController():
    @staticmethod
    def get_uuid_by_win_identifier(win_identifier):
        return uuid.uuid5(VOLUME_CONTROLLER_UUID_NAMESPACE,
                          str(win_identifier)).hex

    def __init__(self, win_volume, win_identifier, display_name):
        self.win_identifier = win_identifier
        self.id = VolumeController.get_uuid_by_win_identifier(
            self.win_identifier)
        self.win_volume = win_volume
        self.display_name = display_name

    def as_dict(self):
        return dict(id=self.id,
                    display_name=self.display_name,
                    volume=self.volume)

    @property
    def volume(self) -> float:
        if hasattr(self.win_volume, 'GetMasterVolumeLevelScalar'):
            return round(self.win_volume.GetMasterVolumeLevelScalar(), 2)
        elif hasattr(self.win_volume, 'GetMasterVolume'):
            return round(self.win_volume.GetMasterVolume(), 2)
        else:
            raise RuntimeError('cannot determine volume level')

    @volume.setter
    def volume(self, new_volume):
        if hasattr(self.win_volume, 'SetMasterVolumeLevelScalar'):
            return self.win_volume.SetMasterVolumeLevelScalar(new_volume, None)
        elif hasattr(self.win_volume, 'SetMasterVolume'):
            return self.win_volume.SetMasterVolume(new_volume, None)
        else:
            raise RuntimeError('cannot set volume level')
