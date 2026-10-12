import os
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

EXPORT_DIR = "/tmp/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

@app.route('/api/process-video', methods=['POST'])
def process_video():
    data = request.json or {}
    youtube_url = data.get('youtube_url')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    output_name = data.get('output_name', 'clip_generado.mp4')
    
    if not youtube_url or start_time is None or end_time is None:
        return jsonify({"error": "Faltan parámetros de entrada"}), 400

    output_path = os.path.join(EXPORT_DIR, output_name)
    temp_input_path = os.path.join(EXPORT_DIR, "video_origen.mp4")
    duration = end_time - start_time

    try:
        # Eliminar descargas previas si existen
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)

        # Configuración de yt-dlp usando cookies.txt para autenticación
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': temp_input_path,
            'cookiefile': 'cookies.txt',  # Lee las cookies subidas a GitHub
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'mweb', 'android']
                }
            }
        }

        # Descargar el video usando la sesión de las cookies
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Recortar y reencuadrar a 9:16 con FFmpeg
        ffmpeg_cmd = (
            f'ffmpeg -y -ss {start_time} -i "{temp_input_path}" -t {duration} '
            f'-vf "crop=ih*(9/16):ih,scale=720:1280" -c:v libx264 -preset ultrafast '
            f'-c:a aac "{output_path}"'
        )
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        # Limpiar el video origen para ahorrar espacio
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)

        return jsonify({
            "status": "success",
            "download_url": f"/download/{output_name}"
        })

    except Exception as e:
        return jsonify({"error": f"Error al procesar el video: {str(e)}"}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(EXPORT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
