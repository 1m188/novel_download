import sys
import requests
from bs4 import BeautifulSoup

URL = 'http://www.waptxt.org/96031'
WEBSITE = 'http://www.waptxt.org'
ENCODING = 'gbk'
PARSER = 'lxml'


def get_bsobj(url: str) -> BeautifulSoup:
    response = requests.get(url)
    response.encoding = ENCODING
    return BeautifulSoup(response.text, PARSER)


def get_chapter(url: str) -> str:
    '''
    获取章节名称及其内容

    url: 章节地址
    return: 章节名称\\n章节内容\\n\\n

    其中，章节内容是每段进行分行
    '''

    soup = get_bsobj(url)
    cont = soup.find('div', {'class': 'con_txt'})
    title = soup.find('div', {'class': 'title'})

    title_text = title.h1.text.strip()
    cont_text = '\n'.join(cont.stripped_strings)

    return title_text + '\n' + cont_text + '\n\n'


def get_chapter_url_list() -> list[str]:
    '''
    获取章节url的列表
    '''

    url = URL
    res: list[str] = []

    while True:
        soup = get_bsobj(url)
        for i in soup.dl.findAll('a'):
            res.append(WEBSITE + i.attrs['href'])

        next_page = soup.find('span', {'class': 'right'})
        next_page_href = next_page.a.attrs.get('href', None)
        if not next_page_href: break
        url = WEBSITE + next_page_href

    return res


def save_novel(start_chapter: int = 1):
    '''
    保存小说

    @param start_chapter 从第几章开始
    '''

    print('开始获取章节目录...')
    chapter_url_list = get_chapter_url_list()
    print('章节目录获取完毕')
    print('开始缓存')
    with open(sys.path[0] + '/道诡异仙.txt', 'a', encoding='utf-8') as f:
        for i, v in enumerate(chapter_url_list[start_chapter - 1:]):
            f.write(get_chapter(v))
            print(f'第{i + start_chapter}章缓存完毕')
    print('所有章节缓存完毕！')


if __name__ == '__main__':
    save_novel()
