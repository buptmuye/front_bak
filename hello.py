#!/usr/bin/env pyhton
#coding:utf-8
__author__ = "muye"

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url, asynchronous
import tornado.options
from tornado.options import define, options
import os
from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPClient, HTTPError
from datetime import datetime
import re
from apscheduler.schedulers.background import BackgroundScheduler

css_regex = re.compile(r'http://.*\.css')
js_regex = re.compile(r'http://.*\.js')
img_regex = re.compile(r'img\ssrc=.*?\"\s')
settings = dict(
    static_path = os.path.join(os.path.dirname(__file__), "static"),
    template_path = os.path.join(os.path.dirname(__file__), "templates"),
    debug = False,
    autoescape = None,
    gzip = True,
    )

define("port", default=8000, help="run on given port", type=int)

class MainHandler(RequestHandler):
    def get(self):
        content = u"欢迎tornado！"
        self.render("index.html", content=content)


@gen.coroutine
def async_parser_sohu():
    client = AsyncHTTPClient()
    response = yield client.fetch("http://m.sohu.com")    
    body = response.body.replace("href=\"/", "href=\"http://m.sohu.com/")

    cur_time = datetime.now().strftime("%Y%m%d%H%M%S")
    os.makedirs(cur_time + r'/js')
    os.makedirs(cur_time + r'/css')
    os.makedirs(cur_time + r'/img')
    
    css_res = css_regex.findall(body)
    for item in css_res:
        css_name = item[item.rfind('/') + 1:]
        css_response = yield client.fetch(item)
        with open(cur_time + r'/css/' + css_name, 'w') as f:
            f.write(css_response.body)

        body = body.replace(item, r'css/' + css_name)

    js_res = js_regex.findall(body)
    for item in js_res:
        js_name = item[item.rfind('/') + 1:]
        js_response = yield client.fetch(item)
        with open(cur_time + r'/js/' + js_name, 'w') as f:
            f.write(js_response.body)
        body = body.replace(item, r'js/' + js_name)

    img_res = img_regex.findall(body)
    for item in img_res:
        item = item[9:-2]
        img_name = item[item.rfind('/') + 1:]
        img_response = yield client.fetch(item)
        with open(cur_time + r'/img/' + img_name, 'w') as f:
            f.write(img_response.body)
        body = body.replace(item, r'img/' + img_name)

    with open(cur_time + r'/res.html', 'w') as f:
        f.write(body)


def main():
    sched = BackgroundScheduler()
    sched.start()
    sched.add_job(async_parser_sohu, 'interval', seconds=60)

    tornado.options.parse_command_line()
    app = Application([
            url(r"/", MainHandler),
            ], **settings)
    http_server = HTTPServer(app)
    http_server.listen(options.port)
    IOLoop.current().start()


if __name__ == "__main__":
    main()
