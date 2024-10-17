from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from cryptography.fernet import Fernet
from PIL import Image
import io
import os
import base64
import hashlib

app = Flask(__name__)
app.secret_key = "steganography_secret_key" 


def password_to_key(password):
    password_bytes = password.encode('utf-8')
    key = hashlib.sha256(password_bytes).digest()  
    return base64.urlsafe_b64encode(key) 

#
def encode_message(image, message, password):
    try:
        fernet = Fernet(password_to_key(password))
        encrypted_message = fernet.encrypt(message.encode())
    except Exception as e:
        return None, str(e)
    
    img = Image.open(image)
    img = img.convert("RGB")
    encoded_img = img.copy()

    encrypted_message += b'###'
    
    binary_msg = ''.join(format(byte, '08b') for byte in encrypted_message)
    data_index = 0
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            
            if data_index < len(binary_msg):
                r = int(format(r, '08b')[:-1] + binary_msg[data_index], 2)
                data_index += 1
            if data_index < len(binary_msg):
                g = int(format(g, '08b')[:-1] + binary_msg[data_index], 2)
                data_index += 1
            if data_index < len(binary_msg):
                b = int(format(b, '08b')[:-1] + binary_msg[data_index], 2)
                data_index += 1
            
            encoded_img.putpixel((x, y), (r, g, b))
            
            if data_index >= len(binary_msg):
                break
        if data_index >= len(binary_msg):
            break

    return encoded_img, None

def decode_message(image, password):
    try:
        fernet = Fernet(password_to_key(password))
    except Exception as e:
        return None, "Invalid password or encryption method."

    img = Image.open(image)
    binary_msg = ""
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            binary_msg += format(r, '08b')[-1]
            binary_msg += format(g, '08b')[-1]
            binary_msg += format(b, '08b')[-1]

    message_bits = [binary_msg[i:i+8] for i in range(0, len(binary_msg), 8)]
    decoded_bytes = bytes([int(byte, 2) for byte in message_bits])

    
    delimiter = b'###'
    delimiter_index = decoded_bytes.find(delimiter)
    if delimiter_index == -1:
        return None, "No hidden message found."

    try:
        message = fernet.decrypt(decoded_bytes[:delimiter_index])
        return message.decode('utf-8'), None
    except Exception as e:
        return None, "Failed to decrypt message. Check the password."

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        if "encode" in request.form:
     
            image = request.files.get("encode_image")
            message = request.form.get("encode_message")
            password = request.form.get("encode_password")
            
            if not image or not message or not password:
                flash("Please provide an image, message, and password for encoding.", "danger")
                return redirect(url_for('index'))
            
            encoded_img, error = encode_message(image, message, password)
            if error:
                flash(f"Encoding failed: {error}", "danger")
                return redirect(url_for('index'))
            
            byte_io = io.BytesIO()
            encoded_img.save(byte_io, 'PNG')
            byte_io.seek(0)
            flash("Message successfully encoded!", "success")
            return send_file(byte_io, mimetype='image/png', as_attachment=True, download_name="encoded_image.png")
        
        elif "decode" in request.form:
 
            image = request.files.get("decode_image")
            password = request.form.get("decode_password")
            
            if not image or not password:
                flash("Please provide an image and password for decoding.", "danger")
                return redirect(url_for('index'))
            
            decoded_message, error = decode_message(image, password)
            if error:
                flash(f"Decoding failed: {error}", "danger")
            else:
                flash(f"Decoded message: {decoded_message}", "success")
    
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
