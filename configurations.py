""" User configurations """

from google.cloud import texttospeech

############################################################
### General ###
############################################################

# Chromecast device (Google Home, etc.) IP
CHROMECAST_DEVICE_IP = '192.168.xxx.xxx'

# Polling interval for scheduled talk [seconds]
POLLING_INTERVAL = 5


############################################################
### Text-to-speech ###
############################################################

TTS_ACCOUNT_JSON = 'gcp-service-account.json'

# Language
TTS_DEFAULT_LANGUAGE = 'en-US'
TTS_CHECK_JAPANESE = True

# Voice gender
#  https://cloud.google.com/text-to-speech/docs/reference/rest/v1/SsmlVoiceGender
TTS_GENDER = texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED
#TTS_GENDER = texttospeech.SsmlVoiceGender.MALE
#TTS_GENDER = texttospeech.SsmlVoiceGender.FEMALE

# Voice settings
TTS_SPEED = 1.0 # [0.25, 4]
TTS_PITCH = 0.0 # [-20, 20]
TTS_GAIN_DB = 0.0 # [-96, 16]

# Device optimization profile
#  https://cloud.google.com/text-to-speech/docs/audio-profiles
#TTS_PROFILE = 'small-bluetooth-speaker-class-device' # Google Home Mini
TTS_PROFILE = 'medium-bluetooth-speaker-class-device' # Google Home
#TTS_PROFILE = 'large-home-entertainment-class-device' # Google Home Max, Smart TV


############################################################
### Google Cloud Storage ###
############################################################

GCS_ACCOUNT_JSON = TTS_ACCOUNT_JSON

BUCKET_NAME = 'xxxxxxxxxxxx'
TTS_TEMPORARY_AUDIO_FILENAME = 'tts_temp.mp3'


############################################################
### Beebotte ###
############################################################

# Connection
MQTT_HOST = 'mqtt.beebotte.com'
MQTT_PORT = 8883
MQTT_CACERT = 'mqtt.beebotte.com.pem'

# Topic
MQTT_TOPIC = 'CHANNEL_NAME/RESOURCE_NAME'
MQTT_TOKEN = 'token_xxxxxxxxxxxxxxx'

