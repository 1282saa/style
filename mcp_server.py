import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, Any, Union

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# 디버깅 출력 함수
def debug_log(message):
    print(f"DEBUG: {message}", file=sys.stderr)

# JSON 데이터 로드
def load_json_data(file_path: str) -> Dict:
    debug_log(f"파일 로드 시도: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            debug_log(f"파일 로드 성공: {file_path}")
            return data
    except Exception as e:
        debug_log(f"파일 로드 실패: {e}")
        raise

# 각 요청에 대한 컨텐츠 찾기 - 개선된 로직
def search_content(data: Dict, query: str) -> List[Dict]:
    results = []
    query = query.lower()  # 미리 소문자로 변환
    
    # 디버그 로그
    print(f"검색어: '{query}'로 검색을 시작합니다.", file=sys.stderr)
    
    # 제목 또는 내용에서 검색
    if query in data['title'].lower() or query in data['content'].lower():
        print(f"메인 제목 또는 내용에서 검색어를 찾았습니다.", file=sys.stderr)
        results.append({
            'title': data['title'],
            'content': data['content']
        })
    
    # 섹션에서 검색
    for section_idx, section in enumerate(data['sections']):
        section_heading = section['heading'].lower()
        print(f"섹션 {section_idx+1} 검색: '{section_heading}'", file=sys.stderr)
        
        # 섹션 제목에서 검색어를 찾은 경우
        section_match = False
        if query in section_heading:
            print(f"섹션 제목 '{section_heading}'에서 검색어를 찾았습니다.", file=sys.stderr)
            section_match = True
            section_result = {
                'heading': section['heading'],
                'content': [],
                'subSections': []
            }
            
            # 섹션 자체 내용이 있으면 추가
            if 'content' in section and isinstance(section['content'], list):
                section_result['content'] = section['content']
            
            # 이 섹션의 모든 서브섹션 추가
            if 'subSections' in section:
                for subsection in section['subSections']:
                    section_result['subSections'].append({
                        'heading': subsection['heading'],
                        'content': subsection['content']
                    })
            
            results.append(section_result)
        
        # 서브섹션 검색 (섹션 제목과 일치하더라도 서브섹션도 검색)
        if 'subSections' in section:
            for subsec_idx, subsection in enumerate(section['subSections']):
                subsection_heading = subsection['heading'].lower()
                print(f"  서브섹션 {subsec_idx+1} 검색: '{subsection_heading}'", file=sys.stderr)
                
                # 서브섹션 제목에서 검색어를 찾은 경우
                if query in subsection_heading:
                    print(f"  서브섹션 제목 '{subsection_heading}'에서 검색어를 찾았습니다.", file=sys.stderr)
                    
                    # 이미 섹션이 추가되었다면 중복 추가하지 않음
                    if not section_match:
                        results.append({
                            'heading': section['heading'],
                            'subSections': [{
                                'heading': subsection['heading'],
                                'content': subsection['content']
                            }]
                        })
                
                # 서브섹션 내용에서 검색
                if 'content' in subsection:
                    # 리스트인 경우 (단순 항목 목록)
                    if isinstance(subsection['content'], list):
                        for item_idx, item in enumerate(subsection['content']):
                            # 문자열 항목인 경우
                            if isinstance(item, str) and query in item.lower():
                                print(f"    항목 {item_idx+1}에서 검색어를 찾았습니다.", file=sys.stderr)
                                if not section_match:
                                    results.append({
                                        'heading': section['heading'],
                                        'subSections': [{
                                            'heading': subsection['heading'],
                                            'content': subsection['content']
                                        }]
                                    })
                                break
                            
                            # 딕셔너리 항목인 경우 (용어와 정의)
                            if isinstance(item, dict):
                                # term/definition 구조인 경우
                                if 'term' in item and 'definition' in item:
                                    if query in item['term'].lower() or query in item['definition'].lower():
                                        print(f"    용어/정의 {item_idx+1}에서 검색어를 찾았습니다.", file=sys.stderr)
                                        results.append({
                                            'term': item['term'],
                                            'definition': item['definition'],
                                            'context': {
                                                'section': section['heading'],
                                                'subsection': subsection['heading']
                                            }
                                        })
                                # variant1/variant2 구조인 경우
                                elif 'variant1' in item and 'variant2' in item:
                                    if query in item['variant1'].lower() or query in item['variant2'].lower():
                                        print(f"    변형 {item_idx+1}에서 검색어를 찾았습니다.", file=sys.stderr)
                                        results.append({
                                            'variant1': item['variant1'],
                                            'variant2': item['variant2'],
                                            'context': {
                                                'section': section['heading'],
                                                'subsection': subsection['heading']
                                            }
                                        })
                                # current/added 구조인 경우
                                elif 'current' in item and 'added' in item:
                                    if query in item['current'].lower() or query in item['added'].lower():
                                        print(f"    추가 표준어 {item_idx+1}에서 검색어를 찾았습니다.", file=sys.stderr)
                                        results.append({
                                            'current': item['current'],
                                            'added': item['added'],
                                            'context': {
                                                'section': section['heading'],
                                                'subsection': subsection['heading']
                                            }
                                        })
    
    print(f"검색 결과 수: {len(results)}", file=sys.stderr)
    return results

# 문장 교정 검사 함수
def check_sentence(data: Dict, sentence: str) -> List[Dict]:
    corrections = []
    sentence_lower = sentence.lower()
    
    print(f"문장 검사 시작: '{sentence}'", file=sys.stderr)
    
    # 모든 섹션과 서브섹션을 확인
    for section in data['sections']:
        # 서브섹션 확인
        if 'subSections' in section:
            for subsection in section['subSections']:
                if 'content' in subsection and isinstance(subsection['content'], list):
                    for item in subsection['content']:
                        # 용어/정의 또는 변형/교정 쌍 확인
                        if isinstance(item, dict):
                            # 오류 표현과 수정 표현 쌍 확인
                            if 'variant1' in item and 'variant2' in item:
                                incorrect = item['variant1'].lower()
                                correct = item['variant2']
                                
                                if incorrect in sentence_lower:
                                    corrections.append({
                                        "incorrect": item['variant1'],
                                        "correct": correct,
                                        "context": {
                                            "section": section['heading'],
                                            "subsection": subsection['heading']
                                        },
                                        "position": sentence_lower.find(incorrect)
                                    })
                            # 추가 표준어 확인
                            elif 'current' in item and 'added' in item:
                                current = item['current'].lower()
                                added = item['added']
                                
                                if current in sentence_lower:
                                    corrections.append({
                                        "current": item['current'],
                                        "suggestion": added,
                                        "context": {
                                            "section": section['heading'],
                                            "subsection": subsection['heading']
                                        },
                                        "position": sentence_lower.find(current)
                                    })
    
    # 위치 순서로 정렬
    corrections.sort(key=lambda x: x.get('position', 0))
    print(f"발견된 교정 항목 수: {len(corrections)}", file=sys.stderr)
    return corrections

# MCP 서버 초기화
server = Server("stylebook-mcp-server")

# 도구 정의 - list_tools 메서드 사용
@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """이 메서드는 도구 목록을 반환합니다."""
    print("도구 목록 요청받음", file=sys.stderr)
    return [
        types.Tool(
            name="search-stylebook",
            description="스타일북에서 특정 어휘나 표현에 대한 정보를 검색합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 단어나 표현"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="list-sections",
            description="스타일북의 모든 섹션 목록을 가져옵니다",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="check-sentence",
            description="문장을 입력받아 스타일북 규칙에 따라 교정 제안을 제공합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "sentence": {
                        "type": "string",
                        "description": "검사할 문장"
                    }
                },
                "required": ["sentence"]
            }
        )
    ]

# 도구 호출 처리
@server.call_tool()
async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[types.TextContent]:
    """도구 호출을 처리하는 함수"""
    print(f"도구 호출: {name}, 인자: {arguments}", file=sys.stderr)
    
    try:
        # JSON 파일 경로
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_file = os.path.join(script_dir, "7_2자주 틀리는 말01.json")
        
        if not os.path.exists(json_file):
            print(f"JSON 파일을 찾을 수 없음: {json_file}", file=sys.stderr)
            return [types.TextContent(
                type="text",
                text=f"JSON 파일을 찾을 수 없습니다. 경로: {json_file}"
            )]
        
        data = load_json_data(json_file)
        
        if name == "search-stylebook":
            if not arguments or "query" not in arguments:
                return [types.TextContent(
                    type="text",
                    text="검색어를 입력해주세요."
                )]
            
            query = arguments["query"]
            results = search_content(data, query)
            
            if not results:
                return [types.TextContent(
                    type="text",
                    text=f"'{query}'에 대한 검색 결과가 없습니다."
                )]
            
            response_text = f"'{query}'에 대한 검색 결과:\n\n"
            
            for result in results:
                if 'title' in result:
                    response_text += f"## {result['title']}\n{result['content']}\n\n"
                elif 'heading' in result:
                    response_text += f"## {result['heading']}\n"
                    if 'content' in result and result['content']:
                        if isinstance(result['content'], list):
                            response_text += "\n".join(result['content']) + "\n\n"
                        else:
                            response_text += str(result['content']) + "\n\n"
                    
                    if 'subSections' in result:
                        for subsection in result['subSections']:
                            response_text += f"### {subsection['heading']}\n"
                            if isinstance(subsection['content'], list):
                                for item in subsection['content']:
                                    if isinstance(item, dict):
                                        if 'term' in item and 'definition' in item:
                                            response_text += f"- {item['term']}: {item['definition']}\n"
                                        elif 'variant1' in item and 'variant2' in item:
                                            response_text += f"- {item['variant1']} ↔ {item['variant2']}\n"
                                        elif 'current' in item and 'added' in item:
                                            response_text += f"- {item['current']} ↔ {item['added']}\n"
                                    else:
                                        response_text += f"- {item}\n"
                            else:
                                response_text += f"{subsection['content']}\n\n"
                elif 'term' in result:
                    if 'context' in result:
                        response_text += f"## {result['context']['section']}\n### {result['context']['subsection']}\n"
                    response_text += f"**{result['term']}**: {result['definition']}\n\n"
                elif 'variant1' in result:
                    if 'context' in result:
                        response_text += f"## {result['context']['section']}\n### {result['context']['subsection']}\n"
                    response_text += f"**{result['variant1']}** ↔ **{result['variant2']}**\n\n"
                elif 'current' in result:
                    if 'context' in result:
                        response_text += f"## {result['context']['section']}\n### {result['context']['subsection']}\n"
                    response_text += f"**{result['current']}** ↔ **{result['added']}**\n\n"
            
            return [types.TextContent(
                type="text",
                text=response_text
            )]
        
        elif name == "list-sections":
            sections = [section['heading'] for section in data['sections']]
            response_text = "## 스타일북 섹션 목록\n\n"
            
            for i, section in enumerate(sections, 1):
                response_text += f"{i}. {section}\n"
            
            return [types.TextContent(
                type="text",
                text=response_text
            )]
            
        elif name == "check-sentence":
            if not arguments or "sentence" not in arguments:
                return [types.TextContent(
                    type="text",
                    text="검사할 문장을 입력해주세요."
                )]
            
            sentence = arguments["sentence"]
            corrections = check_sentence(data, sentence)
            
            if not corrections:
                return [types.TextContent(
                    type="text",
                    text=f"문장 '{sentence}'에서 교정이 필요한 표현을 찾지 못했습니다."
                )]
            
            # JSON 형식으로 응답 (Claude와 연동을 위해)
            result = {
                "original": sentence,
                "corrections": corrections,
                "summary": f"{len(corrections)}개의 교정 제안 발견"
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        return [types.TextContent(
            type="text",
            text=f"알 수 없는 도구: {name}"
        )]
    except Exception as e:
        print(f"도구 실행 중 오류 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return [types.TextContent(
            type="text",
            text=f"오류가 발생했습니다: {str(e)}"
        )]

async def main():
    """서버 실행 함수"""
    try:
        print("스타일북 MCP 서버 시작 중...", file=sys.stderr)
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            print("서버가 초기화되었습니다. 연결 준비 완료", file=sys.stderr)
            
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="stylebook-mcp-server",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        print(f"서버 실행 중 오류 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

if __name__ == "__main__":
    asyncio.run(main())