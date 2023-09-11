import sys, os
sys.path.insert(1,os.path.dirname(__file__))
print(sys.path)


import requests
from flask import Flask, request, render_template, send_from_directory, send_file
from char_union import make_char_union_image

app = Flask(__name__)


@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return send_from_directory(directory='output', filename=filename)


@app.route('/download/<path:url>')
def download_file(url):
    response = requests.get("https://" + url)
    with open('temp_file.png', 'wb') as f:
        f.write(response.content)
    return send_file(os.path.basename(url), as_attachment=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    chars_list = [
        request.form['input0'],
        request.form['input1'],
        request.form['input2']
    ]
    font = request.form['font']
    # do something with the input string to produce the output
    res = make_char_union_image(chars_list, font)
    if res is not None:
        img_q_save_path, img_a_save_path = res
        return render_template(
            'result_success.html', 
            img_q_save_path=img_q_save_path,
            img_a_save_path=img_a_save_path
            )
    else:
        return render_template(
            'result_fail.html', 
            result=res,
            )



if __name__ == '__main__':
    port = int(sys.argv[-1])  # 5001
    app.run(host='0.0.0.0', port=port)