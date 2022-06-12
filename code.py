import digitalio
import audiocore
import audiopwmio
import board
import array
import time
import math
import alarm

MAX_SLEEP_COUNT = 20

#dac = audiopwmio.PWMAudioOut(board.GP0)

led_r = digitalio.DigitalInOut(board.LED_R)
led_b = digitalio.DigitalInOut(board.LED_B)
led_r.direction = digitalio.Direction.OUTPUT
led_b.direction = digitalio.Direction.OUTPUT
led_r.value = False
led_b.value = False

with audiopwmio.PWMAudioOut(board.GP0) as dac:
    with digitalio.DigitalInOut(board.GP1) as button:
        button.switch_to_input(pull=digitalio.Pull.UP)

        # Generate one period of sine wav.
        #length = 10
        #wave_buf = array.array("H", [0] * length)
        #for i in range(length):
        #    sine_wave[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)

        data_1 = open("bakushin-2022-01-22-a.wav", "rb")
        wave_1 = audiocore.WaveFile(data_1)
        data_2 = open("bakushin-2022-01-22-b.wav", "rb")
        wave_2 = audiocore.WaveFile(data_2)

        sleep_count = MAX_SLEEP_COUNT

        dac.play(wave_1)
        time.sleep(1.5)
        repeated = 1

        while sleep_count > 0:
            if not button.value:
                #wave = audiocore.RawSample(wave_buf, sample_rate=8000)
                #dac.play(sine_wave, loop=True)
                print('Pressed')
                if repeated % 3 == 2:
                    dac.play(wave_2)
                else:
                    dac.play(wave_1)
                time.sleep(1.5)
                sleep_count = MAX_SLEEP_COUNT
                repeated += 1
                #dac.stop()
            time.sleep(0.1)
            sleep_count -= 1

        led_r.direction = digitalio.Direction.INPUT
        led_b.direction = digitalio.Direction.INPUT

pin_alarm = alarm.pin.PinAlarm(pin=board.GP1, value=False, pull=True)
# Exit the program, and then deep sleep until the alarm wakes us.
alarm.exit_and_deep_sleep_until_alarms(pin_alarm)
# Does not return, so we never get here.
