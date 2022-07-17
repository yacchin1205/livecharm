import digitalio
import audiocore
import audiopwmio
import board
import array
import time
import math
import os
import alarm
import audiobusio
import random
import re
import errno

DEFAULT_LIGHT_WAKEUP_SEC = 30
DEFAULT_DEEP_WAKEUP_SEC = 5
#LONG_DEEP_WAKEUP_SEC = 60 * 60
MAX_SLEEP_COUNT = 20
AUDIO_DIR = './audio'

# ---- Interface関係の定義
WAKE_PIN = board.D13

def open_dac():
    # for Tiny 2040 (prototype)
    #return audiobusio.I2SOut(board.D11, board.D12, board.D10) as dac:
    # for Tiny 2040 PWM
    #return audiopwmio.PWMAudioOut(board.GP0)
    # Feather RP2040
    return audiobusio.I2SOut(board.A1, board.A2, board.A0)

# ---- Deep Sleep関係の処理
def get_pin_alarm():
    return alarm.pin.PinAlarm(pin=WAKE_PIN, value=True, pull=True)

#def enter_deep_sleep(sec):
def enter_deep_sleep():
    #alarm.sleep_memory[0] = 0
    pin_alarm = get_pin_alarm()
    #time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sec)
    # Exit the program, and then deep sleep until the alarm wakes us.
    #alarm.exit_and_deep_sleep_until_alarms(pin_alarm, time_alarm)
    # for Bug https://github.com/adafruit/circuitpython/issues/5794
    alarm.exit_and_deep_sleep_until_alarms(pin_alarm)
    # Does not return, so we never get here.

def enter_light_sleep():
    pin_alarm = get_pin_alarm()
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + DEFAULT_LIGHT_WAKEUP_SEC)
    triggered_alarm = alarm.light_sleep_until_alarms(pin_alarm, time_alarm)
    return not is_time_alarm(triggered_alarm)

def is_time_alarm(wake_alarm):
    return wake_alarm is not None and isinstance(wake_alarm, alarm.time.TimeAlarm)

# ---- Audio関係の処理
class AudioFiles:
    def __init__(self, audio_dir):
        self.waves = {}
        self.files = self.load_files(audio_dir)
        self.max_index = max([max([max(r[0], r[1]) for r in rset]) if rset is not None and len(rset) > 0 else 0 for rset, _ in self.files])

    def load_files(self, audio_dir):
        if not audio_dir.endswith('/'):
           audio_dir += '/'
        try:
            files = []
            for file in os.listdir(audio_dir):
                if file.startswith('.'):
                    print('File ignored(dot file): ', file)
                    continue
                m = re.match(r'.+(\.[a-zA-Z0-9]+)', file)
                if m is None or m.group(1).lower() != '.wav':
                    print('File ignored(must be .wav file): ', file)
                    continue
                entry = self.file_entry(audio_dir, file)
                files.append((entry, audio_dir + file))
            return files
        except OSError as e:
            if e.args[0] == errno.ENOENT:
                print('Directory not exists:', audio_dir)
                return []
            raise e

    def file_entry(self, audio_dir, file):
        prefix = re.match(r'([0-9\-_]+)[\-_].+', file)
        if prefix is None:
            return None
        return [self._parse_range(elem) for elem in prefix.group(1).split('_')]

    def get_wave(self, index):
        path = self._resolve_wave(index)
        if path is None:
            return None
        if path in self.waves:
            return self.waves[path]
        print('Loading...', path)
        data = open(path, "rb")
        wave = audiocore.WaveFile(data)
        self.waves[path] = wave
        return wave

    def has(self, index):
        return index <= self.max_index

    def _resolve_wave(self, index):
        if index == 0 and all([r is None for r, _ in self.files]):
            print('Randomize waves...')
            _, path = random.choice(self.files)
            return path
        cands = [(r, path) for r, path in self.files if self._is_match(r, index)]
        print('Selecting from', cands, '#{}'.format(index))
        if len(cands) == 0:
            if index > 0:
                return self._resolve_wave(index - 1)
            return None
        _, path = random.choice(cands)
        return path

    def _is_match(self, rset, index):
        if rset is None:
            return False
        for r in rset:
            rmin, rmax = r
            if (rmin <= index) and (index <= rmax):
                return True
        return False

    def _parse_range(self, elem):
        m = re.match(r'([0-9]+)\-([0-9]+)', elem)
        if m is not None:
            return (int(m.group(1)), int(m.group(2)))
        m = re.match(r'[0-9]+', elem)
        if m is not None:
            index = int(elem)
            return (index, index)
        return None

def wait_audio(dac, button):
    time.sleep(0.5)
    if not dac.playing:
        return button.value
    v = False
    while dac.playing:
        if v == False and button.value:
            print('Pressed(while playing)')
            v = True
    return v

def loop_waves(audio_files):
    with digitalio.DigitalInOut(WAKE_PIN) as button:
        button.switch_to_input(pull=digitalio.Pull.DOWN)

        sleep_count = MAX_SLEEP_COUNT
        index = 0
        dac.play(audio_files.get_wave(index))
        next_play = wait_audio(dac, button)
        index += 1
        if not audio_files.has(index):
            index = 0

        while sleep_count > 0:
            if next_play or button.value:
                print('Pressed')
                dac.play(audio_files.get_wave(index))
                next_play = wait_audio(dac, button)
                index += 1
                if not audio_files.has(index):
                    index = 0
                sleep_count = MAX_SLEEP_COUNT
            sleep_count -= 1
            time.sleep(0.1)

# ---- Main
print('WakeAlarm', alarm.wake_alarm)
if is_time_alarm(alarm.wake_alarm):
    # WakeUp by TimeAlarm
    #enter_deep_sleep(LONG_DEEP_WAKEUP_SEC)
    enter_deep_sleep()

audio_files = AudioFiles(AUDIO_DIR)
if len(audio_files.files) == 0:
    print('No audio files')

else:
    #with digitalio.DigitalInOut(board.LED_R) as led_r, digitalio.DigitalInOut(board.LED_B) as led_b:
    #    led_r.direction = digitalio.Direction.OUTPUT
    #    led_b.direction = digitalio.Direction.OUTPUT
    #    led_r.value = False
    #    led_b.value = False
    with open_dac() as dac:
        loop_waves(audio_files)
    #    led_r.value = True
        while enter_light_sleep():
            loop_waves(audio_files)

#enter_deep_sleep(DEFAULT_DEEP_WAKEUP_SEC)
enter_deep_sleep()
