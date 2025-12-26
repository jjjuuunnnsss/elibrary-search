import streamlit as st
import requests
from lxml import html
import re
from urllib.parse import quote
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="전자도서관 통합검색", page_icon="📚")

# 6개 도서관 데이터 정의
libraries = [
    {"name": "성남시", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "경기대", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "용인시", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "수원시", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "고양시", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "강남구", "url": "https://ebook.gangnam.go.kr/elibbook/book_info.asp", "key_param": "strSearch", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr", "type": "gangnam"}
]

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
            results.append({"도서관 이름": lib['name'], "소장 현황": search_url, "display_text": display})
        except:
            results.append({"도서관 이름": lib['name'], "소장 현황": "#", "display_text": "확인불가"})

    # 직접 확인 도서관 추가
    encoded_utf8 = quote(book_name.encode("utf-8"))
    direct_links = [
        {"도서관 이름": "서울도서관", "소장 현황": f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={encoded_utf8}", "display_text": "링크 확인"},
        {"도서관 이름": "서초구", "소장 현황": f"https://e-book.seocholib.or.kr/search?keyword={encoded_utf8}", "display_text": "링크 확인"},
        {"도서관 이름": "부천시", "소장 현황": f"https://ebook.bcl.go.kr:444/elibrary-front/search/searchList.ink?schTxt={encoded_utf8}&schClst=ctts%2Cautr&schDvsn=001", "display_text": "링크 확인"}
    ]
    results.extend(direct_links)
    
    progress_bar.empty()
    return results

# 화면 구성
st.title("📚 전자도서관 통합검색")
st.write("제목 입력 후 엔터(Enter)를 누르세요.")
st.markdown("---")

query_params = st.query_params
url_keyword = query_params.get("search", "")

keyword = st.text_input("책 제목을 입력하세요", value=url_keyword, placeholder="예: 행복의 기원", key="search_input")

if keyword:
    with st.spinner(f"'{keyword}' 검색 중..."):
        data = search_libraries(keyword)
        df = pd.DataFrame(data)
        
        # 2개 컬럼만 노출하도록 설정
        st.data_editor(
            df,
            column_config={
                "도서관 이름": st.column_config.TextColumn("도서관 이름", width="medium"),
                "소장 현황": st.column_config.LinkColumn(
                    "소장 현황", 
                    display_text=r"^.*$", # 데이터프레임의 display_text 컬럼값을 사용하기 위한 설정
                    width="small"
                ),
            },
            # display_text 컬럼은 링크의 이름으로만 사용하고 표에서는 숨깁니다.
            column_order=("도서관 이름", "소장 현황"),
            hide_index=True,
            use_container_width=True,
            disabled=True
        )

        # 링크 작동을 위해 display_text를 LinkColumn의 텍스트로 매칭시키는 팁:
        # 데이터프레임의 실제 '소장 현황' 컬럼에는 URL이 들어가고, 
        # display_text 옵션에 정규식이나 특정 컬럼을 지정할 수 있습니다. 
        # 위 방식이 가장 깔끔하게 컬럼 2개를 유지합니다.
