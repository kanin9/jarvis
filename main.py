import json
import os

import openai
import tiktoken
from werkzeug.utils import secure_filename

from config import OPENAI_API_KEY
from bogus import getFillerData, Call
from flask import Flask, render_template, flash, redirect, url_for, request, make_response
import sqlite3

app = Flask(__name__)
openai.api_key = OPENAI_API_KEY
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

con = sqlite3.connect("calls.db")
cur = con.cursor()
req = cur.execute("SELECT name FROM sqlite_master WHERE type='table';")

if "calls" not in cur.fetchall()[0]:
    cur.execute("CREATE TABLE calls(id INTEGER PRIMARY KEY,"
                "date VARCHAR(255) NOT NULL,"
                "type VARCHAR(255) NOT NULL,"
                "caller VARCHAR(255) NOT NULL,"
                "file VARCHAR(255) NOT NULL,"
                "commentaries TEXT NOT NULL,"
                "status VARCHAR(255) NOT NULL)")

calls = []


def tokenCount(string: str, encoding: str):
    enc = tiktoken.get_encoding(encoding)
    tokens = len(enc.encode(string))
    return tokens


@app.route("/index")
@app.route("/")
def index():
    return render_template('reports/deals_stages.html', title="Звонки", deals=calls)


@app.route("/process", methods=['GET', 'POST'])
def process():
    if request.method == 'POST':
        audio = request.files['file']
        print(audio)
        comment = ""
        transcript = request.form['transcript']

        location = None
        if audio.filename != '':
            location = 'static/audio/' + secure_filename(audio.filename)
            counter = 1
            basename, extension = os.path.splitext(secure_filename(audio.filename))
            while os.path.exists(location):
                uniquefilename = f"{basename}_{counter}{extension}"
                location = 'static/audio/' + uniquefilename
                counter += 1

            audio.save(location)

        if location is not None:
            try:
                audio_file = open(location, 'rb')
                audio_transcript = openai.Audio.transcribe("whisper-1", audio_file)
                text_transcript = audio_transcript['text'].encode('utf-8').decode()
                transcript = text_transcript
            except Exception as e:
                print(e)

        if transcript != '':
            tokencost = tokenCount(transcript, 'cl100k_base')
            print(tokencost)

            if tokencost < 7000:
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system",
                             "content": "Ты ассистент помощник, который делает анализ транскрипта звонка. "
                                        "Выдели как позитивные, так и негативные стороны речи менеджера по "
                                        "продажам. Старайся думать критически."},
                            {"role": "user", "content": f"{transcript}"}
                        ]
                    )
                    comment = response['choices'][0]['message']['content']
                except Exception as e:
                    print(e)
            else:
                comment = 'Превышено ограничение по токенам в тексте.'

        print(request.form)
        status = request.form['status']
        manager = request.form['manager']
        datestr = request.form['date'].replace('-', '/').replace('T', ' ')
        calls.append(Call(datestr, request.form['type'], manager, location, comment, status))

    return redirect(url_for('index'))


@app.route('/analyze', methods=['POST'])
def analyze():
    data = {
        'text': '...'
    }
    audio = None
    if len(request.files) != 0:
        audio = request.files['file']

    transcript = request.form['transcript']

    location = None
    if audio is not None:
        if audio.filename != '':
            location = 'static/audio/' + secure_filename(audio.filename)
            counter = 1
            basename, extension = os.path.splitext(secure_filename(audio.filename))
            while os.path.exists(location):
                uniquefilename = f"{basename}_{counter}{extension}"
                location = 'static/audio/' + uniquefilename
                counter += 1

            audio.save(location)

    if location is not None:
        try:
            audio_file = open(location, 'rb')
            audio_transcript = openai.Audio.transcribe("whisper-1", audio_file)
            text_transcript = audio_transcript['text'].encode('utf-8').decode()
            transcript = text_transcript
        except Exception as e:
            data['text'] = str(e)

    if transcript != '':
        print(transcript)
        tokencost = tokenCount(transcript, 'cl100k_base')
        print(tokencost)

        if tokencost < 7000:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты ассистент помощник, который делает анализ транскрипта звонка. "
                                                      "Выдели как позитивные, так и негативные стороны речи менеджера по "
                                                      "продажам. Старайся думать критически."},
                        {"role": "user", "content": f"{transcript}"}
                    ]
                )
                data['text'] = response['choices'][0]['message']['content']
            except Exception as e:
                data['text'] = str(e)
        else:
            data['text'] = 'Обьем текста слишком большой. Превышено ограничение по токенам.'

    response = make_response(json.dumps(data), 200)
    response.mimetype = "application/json"
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
