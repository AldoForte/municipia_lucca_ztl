import RPi.GPIO as GPIO

def attiva_rel_01():
    GPIO.output(RELAY_01, 1)
    sleep(0.5)
    GPIO.output(RELAY_01, 0)
