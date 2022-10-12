import requests
import lxml.html as parser


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"


class ForumScraper:
    def __init__(self, url, cookie):
        self.payload = {}
        self.url = url
        self.ses = requests.Session()
        self.ses.headers.update({"user-agent": USER_AGENT})
        self.ses.cookies.update({"xf_user": cookie})
        self.get_authorization(url)

    def reply(self,  user, img):
        url = f"{self.url}/add-reply"
        self.payload["message"] = f"@{user} [IMG]{img}[/IMG]"
        self.ses.post(url, data=self.payload)
        
    def get_authorization(self, url):
        url_x = self.ses.get(url)
        html = parser.fromstring(url_x.content)
        csrf_token = html.find('.//input[@name="_xfToken"]').value
        self.payload['_xfToken'] = csrf_token
                
    def parse_replies(self, html):
        text_selector = "./div/div[2]/div/div[1]/div/article/div[1]"
        pl = []
        html = parser.fromstring(html.content)
        csrf_token = html.find('.//input[@name="_xfToken"]').value
        self.payload['_xfToken'] = csrf_token
        posts = html.find_class("js-post js-inlineModContainer")
        for i in posts:
            pl.append({
                "id": i.attrib["data-content"],
                "author": i.attrib["data-author"],
                "phrase": i.xpath(text_selector)[0].text_content().replace("\n", " ") if i.xpath(text_selector) else ""
        })
        return pl, len(posts)

    def get_replies(self, url, page=None):
        if page is None:
            pg = "/page-9999"
        elif page == "":
            pg = "/"
        else:
            pg = f"/page-{page}"
        return self.ses.get(f"{url}{pg}")

    def get_user_prompts(self, url):
        result = []
        # generate some error to get a json with unread alerts
        unread = int(
            self.ses.get(
                "https://www.ignboards.com/?_xfResponseType=json"
            ).json()["visitor"]["alerts_unread"]
        )
        # unread = 27
        if not unread:
            return []
        # get the last page (two requests are made here, 303 redirect)
        search = self.get_replies(url)
        # get the redirected url with total number of thread pages
        location = search.history[0].headers["Location"].split("/page-")
        pages = int(location[1]) if len(location) > 1 else 1
        replies, posts = self.parse_replies(search)
        if unread > posts:
            print("get prev page")
            prev_html = self.get_replies(url, pages - 1)
            previous, _ = self.parse_replies(prev_html)
            replies = previous + replies
        self.ses.get("https://www.ignboards.com/account/alerts")
        for r in replies[-unread:]:
            if any([x in r["phrase"] for x in ["imagine/", "Imagine/"]]):
                r["phrase"] = r["phrase"].replace("imagine/", "").replace("Imagine/", "").strip()
                result.append(r)
        return result
