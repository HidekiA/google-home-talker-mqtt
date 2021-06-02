# Google Home Talker MQTT


## What's this

* Google Home（や Smart TV 等の chromecast 対応機器）を IFTTT のアクション等でしゃべらせることができます
    * [開発理由] きっちり１分前に Google Calendar の予定をしゃべらせたかった
* Full SSL/TLS Internet connections


<a id="overview"></a>
## Overview
![](./img/overview.png)

---
## Index
* [Install](#install)
    * [起動時に実行](#install_systemd)
    * [設定](#configurations)
    * [メッセージフォーマット](#message_format)
* [外部サービスの設定](#cloud_services)
    * [Google Text-to-Speech](#gtts)
    * [Google Cloud Storage](#gcs)
    * [Beebotte](#beebotte)
    * [IFTTT](#ifttt)


---
<a id="install"></a>
## Install

#### ダウンロード
```
git clone https://github.com/HidekiA/google-home-talker-mqtt
```

#### 必要なパッケージのインストール
```
pip install --upgrade pychromecast
pip install --upgrade google-cloud-texttospeech
pip install --upgrade google-cloud-storage
pip install --upgrade paho-mqtt
pip install --upgrade parse
```

#### 設定
[configurations.py](./configurations.py) にクラウドサービスのアカウント等を設定（[下記参照](#configurations)）

#### 実行
```
cd google-home-talker-mqtt
python3 main.py
```

#### テスト
([Beebotte の設定](#beebotte)を行ってから)
```
curl -X POST -H "Content-Type: application/json" -d '{"data":"Hello world!"}' https://api.beebotte.com/v1/data/publish/チャンネル名/リソース名?token=認証トークン
```

平日の朝7時にモーニングコールしてもらう cron 設定例
```
0 7 * * 1-5 /usr/bin/curl -X POST -H "Content-Type: application/json" -d '{"data":"おはようございます"}' https://api.beebotte.com/v1/data/publish/チャンネル名/リソース名?token=認証トークン
```


<a id="install_systemd"></a>
### 起動時に実行 (systemd)

#### To set up a system service
1. [google-home-talker-mqtt@.service](./google-home-talker-mqtt@.service) を編集し、**ExecStart** のパスを実際のパスに置き換える
```
ExecStart=/usr/bin/python3 /home/USERNAME/google-home-talker-mqtt/main.py
```
2. Unit ファイルをコピー
```
sudo cp google-home-talker-mqtt@.service /etc/systemd/system/
```
3. システムサービスとして登録  
**（"*USRENAME*" を実際のユーザ名に置き換えてください）**
```
systemctl enable google-home-talker-mqtt@USRENAME.service
systemctl start google-home-talker-mqtt@USRENAME.service
```

#### To check the service status
```
systemctl status google-home-talker-mqtt@USRENAME.service
```

#### To see the logs
```
journalctl -e -u google-home-talker-mqtt@USRENAME.service
```

---
<a id="configurations"></a>
## 設定

### 全般
|  |  |
|---|---|
| CHROMECAST_DEVICE_IP | chromecast 対応デバイス（Google Home / Google Nest / Smart TV 等）の IPアドレス<br>Home アプリのデバイス情報から確認可能 |
| POLLING_INTERVAL | 予約時刻を確認する周期 [秒] |

### Text-to-Speech 関連
|  |  |
|---|---|
| TTS_ACCOUNT_JSON | Google Cloud Text-to-Speech のサービスアカウントキーのファイル名 ([取得方法](#gtts))|
| TTS_DEFAULT_LANGUAGE | 文章の言語 |
| TTS_CHECK_JAPANESE | True のとき、文章に日本語が含まれる場合は ja-JP、含まれない場合は `TTS_DEFAULT_LANGUAGE` を指定する<br>言語設定を ja-JP とすると英語の発音がひどいため。~~そこまで日本人らしい発音を再現しなくて良いのに~~<br>中国語の漢字も日本語と判定してしまうため、中国語を利用したい場合は False に設定すること |
| TTS_GENDER | 音声の性別 (詳細は[公式ドキュメント](https://cloud.google.com/text-to-speech/docs/reference/rest/v1/SsmlVoiceGender)を参照)<br>- *texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED*<br>- *texttospeech.SsmlVoiceGender.MALE*<br>- *texttospeech.SsmlVoiceGender.FEMALE*<br>(*SSML_VOICE_GENDER_UNSPECIFIED* は中性的な発音というわけではなく、言語ごとに設定された男女どちらかのデフォルト設定が使用される様子。以前は中性的な*NEUTRAL*があったが廃止された。) |
| TTS_SPEED | 発話の速さ (0.25 ～ 4) |
| TTS_PITCH | 音の高さ (-20 ～ 20) |
| TTS_GAIN_DB | 音量調節 (-96 ～ 16) |
| TTS_PROFILE | 再生機器に最適化するための音声プロファイルの設定<br>利用可能な音声プロファイルについては、[公式ドキュメント](https://cloud.google.com/text-to-speech/docs/audio-profiles?hl=ja) を参照 |


### Google Cloud Storage 関連
|  |  |
|---|---|
| GCS_ACCOUNT_JSON | Google Cloud Storage のサービスアカウントキーのファイル名<br>同じアカウントであれば Text-to-Speech のものと同じでも良い |
| BUCKET_NAME | 一時ファイルを保存するための Bucket 名  |
| TTS_TEMPORARY_AUDIO_FILENAME | 一時ファイルの名前<br>上書きして使用されるが、自動的には削除されない |


### Beebotte 関連
|  |  |
|---|---|
| MQTT_CACERT | Beebotte のサーバ証明書<br>https://beebotte.com/certs/mqtt.beebotte.com.pem を保存してそのファイルを指定 |
| MQTT_TOPIC | MQTTトピック ("*チャンネル名*/*リソース名*") |
| MQTT_TOKEN | Beebotte のチャネルトークン ([取得方法](#beebotte)) |


---
<a id="message_format"></a>
## Message Format
|  |  |
|---|---|
| `<talk>` | 話す文章<br>このフィールドがない場合は、メッセージ全体を話す文章とする |
| `<time>` (optional) | 話す時刻を予約する<br>時刻の表現形式は [dateutil.parser が対応する形式](https://dateutil.readthedocs.io/en/stable/parser.html)であれば何でも<br>（かなり柔軟だが日本語は非対応）<br>時刻のみ指定した場合は本日と解釈する<br>過去の時刻が指定された場合はすぐに話される |
| `<before>` (optional) | `<time>` で指定した時刻を補正する |

例
```
<talk>Hello world!</talk>
>> Say "Hello world!" immediately

Hello world!
>> Say "Hello world!" immediately

<talk>Happy New Year!</talk><time>Jan 1, 2030 at 9:00AM</time>
>> Say "Happy New Year!" at 9am on January 1, 2030

<talk>The meeting will begin soon.</talk><time>15:30</time><before>60</before>
>> Say "The meeting will begin soon." at 15:29 today
```


---
<a id="cloud_services"></a>
# 外部サービスの設定
## Google Cloud Platform


<a id="gtts"></a>
### Google Text-to-Speech
1. [公式ドキュメント](https://cloud.google.com/text-to-speech/docs/libraries?hl=JA)を参考にサービスアカウントを作成し、サービスアカウントキーをダウンロード

1. 次のページから Text-to-Speech API を有効化する  
https://console.cloud.google.com/marketplace/product/google/texttospeech.googleapis.com  
1か月あたり100万文字まで無料（文庫本8～10冊くらい）(2021年5月現在)  


<a id="gcs"></a>
### Google Cloud Storage
1. [Google Cloud Storage](https://console.cloud.google.com/storage/browser) で適当な名前のバケットを作成  
下記の設定とすることで、容量5GB、操作5,000回／月（166回／日くらい）まで無料 (2021年5月現在)

|  |  |
|---|---|
| ロケーションタイプ | Region（地域間の冗長化をしない） |
| ロケーション | us-west1 (or us-central1 or us-east1)   |
| ストレージクラス | Standard |


<a id="beebotte"></a>
## Beebotte

1. [Beebotte](https://beebotte.com/home) アカウントを作成
1. 任意のチャネル名、リソース名でチャネルを作成  
![](img/Beebotte_CreateChannel.png)
1. チャネル画面に表示される Channel Token を `MQTT_TOKEN` に設定  
![](img/Beebotte_ChannelToken.png)


<a id="ifttt"></a>
## IFTTT

1. [IFTTT](https://ifttt.com/) アカウントを作成
1. Create ボタンをクリックしてアプレット作成を開始
1. 「If This」に何かしらのトリガーを設定  
    * 予定を読み上げさせる場合は、Google Calendar を選択、「Any event starts」を選択、「Which calendar」に適当なカレンダーを選び、「Time before event starts」で「15 minutes」を選択
        * IFTTT の Trigger は 1～2分程度遅れがち（特に無料アカウントだと）なので、「0 minutes」はその時刻より少し後に実行されることに注意
1. 「Then That」に Webhooks を選択し、下記のように設定
    * 下記は開始時刻の60秒前に予定のタイトルを読み上げる例
    ![](./img/IFTTT_webhooks.png)

|  |  |
|---|---|
| URL | https://api.beebotte.com/v1/data/publish/チャンネル名/リソース名?token=認証トークン |
| Method | POST |
| Content Type | application/json |
| Body | `{"data":"<talk>{{Title}}</talk><time>{{Starts}}</time><before>60</before>"}` |
