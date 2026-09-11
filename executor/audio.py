"""Windows master-volume controls."""

from __future__ import annotations


class AudioController:
    def _endpoint(self) -> object:
        from ctypes import POINTER, cast
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        interface = AudioUtilities.GetSpeakers().Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    def get_volume(self) -> int:
        return round(float(self._endpoint().GetMasterVolumeLevelScalar()) * 100)

    def set_volume(self, value: int) -> int:
        value = max(0, min(100, int(value)))
        self._endpoint().SetMasterVolumeLevelScalar(value / 100, None)
        return value

    def adjust(self, delta: int) -> int:
        return self.set_volume(self.get_volume() + delta)

    def mute(self, muted: bool) -> bool:
        self._endpoint().SetMute(bool(muted), None)
        return muted

