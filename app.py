import streamlit as st
import requests
from lxml import html
import re
from urllib.parse import quote
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="전자도서관 통합검색", page_icon="📚")

# 2. 도서관 데이터 정의 (함수보다 위에 있어야 함)
libraries = [
    {"name": "성남시", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "경기대", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "용인시", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "수원시", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "고양시", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "강남구", "url": "https://ebook.gangnam.go.kr/elibbook/book_info.asp", "key_param": "strSearch", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr", "type": "gangnam"}
]

# 3. 검색 함수 정의
def search_libraries(book_name):
    results = []
    progress_bar = st.progress(0)
    total = len(libraries)

    for i, lib in enumerate(libraries):
        progress_bar.progress((i + 1) / total)
        try:
            encoded_query = quote(book_name.encode(lib["encoding"]))
            if lib["type"] == "gangnam":
                search_url = f"{lib['url']}?{lib['key_param']}={encoded_query}&search=title"
            else:
                search_url = f"{lib['url']}?{lib['key_param']}={encoded_query}&schClst=ctts%2Cautr&schDvsn=001"

            resp = requests.get(search_url, timeout=5)
            count = 0
            if resp.status_code == 200:
                tree = html.fromstring(resp.content)
                nodes = tree.xpath(lib["xpath"])
                if nodes:
                    count_match = re.findall(r'\d+', "".join(nodes))
                    count = int(count_match[0]) if count_match else 0
            
            display = f"{count}권" if count > 0 else "없음"
            results.append({"도서관 이름": lib['name'], "url": search_url, "소장 현황": display})
        except:
            results.append({"도서관 이름": lib['name'], "url": "#", "소장 현황": "확인불가"})

    # 직접 확인 도서관 추가
    encoded_utf8 = quote(book_name.encode("utf-8"))
    direct_links = [
        {"도서관 이름": "서울도서관", "url": f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={encoded_utf8}", "소장 현황": "링크 확인필요"},
        {"도서관 이름": "서초구", "url": f"https://e-book.seocholib.or.kr/search?keyword={encoded_utf8}", "소장 현황": "링크 확인필요"},
        {"도서관 이름": "부천시", "url": f"https://ebook.bcl.go.kr:444/elibrary-front/search/searchList.ink?schTxt={encoded_utf8}&schClst=ctts%2Cautr&schDvsn=001", "소장 현황": "링크 확인필요"}
    ]
    results.extend(direct_links)
    
    progress_bar.empty()
    return results

# 4. 화면 구성
st.title("📚 전자도서관 통합검색")
st.write("제목 입력 후 엔터(Enter)를 누르세요.")
st.markdown("---")

# Alfred 연동을 위한 파라미터 읽기
query_params = st.query_params
url_keyword = query_params.get("search", "")

# [핵심] keyword 변수 정의가 if 문보다 먼저 와야 합니다.
keyword = st.text_input("책 제목을 입력하세요", value=url_keyword, placeholder="예: 행복의 기원", key="search_input")

# 5. 검색 실행 및 결과 출력
if keyword:
    with st.spinner(f"'{keyword}' 검색 중..."):
        data = search_libraries(keyword)
        df = pd.DataFrame(data)
        
        # 2개 컬럼만 깔끔하게 보여주는 설정
        st.data_editor(
            df,
            column_config={
                "도서관 이름": st.column_config.TextColumn("도서관 이름", width="medium"),
                "소장 현황": st.column_config.LinkColumn(
                    "소장 현황", 
                    width="small",
                    display_text=None
