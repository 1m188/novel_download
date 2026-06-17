import requests
from bs4 import BeautifulSoup
from typing import List

URL = 'http://www.waptxt.org/96031'
WEBSITE = 'http://www.waptxt.org'
ENCODING = 'gbk'
PARSER = 'lxml'

# 浏览器 User-Agent。站点会拦截 requests 的默认 UA，统一带上浏览器 UA 以正常访问。
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'


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
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers)
        response.encoding = self.encoding
        return BeautifulSoup(response.text, self.parser)

    def get_chapter(self, curl: str) -> str:
        '''
        获取章节名称及其内容

        curl: 章节地址
        return: 章节名称\\n章节内容\\n\\n

        其中，章节内容是每段进行分行
        '''

        title_txt = None
        txts = []

        while True:  # 循环求取每一页的内容
            soup = self.get_bsobj(curl)

            if title_txt == None:
                title = soup.find('div', {'class': 'title'})
                title_txt = title.h1.text.strip()

            cont = soup.find('div', {'class': 'con_txt'})
            cont_txt = '\n'.join(cont.stripped_strings)
            txts.append(cont_txt)

            chapter_go = soup.find('div', {'class': 'chapter_go'})
            next_chapter = chapter_go.find('a', {'id': 'xiazhang'})
            if next_chapter.text.strip() == '下一章':
                break
            curl = f'{self.website}/{next_chapter.attrs["href"]}'

        x = '\n'.join(txts)
        return f'{title_txt}\n{x}\n\n'

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
            url = f'{self.website}/{next_page_href}'

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
        print(f'总共 {len(chapter_url_list)} 章，从第 {start_chapter} 章开始')
        print('开始缓存')

        with open(file_path, 'a' if is_append else 'w', encoding='utf-8') as f:
            for i, v in enumerate(chapter_url_list[start_chapter - 1:]):

                # 有时候请求会出问题，因此出了问题反复请求几遍
                # 直到超出一定次数仍然出问题则报错
                cnt = 0  # 当前请求次数
                flag = True
                while flag:
                    try:
                        cnt += 1
                        content = self.get_chapter(v)
                        flag = False
                    except Exception as e:
                        if cnt >= 100:  # 请求最大次数
                            raise e
                        flag = True

                f.write(content)
                print(f'第{i + start_chapter}章缓存完毕')
        print('所有章节缓存完毕！')


if __name__ == '__main__':
    from pathlib import Path
    spider = Spider(WEBSITE, URL, ENCODING, PARSER)
    p = str(Path(__file__).resolve().parent / '道诡异仙.txt')
    spider.save_novel(p, False)

    # spider = Spider(WEBSITE, URL, ENCODING, PARSER)
    # x = spider.get_chapter('https://www.waptxt.org/96031/28391910.html')
    # print(x)
