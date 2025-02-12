# -*- coding:utf-8 -*-
'''
Filename: /Users/kingtous/PycharmProjects/neuq_car_upper/Auto_Driver_client_v2.py
Path: /Users/kingtous/PycharmProjects/neuq_car_upper
Created Date: Friday, July 17th 2020, 9:24:23 am
Author: Kingtous
Version: v5
Change: add video support
"""
get image from camera:/dev/video2  424*240
deal 128 *128     256*256
get the angle     object_detect
"""
Copyright (c) 2020 Kingtous' 2020
'''

# from user import user_cmd
from datetime import datetime
from collections import namedtuple
from PIL import ImageDraw
from PIL import ImageFont
import os
import v4l2capture
from ctypes import *
import struct
import array
from fcntl import ioctl
import cv2
import numpy as np
import time
from sys import argv
import getopt
import sys
import select
import termios
import tty
import threading
import paddlemobile as pm
from paddlelite import *
import codecs
#import paddle
import multiprocessing
#import paddle.fluid as fluid
#from IPython.display import display
import math
import functools
from PIL import Image
from PIL import ImageFile
import threading
#fr�om central import Central
ImageFile.LOAD_TRUNCATED_IMAGES = True
save_path = 'model_infer'
save_path = 'model_infer'


#script,vels,save_path= argv
# GLOBAL DEFINITION START
save_path = 'model_infer'
# path = os.path.split(os.path.realpath(__file__))[0]+"/.."
path = "/home/root/workspace/deepcar/deeplearning_python/src"+"/.."
opts, args = getopt.getopt(argv[1:], '-hH', ['save_path=', 'vels=', 'camera='])
# img savepath,camera
camera = "/dev/video2"
# car character
vels = 1560
limit_vels = 1525
crop_size = 128
recog_rate = 0.5
curent_speed = 1500
# recog classes
classes = 6
label_dict = {0: "tag"}
DEBUG_MODE = True

def output(s):
    global DEBUG_MODE
    if DEBUG_MODE == True:
        print(s)
# GLOBAL DEFINITION END


for opt_name, opt_value in opts:
    if opt_name in ('-h', '-H'):
        output("python3 Auto_Driver.py --save_path=%s  --vels=%d --camera=%s " %
               (save_path, vels, camera))
        exit()

    if opt_name in ('--save_path'):
        save_path = opt_value

    if opt_name in ('--vels'):
        vels = int(opt_value)

    if opt_name in ('--camera'):
        camera = opt_value




def load_image(cap):

    lower_hsv = np.array([156, 43, 46])
    upper_hsv = np.array([180, 255, 255])
    lower_hsv1 = np.array([0, 43, 46])
    upper_hsv1 = np.array([10, 255, 255])
    ref, frame = cap.read()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask0 = cv2.inRange(hsv, lowerb=lower_hsv, upperb=upper_hsv)
    mask1 = cv2.inRange(hsv, lowerb=lower_hsv1, upperb=upper_hsv1)
    mask = mask0 + mask1
    img = Image.fromarray(mask)
    img = img.resize((128, 128), Image.ANTIALIAS)
    img = np.array(img).astype(np.float32)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img = img.transpose((2, 0, 1))
    img = img[(2, 1, 0), :, :] / 255.0
    img = np.expand_dims(img, axis=0)
    
    return img

frame_count = 0

def dataset(video):
    global frame_count
    lower_hsv = np.array([25, 75, 190])
    upper_hsv = np.array([40, 255, 255])

    select.select((video,), (), ())

    image_data = video.read_and_queue()

    frame = cv2.imdecode(np.frombuffer(
        image_data, dtype=np.uint8), cv2.IMREAD_COLOR)

    '''load  128*128'''

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask0 = cv2.inRange(hsv, lowerb=lower_hsv, upperb=upper_hsv)
    mask = mask0  # + mask1
    img = Image.fromarray(mask)
    img = img.resize((128, 128), Image.ANTIALIAS)
    #img = cv2.resize(img, (128, 128))
    img = np.array(img).astype(np.float32)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img = img / 255.0
    #output("Before func_expand image_shape:",img.shape)
    img = np.expand_dims(img, axis=0)
    #output("vedio image_shape:",img.shape)
    '''object   256*256'''
    img_256 = Image.fromarray(frame)
    frame_count += 1
    return img_256, img, frame

# *************
# car line
# *************

def load_model():

    valid_places = (
        Place(TargetType.kFPGA, PrecisionType.kFP16, DataLayoutType.kNHWC),
        Place(TargetType.kHost, PrecisionType.kFloat),
        Place(TargetType.kARM, PrecisionType.kFloat),
    )
    config = CxxConfig()
    model = save_path
    model_dir = model
    config.set_model_file(model_dir + "/model")
    config.set_param_file(model_dir + "/params")
    #config.model_dir = model_dir
    config.set_valid_places(valid_places)
    nolimit_predictor = CreatePaddlePredictor(config)

    limit_config = CxxConfig()
    limit_config.set_model_file(model_dir + "/model")
    limit_config.set_param_file(model_dir + "/params")
    #config.model_dir = model_dir
    limit_config.set_valid_places(valid_places)

    limit_predictor = CreatePaddlePredictor(limit_config)
    return nolimit_predictor,limit_predictor


def predict(predictor, image, z):
    img = image

    i = predictor.get_input(0)
    i.resize((1, 3, 128, 128))
    #output("predict img.shape:",img.shape)
    #output("predict z.shape:",z.shape)
    z[0, 0:img.shape[1], 0:img.shape[2] + 0, 0:img.shape[3]] = img
    z = z.reshape(1, 3, 128, 128)
    frame1 = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)
    cv2.imwrite("first_frame.jpg", frame1)
    i.set_data(z)

    predictor.run()
    out = predictor.get_output(0)
    score = out.data()[0][0]
    output(out.data()[0])
    return score
#coordinate
send_index=0
# EXPORT
RUNNING = False
reverse_label=False

def reverse_car():
    global reverse_label
    if reverse_label==True:
        if STATUS_PARK == False:
            lib.send_cmd(1500,0)
            lib.send_cmd(0, 1400)
        else:
            lib.send_cmd(2300,0)
            lib.send_cmd(0,1400)
    return []


def send_coordinte():
	#global send_index,coord_x,coord_y
	send_index=send_index+1
	if send_index==1:
		coord_x=0
		coord_y=0
	else:
		if len(bboxes.shape) == 1:
		     output("No object found in video")
		     STATE_value = False
		     last_barrier_x = int(barrier_x)
		     last_barrier_y = int(barrier_y)
		     #lib.send_cmd(last_barrier_x, last_barrier_y)
		     coord_x=last_barrier_x
		     coord_y=last_barrier_y
		else:
		     STATE_value = False
		     labels = bboxes[:, 0].astype('int32')
		     # scores -> angle , true_angle = 500 + 2000*scores
		     scores = bboxes[:, 1].astype('float32')
		     # pixels position
		     boxes = bboxes[:, 2:].astype('float32')
		     boxes = boxes[0:1].tolist()
		     box = boxes[0]
		     x_rate = 320.0 / 608
		     y_rate = 240.0 / 608
		     # global barrier_x
		     # global barrier_y
		     #[0]left_top_x，[1]left_top_y,[2]right_bottom_x,[3]right_bottom_y
		     barrier_x = (box[0] + 1/2 * (box[2] - box[0])) * x_rate - 160
		     barrier_y = 260 - ((box[3] + 1/2 * (box[1] - box[0])) * y_rate )

		     if barrier_y > 0:
		         lib.send_cmd(int(barrier_x), int(barrier_y))
		         coord_x=barrier_x
		         coord_y=barrier_y
#		         print('barrier_x', int(barrier_x))
#		         print('barrier_y', int(barrier_y))
		     else:
		         barrier_y = 0
		         coord_x=barrier_x
		         coord_y=barrier_y
		         #lib.send_cmd(int(barrier_x), int(barrier_y))
#		         print('barrier_x', int(barrier_x))
#		         print('barrier_y', int(barrier_y))
		     
		     last_barrier_x = int(barrier_x)
		     last_barrier_y = int(barrier_y)
	return coord_x,coord_y


# *************
# object detect
# *************

train_parameters = {
    "train_list": "train.txt",
    "eval_list": "eval.txt",
    "class_dim": -1,
    "label_dict": {},
    "num_dict": {},
    "image_count": -1,
    "continue_train": True,
    "pretrained": False,
    "pretrained_model_dir": "./pretrained-model",
    "save_model_dir": "./yolo-model",
    "model_prefix": "yolo-v3",
    "freeze_dir": "/home/root/workspace/deepcar/deeplearning_python/src/freeze_model_0809",
    # "freeze_dir": "../model/tiny-yolov3",
    "use_tiny": True,
    "max_box_num": 20,
    "num_epochs": 80,
    "train_batch_size": 32,
    "use_gpu": False,
    "yolo_cfg": {
        "input_size": [3, 448, 448],
        "anchors": [7, 10, 12, 22, 24, 17, 22, 45, 46, 33, 43, 88, 85, 66, 115, 146, 275, 240],
        "anchor_mask": [[6, 7, 8], [3, 4, 5], [0, 1, 2]]
    },

    "yolo_tiny_cfg": {
        "input_size": [3, 256, 256],
        "anchors": [6, 8, 13, 15, 22, 34, 48, 50, 81, 100, 205, 191],
        "anchor_mask": [[3, 4, 5], [0, 1, 2]]
    },
    "ignore_thresh": 0.7,
    "mean_rgb": [127.5, 127.5, 127.5],
    "mode": "train",
    "multi_data_reader_count": 4,
    "apply_distort": True,
    "nms_top_k": 300,
    "nms_pos_k": 300,
    "valid_thresh": 0.01,
    "nms_thresh": 0.45,

    "image_distort_strategy": {
        "expand_prob": 0.5,
        "expand_max_ratio": 4,
        "hue_prob": 0.5,
        "hue_delta": 18,
        "contrast_prob": 0.5,
        "contrast_delta": 0.5,
        "saturation_prob": 0.5,
        "saturation_delta": 0.5,
        "brightness_prob": 0.5,
        "brightness_delta": 0.125
    },

    "sgd_strategy": {
        "learning_rate": 0.002,
        "lr_epochs": [30, 50, 65],
        "lr_decay": [1, 0.5, 0.25, 0.1]
    },

    "early_stop": {
        "sample_frequency": 50,
        "successive_limit": 3,
        "min_loss": 2.5,
        "min_curr_map": 0.84
    }
}


def init_train_parameters():

    # os.path.join(train_parameters['data_dir'], train_parameters['train_list'])
    file_list = "/home/root/workspace/deepcar/deeplearning_python/src/data/data6045/train.txt"
    # os.path.join(train_parameters['data_dir'], "label_list")
    label_list = "/home/root/workspace/deepcar/deeplearning_python/src/data/data6045/tag_only_list/label_list"
    index = 0
    with codecs.open(label_list, encoding='utf-8') as flist:
        lines = [line.strip() for line in flist]
        for line in lines:
            train_parameters['num_dict'][index] = line.strip()
            train_parameters['label_dict'][line.strip()] = index
            index += 1
        train_parameters['class_dim'] = index
    with codecs.open(file_list, encoding='utf-8') as flist:
        lines = [line.strip() for line in flist]
        train_parameters['image_count'] = len(lines)


def read_image(buffer):
    #lock.acquire()
    # origin: ndarray
    origin = Image.open(buffer)
    #img = resize_img(origin, target_size)
    #decode_img = cv2.imdecode(np.frombuffer(buffer,np.uint8),-1)
    #img = cv2.resize(decode_img,(256,256))
    img = origin.resize((256,256), Image.BILINEAR)   #######resize 256*256
    # print(type(img))
    #lock.release()

    #origin = image
    #img = resize_img(origin, target_size)

    # img = origin.resize((256,256), Image.BILINEAR)   #######resize 256*256

    # added
    #img = cv2.resize(origin, (256,256))

    # if img.mode != 'RGB':
    #     img = img.convert('RGB')
    img = np.array(img).astype('float32').transpose((2, 0, 1))  # HWC to CHW
    #img = np.array(img).astype('float32')
    img -= 127.5
    img *= 0.007843
    img = img[np.newaxis, :]
    return img


def load_model_detect():
    ues_tiny = train_parameters['use_tiny']
    yolo_config = train_parameters['yolo_tiny_cfg'] if ues_tiny else train_parameters['yolo_cfg']
    target_size = yolo_config['input_size']
    anchors = yolo_config['anchors']
    anchor_mask = yolo_config['anchor_mask']
    label_dict = train_parameters['num_dict']
    #output("label_dict:", label_dict)
    class_dim = train_parameters['class_dim']
    # output("class_dim:",class_dim)

    path1 = train_parameters['freeze_dir']
    model_dir = path1
    pm_config1 = pm.PaddleMobileConfig()
    pm_config1.precision = pm.PaddleMobileConfig.Precision.FP32  # ok
    pm_config1.device = pm.PaddleMobileConfig.Device.kFPGA  # ok
    #pm_config.prog_file = model_dir + '/model'
    #pm_config.param_file = model_dir + '/params'
    pm_config1.model_dir = model_dir
    pm_config1.thread_num = 4
    predictor1 = pm.CreatePaddlePredictor(pm_config1)
    # Cxx
    # valid_places =   (
    # 	Place(TargetType.kFPGA, PrecisionType.kFP16, DataLayoutType.kNHWC),
    # 	Place(TargetType.kFPGA, PrecisionType.kInt8),
    # 	Place(TargetType.kFPGA, PrecisionType.kInt16),
    # );
    # model_dir = "/home/root/workspace/deepcar/deeplearning_python/model/detect_model_infer"
    # config = CxxConfig();
    # config.set_model_file(model_dir+"/model");
    # config.set_param_file(model_dir+"/params");
    # #config.model_dir = model_dir
    # config.set_valid_places(valid_places);
    # predictor = CreatePaddlePredictor(config);

    return predictor1

# process frame adding labels,scores,boxes
# return frame


def process_frame(img, labels, scores, boxes, need_raw=True):
    # need_raw -> True, output raw video, no prediction text and rectangle
    x_rate = 320.0 / 608
    y_rate = 240.0 / 608
    #boxes = boxes[:,2:].astype('float32')
    d = img
    if not need_raw:
        output(boxes)
        for label, box, score in zip(labels, boxes, scores):
            # output("label:",label_dict[int(label)])
            if score < recog_rate:
                continue
            xmin, ymin, xmax, ymax = box[0], box[1], box[2], box[3]
            d = cv2.rectangle(img, (int(box[0]*x_rate), int(box[1]*y_rate)),
                            (int(box[2]*x_rate), int(box[3]*y_rate)), (255, 0, 0), 1)
            d = cv2.putText(img, label_dict[int(label)]+":"+str(score), (int(
                box[0]*x_rate), int(box[3]*y_rate)), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 1)
    return d


# queue thread
def queueThread(lib,pipe):
    global curent_speed
    while 1:
        p1,p2,t = pipe.recv()
        time.sleep(t)
        #lib.send_cmd(p1,p2)
        if (p1 == 0):
            curent_speed = p2
        print("sent ",p1,p2,"delay time:",t,"s")

def isRunning():
    return RUNNING
    
#if __name__ == "__main__":
def start(coord_x,coord_y,XY_TIMESTAMP):
    RUNNING = True
    cout = 0
    global save_path
    save_path = path + "/model/" + save_path
    # 视频
    video = v4l2capture.Video_device(camera)
    video.set_format(320, 240, fourcc='MJPG')
    video.create_buffers(1)
    video.queue_all_buffers()
    video.start()
    carline_predictor,carline_limited_predictor = load_model()

    '''##########################################################object  detect##########################################################'''
    init_train_parameters()
    detect_predictor = load_model_detect()

    vel = int(vels)
    lib_path = path + "/lib" + "/libart_driver.so"
    so = cdll.LoadLibrary
    lib = so(lib_path)
    
    car = "/dev/ttyUSB0"
    z = np.zeros((1, 128, 128, 3))
    if (lib.art_racecar_init(38400, car.encode("utf-8")) < 0):
        raise
        pass
    #central = Central(lib,vels)
    # most possible status
    # VIDEO
    out = cv2.VideoWriter(
        'save.avi', cv2.VideoWriter_fourcc(*'MJPG'), 20, (320, 240))

    # cv2.VideoWriter
    # labels in no_limit(0),limit(1),park(2),red(3),green(4),zebra(5),block(6)
    # DEFINITION END
    NO_LIMIT = 0
    LIMIT = 1
    PARK = 2
    RED = 3
    GREEN = 4
    ZEBRA = 5
    STAIGHT = 6
    BARRIER = 7
    STRAIGHT = 8
    # DEFINITION
    try:
        while 1:
            count = 0
            yuzhi_0 = 0
            yuzhi_3 = 0
            yuzhi_4 = 0
            # SIGN DEFINITION START
            # judge zebra line
            zebra_line_detected = False
            # reset ZEBRA and RED and GREEN
            STATUS_LIMIT = False
            STATUS_PARK = False
            z = np.zeros((1, 128, 128, 3))
            while 1:
                t1 = time.time()
                ZEBRA_SIGN = False
                RED_SIGN = False
                GREEN_SIGN = False
                LIMIT_SIGN = False
                NO_LIMIT_SIGN = False
                BARRIER_SIGN = False
                nowtime = time.time()
                origin, img, frame = dataset(video)
                # STEP 1: ANGLE
                angle = 1500
                if not STATUS_LIMIT:
                    print("no limit predictor analyzing..")
                    angle = predict(carline_predictor, img, z)
                else:
                    print("limit predictor analyzing..")
                    angle = predict(carline_limited_predictor, img, z)
                # DISABLE DETECTION
                # output("angle:",angle)
                # lib.send_cmd
                # )
                # continue
                # tensor_img,img= read_image()  #  resize image
                # tensor_img = origin.resize((256,256), Image.BILINEAR)   #######resize 256*256
                # tensor_img.mode = 'BGR'
                # if tensor_img.mode != 'RGB':
                #     #    tensor_img = cv2.cvtColor(Image.fromarray(tensor_img),cv2.COLOR_RGB2BGR)
                #     tensor_img = tensor_img.convert('RGB')
                #     #    print(type(tensor_img))
                # print("mode:",tensor_img.mode)
                # tensor_img = np.array(tensor_img).astype('float32')#.transpose((2, 0, 1))  # HWC to CHW
                # tensor_img -= 127.5
                # tensor_img *= 0.007843
                # show_img = tensor_img
                #tensor_img = tensor_img[np.newaxis, :]

                # print(type(tensor_img))
                # print(tensor_img.shape)
                #tensor_img = tensor_img.convert('RGB')
                #tensor_img = cv2.cvtColor(np.asarray(tensor_img),cv2.COLOR_BGR2RGBA)

                #tensor_img = cv2.cvtColor(tensor_img,cv2.COLOR_RGB2BGR)
                # cv2.namedWindow("boot", cv2.WINDOW_AUTOSIZE)
                # cv2.imshow('FRAME',show_img)
                # cv2.waitKey(0)
                # cv2.destroyAllWindows("FRAME")

                # exit(0)

                '''
                print("frame_info:")
                print(type(frame))
                print(frame.shape)
                print(frame)
                '''
                #is_success, buffer = cv2.imencode(".jpg", frame)
                cv2.imwrite("carline.jpg",frame)

                '''
                carline = cv2.imread("carline.jpg")
                #np.savetxt('carline',carline)
                '''

                '''
                print("carline.jpg_info:",carline)
                print(type(carline))
                print(carline.shape)
                '''
                img = read_image("carline.jpg")

                '''
                print("img_info:")
                print(type(img))
                print(img.shape)
                print(img)
                #np.savetxt('img',img)
                exit(0)
                '''

                '''
                frame1 = frame.transpose((2, 0, 1))
                print("frame1_info:")
                print(type(frame1))
                print(frame1.shape)

                frame2 = np.expand_dims(frame1, axis=0)
                print("frame2_info:")
                print(type(frame2))
                print(frame2.shape)

                frame3 = cv2.resize(frame2,(256,256))

                #print("before",frame)
                # print(type(frame))
                # print(frame.shape)

                img = read_image(frame3)
                #print("after",img)
                print(type(img))
                print(img.shape)
                '''

                # added
                '''
                frame_info:
                <class 'numpy.ndarray'>
                (240, 320, 3)

                carline.jpg_info:
                <class 'numpy.ndarray'>
                (240, 320, 3)

                img_info:
                <class 'numpy.ndarray'>
                (1, 3, 256, 256)
                '''

                # print("shape", tensor_img.shape)
                # print("origin",tensor_img)
                # print("after",tensor_img)
                tensor = pm.PaddleTensor()
                tensor.dtype = pm.PaddleDType.FLOAT32
                tensor.shape = (1, 3, 256, 256)
                tensor.data = pm.PaddleBuf(img)
                paddle_data_feeds1 = [tensor]
                count += 1
                outputs1 = detect_predictor.Run(paddle_data_feeds1)
                #output("outputs1 value:", str(outputs1))

                # assert len(
                #     outputs1) == 1, 'error numbers of tensor returned from Predictor.Run function !!!'
                bboxes = np.array(outputs1[0], copy=False)
                # output("bboxes.shape",bboxes.shape)

                t_labels = []
                t_scores = []
                t_boxes = []
                center_x = []
                center_y = []

                barrier_x = 0
                barrier_y = 0

                # starting judge labels
                final_label = NO_LIMIT
                if STATUS_LIMIT == True:
                    final_label = LIMIT
                final_score = 0.0
                if len(bboxes.shape) == 1:
                    output("No object found in video")
                    STATE_value = False
                    last_barrier_x = int(barrier_x)
                    last_barrier_y = int(barrier_y)
                    coord_x.value=last_barrier_x
                    coord_y.value=last_barrier_y
                    lib.send_cmd(last_barrier_x, last_barrier_y)
                    
                else:
                    STATE_value = False
                    labels = bboxes[:, 0].astype('int32')
                    # scores -> angle , true_angle = 500 + 2000*scores
                    scores = bboxes[:, 1].astype('float32')
                    # pixels position
                    boxes = bboxes[:, 2:].astype('float32')
                    print("labels:",str(labels))
                    print("scores:",str(scores))
                    print("boxes:", str(boxes))
                    print(str(boxes[0:1]))
                    boxes = boxes[0:1].tolist()
                    box = boxes[0]
                    print(box)
                    x_rate = 320.0 / 608
                    y_rate = 240.0 / 608
                    # global barrier_x
                    # global barrier_y
                    print("boxes", boxes)
                    #[0]left_top_x，[1]left_top_y,[2]right_bottom_x,[3]right_bottom_y
                    barrier_x = (box[0] + 1/2 * (box[2] - box[0])) * x_rate - 160
                    barrier_y = 260 - ((box[3] + 1/2 * (box[1] - box[0])) * y_rate )
                    
                    
                    if barrier_y > 0:
                        lib.send_cmd(int(barrier_x), int(barrier_y))
                        coord_x.value=barrier_x
                        coord_y.value=barrier_y
                        print('barrier_x', int(barrier_x))
                        print('barrier_y', int(barrier_y))
                    else:
                        barrier_y = 0
                        lib.send_cmd(int(barrier_x), int(barrier_y))
                        coord_x.value=barrier_x
                        coord_y.value=barrier_y
                        print('barrier_x', int(barrier_x))
                        print('barrier_y', int(barrier_y))
                    
                    last_barrier_x = int(barrier_x)
                    last_barrier_y = int(barrier_y)
                    XY_TIMESTAMP.value=int(time.time() * 1000)
                    print(XY_TIMESTAMP)
                    with open('data111111.txt', 'a') as file:
                        
                        file.write(str(int(barrier_x)))
                        file.write('\t')   
                        file.write(str(int(barrier_y)))
                        file.close()
                         # file.write(str(barrier_x))
                       # file.write(str(barrier_y))
                       # file.write("\n")
                    frame = process_frame(frame, labels, scores, boxes, need_raw=False)
                    # start algorithm
                    # <- final_label

                    STATE_value = True
                    
                    
                ################################################################################################
                # preprocessing data (data、sign)
                # TODO BLOCK Judgement
                # TODO
                # calculate true angle
                # TODO 角度突变

                true_angle = 0.5
                try:
                    true_angle = int(angle * 1600 + 700)
                except ValueError as e:
                    true_angle = 1500
                    #print(str(e))
                # Judge SIGN
                if RED_SIGN == True:  # and ZEBRA_SIGN == True:
                    # cv2.imwrite("red.jpg",tensor_img)
                    # V2: only recognize both SIGNs
                    final_label = PARK
                    STATUS_PARK = True
                if GREEN_SIGN == True and STATUS_PARK == True:
                    # cv2.imwrite("green.jpg",tensor_img)
                    if STATUS_LIMIT:
                        final_label = LIMIT
                    else:
                        final_label = NO_LIMIT
                    STATUS_PARK = False
                if LIMIT_SIGN == True:
                    final_label = LIMIT
                    STATUS_PARK = False
                if NO_LIMIT_SIGN == True and STATUS_LIMIT == True:
                    final_label = NO_LIMIT
                    STATUS_PARK = False

                # start sending proccessed command
                #output("sending: angle: %d, label: %d" % (true_angle, final_label))
                # user_cmd(STATE_value,t_labels,t_scores,center_x,center_y,vel,a)
                delay_time = 0
                if STATUS_PARK == True:
                    final_label = PARK
                # if STATUS_LIMIT == True :
                #     final_label = LIMIT
                #     lib.send_cmd(0,limit_vels)
                #     print("sent speed:",limit_vels)

                if BARRIER_SIGN == True and STATUS_PARK != False:
                    final_label = BARRIER

                # final sent process
                if final_label == LIMIT and LIMIT_SIGN == True and STATUS_LIMIT == False:
                    STATUS_LIMIT = True
                    # delay_p1.send((0,limit_vels,0))
                    # delay_p1.send((true_angle,final_label,0))
                    curent_speed = limit_vels
                    delay_time = 2.5

                if final_label == NO_LIMIT and NO_LIMIT_SIGN == True and STATUS_LIMIT == True:
                    STATUS_LIMIT = False
                    # delay_p1.send((0,vels,0))
                    # delay_p1.send((true_angle,final_label,0))
                    curent_speed = vels
                    delay_time = 1

                if STATUS_PARK == True and final_label == LIMIT:
                    final_label = PARK

                if final_label == NO_LIMIT and STATUS_LIMIT == True:
                    final_label = LIMIT
                    delay_time = 2.5
                
                if final_label == STRAIGHT:
                    if STATUS_LIMIT == True:
                        final_label = LIMIT
                    else:
                        final_label = NO_LIMIT


                
                #central.request(true_angle,int(final_label),delay_time)
                #print("is parking?",STATUS_PARK)
                #print("is limit?",STATUS_LIMIT)
                #print("label:",final_label)
                #print("delay:",delay_time)
                
                t2 = time.time()
                cout = cout + 1

                # output VIDEO
                
                				  #cv2.putText(frame,"line pt: " + "lp" if STATUS_LIMIT else "p",(0,180),cv2.FONT_HERSHEY_PLAIN,1.5, (0, 255, 0), 1)
                cv2.putText(frame,str(true_angle) + ":" + str(final_label),(0,200),cv2.FONT_HERSHEY_PLAIN,1.5, (0, 255, 0), 1)
                #cv2.putText(frame,"is limit?:" + str(STATUS_LIMIT),(0,220),cv2.FONT_HERSHEY_PLAIN,1.5, (0, 255, 0), 1)
                #cv2.putText(frame,"sp:" + str(curent_speed),(0,160),cv2.FONT_HERSHEY_PLAIN,1.5, (0, 255, 0), 1)
                #cv2.putText(frame,"t:" + str(t2-t1),(0,140),cv2.FONT_HERSHEY_PLAIN,1.5, (0, 255, 0), 1)
                #cv2.putText(frame,"frame:" + str(frame_count),(0,20),cv2.FONT_HERSHEY_PLAIN,1.5, (0, 255, 0), 1)
                #cv2.putText(frame,"delay:" + str(delay_time),(0,40),cv2.FONT_HERSHEY_PLAIN,1.5, (0, 255, 0), 1)
                cv2.putText(frame,"barrier_x:" + str(int(coord_x.value)),(0, 20),cv2.FONT_HERSHEY_PLAIN,1.5, (0, 255, 0), 1)
                cv2.putText(frame,"barrier_y:" + str(int(coord_y.value)),(0, 40),cv2.FONT_HERSHEY_PLAIN,1.5, (0, 255, 0), 1)
                # VIDEO Write
                out.write(frame)
                # if final_label == 2:
                #    input("stop")
                # if final_label == 1:
                #    input("limit")
                # output(cout)
                
                #output("the time of predict:",time.time()-nowtime)
                
                # print("convert time:", t2-t1)
    except KeyboardInterrupt as e:
        output("keyboard detected")
        #VIDEO
        out.release()
        
        # stop car
        #lib.send_cmd(1500, 2)
        exit(0)
    finally:
        output('exit')
if __name__ == "__main__":
	start()