from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# API route to get available formats
@app.route('/formats', methods=['POST'])
def formats():
    from yt_dlp.utils import DownloadError

    data = request.get_json()
    url = data.get('url')

    try:
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])

            format_list = []
            for fmt in formats:
                if fmt.get('vcodec') != 'none':  # Only include video (with or without audio)
                    resolution = fmt.get('height', 'Unknown')
                    note = 'Video+Audio' if fmt.get('acodec') != 'none' else 'Video-only'
                    format_list.append({
                        'format_id': fmt['format_id'],
                        'resolution': f"{resolution}p" if isinstance(resolution, int) else resolution,
                        'ext': fmt['ext'],
                        'note': note
                    })

        # Sort by resolution (desc), fallback to lowest
        format_list = sorted(
            format_list,
            key=lambda f: int(f['resolution'].replace('p', '')) if f['resolution'] != 'Unknown' else 0,
            reverse=True
        )

        return jsonify({'formats': format_list})
    except DownloadError as e:
        return jsonify({'error': 'Invalid YouTube link or format could not be fetched.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Route to download selected format
@app.route('/download', methods=['POST'])
def download():
    video_url = request.form['url']
    format_id = request.form['format_id']
    temp_filename = f"{uuid.uuid4()}.mp4"
    output_path = os.path.join('downloads', temp_filename)

    ydl_opts = {
        'format': format_id,
        'outtmpl': output_path,
        'merge_output_format': 'mp4'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return f"Download failed: {str(e)}", 500

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    app.run(debug=True)

