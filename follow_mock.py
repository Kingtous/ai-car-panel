RUNNING = False
PID = None

coord_x = 0
coord_y = 1
# x,y在timestamp时生成
XY_TIMESTAMP = 0

def isRunning():
    return RUNNING

def exit():
    print("exited")
    return True

def reverse_car():
    return []

# 启动人车跟随
def start(p1,p2,p3):
    RUNNING = True
    while True:
        pass