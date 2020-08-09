import tornado
import tornado.web
from tornado import gen
from tornado.httpserver import HTTPServer
import os
from serial import Serial
import tools.raw_conn as rc

class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html",y_data=[0],control_data=[1515,4,3,1])
    
    def post(self):
        args = self.request.body_arguments
        x_args = [
            int(float(args['p1'][0].decode("utf-8"))),
            round(float(args['p2'][0].decode("utf-8")),3),
            round(float(args['p3'][0].decode("utf-8")),3),
            round(float(args['p4'][0].decode("utf-8")),3),
        ]
        data = rc.send(x_args)
        #print(data)
        if type(data) == str:
            self.write(data)
        else:
            self.render("index.html",y_data=data,control_data=x_args)

class RevertDirectionHandler(tornado.web.RequestHandler):
    def get(self):
        rc.revertDirection()
        self.write("ok")


settings = {'debug': True}

if __name__ == "__main__":
    
    app = tornado.web.Application([
        (r"/",IndexHandler),
        (r"/revert",RevertDirectionHandler)
    ],
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    template_path=os.path.join(os.path.dirname(__file__), "templates"), **settings )
    server = HTTPServer(app)
    server.listen(8888)
    tornado.ioloop.IOLoop.current().start()
