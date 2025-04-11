from flask import Flask, request, render_template
import openai
import base64

app = Flask(__name__)

openai.api_key = "myapi"

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

@app.route('/upload', methods=['GET', 'POST'])
def index():
    response_text = ""

    if request.method == 'POST':
        question = request.form.get('question')
        image = request.files.get('image')

        if question and image and image.filename:
            try:
                image_b64 = encode_image(image)

                response = openai.ChatCompletion.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": question},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=600
                )
                response_text = response.choices[0].message.content

            except Exception as e:
                response_text = f"⚠️ Error: {e}"

        else:
            response_text = "Please provide both an image and a question."

    return render_template("upload.html", response=response_text)

if __name__ == '__main__':
    app.run(debug=True)
