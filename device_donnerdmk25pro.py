# name=Donner DMK-25 Pro
from time import time

import transport
import channels
from midi import SS_Start, SS_Stop, SONGLENGTH_MS

# Control Keys
LOOP_KEY = 0x0f
REWIND_KEY = 0x10
FORWARD_KEY = 0x11
STOP_KEY = 0x12
PLAY_KEY = 0x13
RECORD_KEY = 0x14

# Special Keys
PIANO_NOTE_PRESSED = 0x90
PIANO_NOTE_RELEASED = 0x80
PAD_ITEM_PRESSED = 0x99
PAD_ITEM_RELEASED = 0x89

CONTROL_KEY_RELEASED = 0x00


### Info on Some Control Knobs I do not know what to
### Mod Slider S: 0xB0 D1: 0x01 D2: Value Chan: 1 Event: Control Mod
###
### Sliders: S: Varied on S Bank 0xB8-0xBB; D1: 0x07; D2: Value; Chan: Varied on S bank 0x01 - 0x12; Event: CC Volume
###
### Knobs: S: 0xB0; D1: Varied on K Bank 0x1E-0x29; D2: Value; Chan: 0x01; Event: Varies most are Control Change
### End


class EventData:
    """
    Stub for FL Studio eventData with readonly properties
    """
    def __init__(
            self, handled: bool,  # set to True to stop event propagation
            timestamp: time,  # timestamp of event
            status: int,  # MIDI status
            data1: int,  # MIDI data1
            data2: int,  # MIDI data2
            port: int,  # MIDI port
            note: int,  # MIDI note number
            velocity: int,  # MIDI velocity
            pressure: int,  # MIDI pressure
            progNum: int,  # MIDI program number
            controlNum: int,  # MIDI control number
            controlVal: int,  # MIDI control value
            pitchBend: int,  # MIDI pitch bend value
            sysex: bytes,  # MIDI sysex data
            isIncrement: bool,  # MIDI is increment state
            res: float,  # MIDI res
            inEv: int,  # Original MIDI event value
            outEv: int,  # MIDI event output value
            midiChan: int,  # MIDI midiChan (0 based)
            midiChanEx: int,  # MIDI midiChanEx
            pmeflags: int  # MIDI pmeflags
    ):
        self.handled = handled
        self._timestamp = timestamp
        self.status = status
        self.data1 = data1
        self.data2 = data2
        self._port = port
        self.note = note
        self.velocity = velocity
        self.pressure = pressure
        self._progNum = progNum
        self._controlNum = controlNum
        self._controlVal = controlVal
        self._pitchBend = pitchBend
        self.sysex = sysex
        self.isIncrement = isIncrement
        self.res = res
        self.inEv = inEv
        self.outEv = outEv
        self.midiChan = midiChan
        self.midiChanEx = midiChanEx
        self._pmeflags = pmeflags

    # Readonly Properties
    @property
    def timestamp(self):
        return self._timestamp

    @property
    def port(self):
        return self._port

    @property
    def progNum(self):
        return self._progNum

    @property
    def controlNum(self):
        return self._controlNum

    @property
    def controlVal(self):
        return self._controlVal

    @property
    def pitchBend(self):
        return self._pitchBend

    @property
    def pmeflags(self):
        return self._pmeflags


def OnMidiMsg(event: EventData):
    """
    Handles Special Cases for keyboard
    :param event: midi event
    :return:
    """

    event.handled = False
    if event.status == PIANO_NOTE_PRESSED or event.status == PIANO_NOTE_RELEASED:
        print(f"Actual Key Pressed or Released ({event.note})")
        return

    if event.status == PAD_ITEM_PRESSED or event.status == PAD_ITEM_RELEASED:
        print("Pad Pressed or Released")
        return

    song_pos = transport.getSongPos(SONGLENGTH_MS)
    if event.data1 > 0:  # Anything 0x00 or less is invalid
        if event.data2 > CONTROL_KEY_RELEASED:
            if event.data1 == PLAY_KEY:  # Play or Pause Playback Depending on State
                print("Play / Paused pressed")
                if not transport.isPlaying():
                    transport.start()
                else:
                    transport.stop()
                    transport.setSongPos(song_pos, SONGLENGTH_MS)
                event.handled = True
            elif event.data1 == STOP_KEY:  # Stop Playback
                print("Stop Pressed")
                transport.stop()
                event.handled = True
            elif event.data1 == LOOP_KEY:  # Toggle Loop Mode
                print("Loop Pressed")
                transport.setLoopMode()
                event.handled = True
            elif event.data1 == REWIND_KEY:  # Seek Backwards Start
                print("Rwd Pressed")
                transport.rewind(SS_Start)
                event.handled = True
            elif event.data1 == FORWARD_KEY:  # Seek Forwards Start
                print("Fwd Pressed")
                transport.fastForward(SS_Start)
                event.handled = True
            elif event.data1 == RECORD_KEY:  # Toggle Recording
                print("Rec Pressed")
                transport.record()
                event.handled = True
            else:
                print("Unknown Key Pressed")
        else:
            print("Key Released")
            if event.data1 == REWIND_KEY:  # Seek Backwards Stop
                transport.rewind(SS_Stop)
                event.handled = True
            elif event.data1 == FORWARD_KEY:  # Seek Forwards Stop
                transport.fastForward(SS_Stop)
                event.handled = True


def OnPitchBend(event: EventData):
    """
    Handle Pitch Bends
    :param event:
    :return:
    """
    channel = channels.selectedChannel()
    # Donner has pitch shifts in the range (0-127[7F])
    # Need to map these values to FL Studio's range of -1 - 1 and apply the shift
    pitchValue = (event.data2 * 2) / 127 - 1
    channels.setChannelPitch(channel, pitchValue)
    event.handled = True
