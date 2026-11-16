import os
import uuid
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from flask import Flask, render_template, request, send_from_directory, jsonify, session

app = Flask(__name__)
app.secret_key = "change-this-to-a-strong-secret-key-in-production"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ===================== EVERYTHING FREE =====================
MAX_SIZE = 2000


def process_image(img, feature, value=1.0):
    value = float(value)

    # ---------- Basic Adjustments ----------
    if feature == "brightness":
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Brightness(pil)
        return cv2.cvtColor(np.array(enhancer.enhance(value)), cv2.COLOR_RGB2BGR)

    if feature == "contrast":
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Contrast(pil)
        return cv2.cvtColor(np.array(enhancer.enhance(value)), cv2.COLOR_RGB2BGR)

    if feature == "saturation":
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Color(pil)
        return cv2.cvtColor(np.array(enhancer.enhance(value)), cv2.COLOR_RGB2BGR)

    if feature == "warmth":
        # Warmth / Coolness (Red vs Blue balance)
        b, g, r = cv2.split(img)
        r = cv2.convertScaleAbs(r, alpha=value)
        b = cv2.convertScaleAbs(b, alpha=(2.0 - value))
        return cv2.merge((b, g, r))

    if feature == "hue":
        # Hue Shift
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + int(value * 10)) % 180
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # ---------- Noise Removal ----------
    if feature == "gaussian":
        k = int(value) if int(value) % 2 == 1 else int(value) + 1
        k = max(3, min(k, 31))
        return cv2.GaussianBlur(img, (k, k), 0)

    if feature == "median":
        k = int(value) if int(value) % 2 == 1 else int(value) + 1
        k = max(3, min(k, 15))
        return cv2.medianBlur(img, k)

    if feature == "bilateral":
        return cv2.bilateralFilter(img, 9, 75, 75)

    if feature == "mean":
        k = int(value) if int(value) % 2 == 1 else int(value) + 1
        k = max(3, min(k, 15))
        return cv2.blur(img, (k, k))

    # ---------- Edge Detection ----------
    if feature == "sobel":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel = np.sqrt(sobelx**2 + sobely**2)
        sobel = np.uint8(np.clip(sobel, 0, 255))
        return cv2.cvtColor(sobel, cv2.COLOR_GRAY2BGR)

    if feature == "canny":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    if feature == "laplacian":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        lap = np.uint8(np.absolute(lap))
        return cv2.cvtColor(lap, cv2.COLOR_GRAY2BGR)

    if feature == "log":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        log = cv2.Laplacian(blur, cv2.CV_64F)
        log = np.uint8(np.absolute(log))
        return cv2.cvtColor(log, cv2.COLOR_GRAY2BGR)

    # ---------- Sharpening ----------
    if feature == "sharpen":
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
        return cv2.filter2D(img, -1, kernel)

    if feature == "unsharp":
        blurred = cv2.GaussianBlur(img, (9, 9), 10.0)
        return cv2.addWeighted(img, 1.5 + value * 0.3, blurred, -0.5 - value * 0.2, 0)

    # ---------- Artistic ----------
    if feature == "grayscale":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    if feature == "invert":
        return cv2.bitwise_not(img)

    if feature == "posterize":
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        levels = max(2, min(8, int(value)))
        return cv2.cvtColor(np.array(ImageOps.posterize(pil, levels)), cv2.COLOR_RGB2BGR)

    if feature == "sepia":
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])
        sepia = cv2.transform(img, kernel)
        return np.clip(sepia, 0, 255).astype(np.uint8)

    if feature == "emboss":
        kernel = np.array([[-2, -1, 0],
                           [-1,  1, 1],
                           [ 0,  1, 2]])
        return cv2.filter2D(img, -1, kernel) + 128

    if feature == "threshold":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    # ---------- New Artistic Features ----------
    if feature == "sketch":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)

    if feature == "cartoon":
        # 1. Edge detection for outlines
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        # 2. Smooth colors
        color = cv2.bilateralFilter(img, 9, 300, 300)
        # 3. Combine
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        return cartoon

    if feature == "pixelate":
        # value used as block size
        block_size = max(2, int(30 - value * 5))
        h, w = img.shape[:2]
        temp = cv2.resize(img, (w // block_size, h // block_size), interpolation=cv2.INTER_LINEAR)
        return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)

    # ---------- Morphological ----------
    if feature == "erosion":
        kernel = np.ones((5, 5), np.uint8)
        return cv2.erode(img, kernel, iterations=1)

    if feature == "dilation":
        kernel = np.ones((5, 5), np.uint8)
        return cv2.dilate(img, kernel, iterations=1)

    # ---------- AI Placeholders ----------
    if feature == "bg_remove":
        return img

    if feature == "upscale":
        return cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    if feature == "face_retouch":
        return img

    return img


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/process", methods=["POST"])
def process():
    file = request.files.get("image")
    feature = request.form.get("feature", "gaussian")
    value = request.form.get("value", 1.0)

    if not file:
        return jsonify({"error": "No image uploaded"}), 400

    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"error": "Invalid image file"}), 400

    # Resize if too large
    h, w = img.shape[:2]
    if max(h, w) > MAX_SIZE:
        scale = MAX_SIZE / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    result = process_image(img, feature, value)

    filename = f"{uuid.uuid4().hex}.png"
    out_path = os.path.join(UPLOAD_FOLDER, filename)
    cv2.imwrite(out_path, result)

    return jsonify({
        "result_url": f"/uploads/{filename}",
        "watermark": False
    })


@app.route("/uploads/<name>")
def uploaded_file(name):
    return send_from_directory(UPLOAD_FOLDER, name)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)