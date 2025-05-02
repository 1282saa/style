from flask import Flask, request, jsonify
import json
import sys
import os
import asyncio
from mcp_server import search_content, check_sentence, load_json_data

app = Flask(__name__)

# JSON 파일 로드
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file = os.path.join(script_dir, "7_2자주 틀리는 말01.json")
data = load_json_data(json_file)

@app.route('/api/search', methods=['POST'])
def search():
    content = request.json
    if not content or 'query' not in content:
        return jsonify({"error": "검색어를 입력해주세요."}), 400
    
    query = content['query']
    results = search_content(data, query)
    
    return jsonify({"results": results})

@app.route('/api/check-sentence', methods=['POST'])
def check():
    content = request.json
    if not content or 'sentence' not in content:
        return jsonify({"error": "검사할 문장을 입력해주세요."}), 400
    
    sentence = content['sentence']
    corrections = check_sentence(data, sentence)
    
    result = {
        "original": sentence,
        "corrections": corrections,
        "summary": f"{len(corrections)}개의 교정 제안 발견"
    }
    
    return jsonify(result)

@app.route('/api/list-sections', methods=['GET'])
def list_sections():
    sections = [section['heading'] for section in data['sections']]
    return jsonify({"sections": sections})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)