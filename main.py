""" google-home-talker-mqtt """

from logging import getLogger, Formatter, StreamHandler, INFO
import os
import io
import json
import unicodedata
from time import sleep
from datetime import datetime, timedelta
from dateutil.parser import parse as date_parse

import parse
import paho.mqtt.client as mqtt
from google.cloud import texttospeech, storage
import pychromecast

from configurations import *


# global
logger = getLogger(__name__)
talk_schedule = []


def main():
    """ main """
    # Logger
    logger.setLevel(INFO)
    handler = StreamHandler()
    handler.setFormatter(Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    logger.info('Start')

    # Subscribe Beebotte by MQTTS
    mqtt_client = mqtt.Client()
    mqtt_client.enable_logger(logger)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set('token:' + MQTT_TOKEN)
    mqtt_client.tls_set(MQTT_CACERT)
    mqtt_client.connect(MQTT_HOST, port=MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()

    # Check scheduled talk
    while True:
        sleep(POLLING_INTERVAL)
        if talk_schedule:
            now = datetime.now()
            for time, text in talk_schedule[:]:
                if time <= now:
                    talk(text)
                    talk_schedule.remove((time, text))


def on_connect(client, _userdata, _flags, _respons_code):
    """ MQTT on connect """
    logger.info('MQTT Connected. Subscribe "%s"', MQTT_TOPIC)
    client.subscribe(MQTT_TOPIC)


def on_message(_client, _userdata, msg):
    """ MQTT on message """
    logger.debug('OnMessage:%s %s', msg.topic, str(msg.payload))

    record = json.loads(msg.payload.decode('utf-8'))
    logger.info('Receive:"%s"', record['data'])

    text, time = parse_data(record['data'])
    if time is None:
        talk(text)
    elif time < datetime.now():
        logger.warning('Specified time "%s" has already past. Talk immediately.', time)
        talk(text)
    else:
        logger.info('Scheduled for "%s" to talk "%s"', time, text)
        talk_schedule.append((time, text))


def parse_data(data: str) -> (str, datetime):
    """ Parse "data" filed
    Parse target
        <talk>text</talk> : talk text
        <time>2000-01-01 12:00:00</time> : dateutil.parser acceptable string
        <before>60</before> : seconds
    """
    result = parse.search('<talk>{}</talk>', data)
    if result is None:
        return data, None
    text = result[0]

    result = parse.search('<time>{}</time>', data)
    if result is None:
        return text, None
    try:
        time = date_parse(result[0])
    except ValueError:
        logger.error('Invalid time expression')
        return 'Error. Invalid time expression.', None

    result = parse.search('<before>{:d}</before>', data)
    if result:
        time -= timedelta(seconds=result[0])

    return text, time


def talk(text):
    """ Synthesize and play """
    audio_url = upload_and_get_url(text_to_speech(text))

    try:
        device = pychromecast.Chromecast(CHROMECAST_DEVICE_IP)
        device.wait()
    except pychromecast.PyChromecastError:
        logger.error('Cannot connect to "%s"', CHROMECAST_DEVICE_IP)
        return

    logger.info('Device will say "%s"', text)

    try:
        device.media_controller.play_media(audio_url, 'audio/mp3')
        device.media_controller.block_until_active()
    except pychromecast.PyChromecastError:
        logger.error('Chromecast device error')


def text_to_speech(text):
    """ Synthesize speech audio
    Return:
        audio binary (mp3)
    References:
        https://cloud.google.com/text-to-speech/docs/libraries
    """
    tts_input = texttospeech.SynthesisInput(text=text)

    def check_language(text):
        """ Check if text contains Japanese
        Note:
            Chinese is checked as Japanese
        Thanks to 'minus9d':
            https://minus9d.hatenablog.com/entry/2015/07/16/231608
        """
        for char in text:
            name = unicodedata.name(char)
            if 'CJK UNIFIED' in name or 'HIRAGANA' in name or 'KATAKANA' in name:
                return 'ja-JP'
        return TTS_DEFAULT_LANGUAGE

    language_code = check_language(text) if TTS_CHECK_JAPANESE else TTS_DEFAULT_LANGUAGE

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=TTS_GENDER
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=TTS_SPEED,
        pitch=TTS_PITCH,
        volume_gain_db=TTS_GAIN_DB,
        effects_profile_id=[TTS_PROFILE]
    )

    tts_client = texttospeech.TextToSpeechClient.from_service_account_json(TTS_ACCOUNT_JSON)
    return tts_client.synthesize_speech(input=tts_input, voice=voice, audio_config=audio_config)


def upload_and_get_url(audio):
    """ Upload audio to Google Cloud Storage
    Return:
        URL valid for 5 minutes
    """
    # upload to Google cloud storage
    gcs_client = storage.Client.from_service_account_json(GCS_ACCOUNT_JSON)
    bucket = gcs_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(TTS_TEMPORARY_AUDIO_FILENAME)
    blob.upload_from_file(io.BytesIO(audio.audio_content))

    # get url valid for 5 minutes
    url = blob.generate_signed_url(expiration=timedelta(minutes=5))
    return url


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
