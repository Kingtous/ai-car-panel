import tornado
import tornado.web
import tornado.websocket
from tornado import gen
from tornado.httpserver import HTTPServer
import os
from serial import Serial
### TRUE SERVER
import tools.raw_conn as rc
import follow
# MOCK SERVER
# import follow_mock as follow
# import tools.raw_conn_mock as rc
###
import random
import json
import multiprocessing as mp

##### 网页Handler
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

class Mode2Handler(tornado.web.RequestHandler):

    def get(self):
        self.render("mode2.html",y_data=[0],control_data=[150,150,4,3,1],status=False,msg="")
    
    def post(self):
        args = self.request.body_arguments
        x_args = [
            int(float(args['p0'][0].decode("utf-8"))),
            int(float(args['p1'][0].decode("utf-8"))),
            round(float(args['p2'][0].decode("utf-8")),3),
            round(float(args['p3'][0].decode("utf-8")),3),
            round(float(args['p4'][0].decode("utf-8")),3),
        ]
        data = rc.send_mode2(x_args)
        #print(data)
        if type(data) == str:
            self.write(data)
        else:
            self.render("mode2.html",y_data=data,control_data=x_args,status=True,msg="Complete!")

# 人车跟随
class FollowHandler(tornado.web.RequestHandler):

    # TODO: PID面板

    def get(self):
        # control_data
        self.render("follow.html",y_xdata=[0],y_ydata=[0],x_data=[0],control_data=[4,3,1],isRunning=FollowDataHandler.PID is not None)

    def post(self):
        if type(self.request.body) == bytes:
            self.request.body = self.request.body.decode("utf-8")
        args = self.request.body
        args = json.loads(args)
        x_args = [
            round(float(args['p0'][0]),3),
            round(float(args['p1'][0]),3),
            round(float(args['p2'][0]),3),
        ]
        data = rc.send_pid_follow(x_args)
        #print(data)
        if type(data) == str:
            self.write(json.dumps({"msg":data}))
        else:
            self.write(json.dumps({"msg":"ok"}))
            # print("ok")

class ReverseCarHandler(tornado.web.RequestHandler):

    def post(self):
        if type(self.request.body) == bytes:
            self.request.body = self.request.body.decode("utf-8")
        args = self.request.body
        args = json.loads(args)
        result = follow.reverse_car()
        if type(result) == str:
            self.write(json.dumps({"msg":result}))
        else:
            self.write(json.dumps({"msg":"ok"}))

############### WEB SOCKET
# 人车跟随
class FollowDataHandler(tornado.websocket.WebSocketHandler):

    clients = set()
    num = 1
    # coord_x=0
    # coord_y=0
    # RUNNING = False
    PID = None
    # multiprocessing
    coord_x = mp.Value("f",0)
    coord_y = mp.Value("f",0)
    XY_TIMESTAMP = mp.Value("f",0)

    def open(self):
        # 打开进程
        self.clients.add(self)
        pass

    # 客户端发来数据
    def on_message(self,message):
        if self.PID == None:
            # start multiprocessing
            self.PID = mp.Process(target=follow.start,args=(self.coord_x,self.coord_y,self.XY_TIMESTAMP,))
            self.PID.start()
        try:
            if message == "q":
                for client in self.clients:
                    client.write_message(json.dumps(
                        {"time":self.XY_TIMESTAMP.value,"x":self.coord_x.value,"y":self.coord_y.value}
                        ))
                # self.num = (self.num + 1) % 4
            elif message == "exit":
                if self.PID is not None:
                    self.PID.terminate()
                    self.PID = None
                    print("exit")
        except Exception as e:
            print(e)
    
    def on_close(self):
        try:
            self.clients.remove(self)
        except Exception as e:
            print(e)

    def check_origin(self,origin):
        return True


class RevertDirectionHandler(tornado.web.RequestHandler):
    def get(self):
        rc.revertDirection()
        self.write("ok")


settings = {'debug': True}

if __name__ == "__main__":
    
    app = tornado.web.Application([
        (r"/",IndexHandler),
        (r"/revert",RevertDirectionHandler),
        (r"/mode2",Mode2Handler),
        (r"/follow",FollowHandler),
        (r"/rt/follow_data",FollowDataHandler),
        (r"/reverse",ReverseCarHandler)
    ],
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    template_path=os.path.join(os.path.dirname(__file__), "templates"), **settings )
    server = HTTPServer(app)
    server.listen(8888)
    tornado.ioloop.IOLoop.current().start()
