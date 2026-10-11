import os
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

EXPORT_DIR = "/tmp/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

@app.route('/api/process-video', methods=['POST'])
def process_video():
    data = request.json
    youtube_url = data.get('youtube_url')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    output_name = data.get('output_name', 'clip_generado.mp4')
    
    if not youtube_url or start_time is None or end_time is None:
        return jsonify({"error": "Faltan parámetros de entrada"}), 400

    output_path = os.path.join(EXPORT_DIR, output_name)
    duration = end_time - start_time

    try:
        cmd_yt = f"yt-dlp -g -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]' {youtube_url}"
        stream_urls = subprocess.check_output(cmd_yt, shell=True).decode('utf-8').strip().split('\n')
        video_stream_url = stream_urls[0]

        ffmpeg_cmd = (
            f"ffmpeg -y -ss {start_time} -i \"{video_stream_url}\" -t {duration} "
            f"-vf \"crop=ih*(9/16):ih,scale=720:1280\" -c:v libx264 -preset ultrafast "
            f"-c:a aac {output_path}"
        )
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        return jsonify({
            "status": "success",
            "download_url": f"/download/{output_name}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(EXPORT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
