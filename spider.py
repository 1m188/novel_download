import sys
import requests
from bs4 import BeautifulSoup
from typing import List

URL = 'http://www.waptxt.org/96031'
WEBSITE = 'http://www.waptxt.org'
ENCODING = 'gbk'
PARSER = 'lxml'


class Spider:

    def __init__(self, website: str, url: str, encoding: str, parser: str) -> None:
        '''
        @param website 小说网站地址
        @param url 小说页面（目录页面）地址
        @param encoding: 网站编码
        @param parser: 解码器
        '''

        self.website = website
        self.url = url
        self.encoding = encoding
        self.parser = parser

    def get_bsobj(self, url: str) -> BeautifulSoup:
        response = requests.get(url)
        response.encoding = self.encoding
        return BeautifulSoup(response.text, self.parser)

    def get_chapter(self, curl: str) -> str:
        '''
        获取章节名称及其内容

        curl: 章节地址
        return: 章节名称\\n章节内容\\n\\n

        其中，章节内容是每段进行分行
        '''

        soup = self.get_bsobj(curl)
        cont = soup.find('div', {'class': 'con_txt'})
        title = soup.find('div', {'class': 'title'})

        title_text = title.h1.text.strip()
        cont_text = '\n'.join(cont.stripped_strings)

        return title_text + '\n' + cont_text + '\n\n'

    def get_chapter_url_list(self) -> List[str]:
        '''
        获取章节url的列表
        '''

        url = self.url
        res: list[str] = []

        while True:
            soup = self.get_bsobj(url)
            for i in soup.dl.findAll('a'):
                res.append(self.website + i.attrs['href'])

            next_page = soup.find('span', {'class': 'right'})
            next_page_href = next_page.a.attrs.get('href', None)
            if not next_page_href:
                break
            url = self.website + next_page_href

        return res

    def save_novel(self, file_path: str, is_append: bool, start_chapter: int = 1):
        '''
        保存小说

        @param file_path 保存文件路径
        @param is_append 是否追加
        @param start_chapter 从第几章开始
        '''

        print('开始获取章节目录...')
        chapter_url_list = self.get_chapter_url_list()
        print('章节目录获取完毕')
        print('开始缓存')
        with open(file_path, 'a' if is_append else 'w', encoding='utf-8') as f:
            for i, v in enumerate(chapter_url_list[start_chapter - 1:]):
                f.write(self.get_chapter(v))
                print(f'第{i + start_chapter}章缓存完毕')
        print('所有章节缓存完毕！')


if __name__ == '__main__':
    spider = Spider(WEBSITE, URL, ENCODING, PARSER)
    spider.save_novel(sys.path[0] + '/道诡异仙.txt', False)
