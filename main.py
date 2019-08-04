import sys, pygame, math,time,numpy
from multiprocessing import Process, Lock
from hashlib import sha1
import xml.etree.ElementTree as ET
pygame.init()
pygame.font.init()

def cthread(func,args):
    t = Process(target = func, args = args)
    t.start()

def calculate_circle_points(x, y, r):
    points = []
    for i in range(-r, r + 1):
        s = math.sqrt(abs((x + i)**2 - r**2))
        points.append([x + i, s])
        if s != 0:
            points.append([x + i, -s])
    return points

#drawing
def draw_point(point):
    try:
        screen.blit(hash, (round(point[0] + width / 2), round(point[1] + height / 2)))
    except TypeError:
        pass





def calculate_2d_point(point, camera = [0,0,0], f = 1000): #The holy grail lmao
    try:
        if point[2] - camera[2] >= 0:
            x = ((point[0] - camera[0]) * (f / (point[2] - camera[2]))) + camera[0]
            y = ((point[1] - camera[1]) * (f / (point[2] - camera[2]))) + camera[1]
        else:
            x = -1
            y = -1
    except ZeroDivisionError: #TODO: fix this lmao
        x = -1
        y = -1
    return x, y

def compute_rotate(r,p,y):

    cosa = math.cos(y)
    sina = math.sin(y)
    
    cosb = math.cos(p)
    sinb = math.sin(p)
    
    cosc = math.cos(r)
    sinc = math.sin(r)
    
    Axx = cosa*cosb
    Axy = cosa*sinb*sinc - sina*cosc
    Axz = cosa*sinb*cosc + sina*sinc
    
    Ayx = sina*cosb
    Ayy = sina*sinb*sinc + cosa*cosc
    Ayz = sina*sinb*cosc - cosa*sinc
    
    Azx = -sinb
    Azy = cosb*sinc
    Azz = cosb*cosc
    
    return (Axx, Axy, Axz, Ayx, Ayy, Ayz, Azx, Azy, Azz)
    
    
def rotate_point(point,origin, r_vars):
    Axx, Axy, Axz, Ayx, Ayy, Ayz, Azx, Azy, Azz = r_vars
    res = []

    px = point[0]
    py = point[1]
    pz = point[2]
    
    #transform to origin
    
    px -= origin[0]
    py -= origin[1]
    pz -= origin[2]
    
    #rotate
    res = [Axx*px + Axy*py + Axz*pz,Ayx*px + Ayy*py + Ayz*pz,Azx*px + Azy*py + Azz*pz]
    
    #transform back
    
    res[0] += origin[0]
    res[1] += origin[1]
    res[2] += origin[2]
    
    return res
def full_process_point(point, rorigin,r_vars,c_vars): #Compute rotate first!
    global camera
    point = rotate_point(point,rorigin,r_vars)
    point = rotate_point(point,camera,c_vars)
    point = calculate_2d_point(point, camera)
    return point
    #draw_point(point)
    
    

def calculate_cube(x, y, z, x1, y1, z1, pitch, roll, yaw):
    it_x = x1 - x
    it_y = y1 - y
    it_z = z1 - z
  
    mid_x = (x1 + x) / 2
    mid_y = (y1 + y) / 2
    mid_z = (z1 + z) / 2
    
    mid = [mid_x, mid_y, mid_z]
    
    r_vars = compute_rotate(pitch, roll, yaw) #Prepare rotation
    
    c_vars = compute_rotate(camera_facing[1] * math.pi/180,camera_facing[0] * math.pi/180,0) #Prepare camera rotation
    
    points = []
    
    for ix in range(x, x1+1):
        for iz in range(z, z1+1):
            points.append([ix,y,iz])
            points.append([ix,y1,iz])
    for iz in range(z, z1+1):
        for iy in range(y, y1+1):
            points.append([x,iy,iz])
            points.append([x1,iy,iz])
    for ix in range(x, x1+1):
        for iy in range(y, y1+1):
            points.append([ix,iy,z])
            points.append([ix,iy,z1])
    for i in range(len(points)):
        points[i] = full_process_point(points[i],mid,r_vars,c_vars)
    return points

def calculate_sphere(x, y, z, r, pitch, roll, yaw):
    #TODO: Improve algo
    #Algo right now ->
    #   Calculate circles sequetially
    
    r_vars = compute_rotate(pitch, roll, yaw) #Prepare rotation
    c_vars = compute_rotate(camera_facing[1] * math.pi/180,camera_facing[0] * math.pi/180,0) #Prepare camera rotation
    
    points = []
    for ir in range(-r,r+1):
        p = calculate_circle_points(0, 0, round(math.sqrt(r**2 - ir**2)))
        for point in p:
            points.append([point[0]+x, point[1]+y, z + ir])
            points.append([point[0]+x, y+ir, z + point[1]])
    for i in range(len(points)):
        points[i] = full_process_point(points[i],[x,y,z],r_vars,c_vars)
   
    return points
def calculate_pyramid():
    pass
    
    
    
    
def read_map_xml(filename): # {id:[objecttype,calculatedhash,[params],points,isanimated,anim]}
    result = {}
    file = open(filename,'r')
    data = file.read()
    file.close()
    root = ET.fromstring(data)
    for child1 in root:
        if child1.tag == 'objects':
            for child2 in child1:
                if child2.tag == 'cube':
                    params = {}
                    object_variables[child2.attrib['id']] = {}
                    for attrib in child2:
                        if attrib.attrib['type'] == 'eval':
                            params[attrib.tag] = eval(attrib.text)
                        elif attrib.attrib['type'] == 'str':
                            params[attrib.tag] = attrib.text
                        else:
                            params[attrib.tag] = eval('{}({})'.format(attrib.attrib['type'],attrib.text))
                    if 'animate' in params:
                        isanimated = True
                        id = child2.attrib['id']
                        anim = params['animate']
                        exec(params['animate_init'])
                    else:
                        isanimated = False
                        anim = ''
                    funcparams = [params['x'],params['y'],params['z'],params['x1'],params['y1'],params['z1'],params['pitch'],params['roll'],params['yaw']]
                    result[child2.attrib['id']] = ['cube',None,funcparams,[],isanimated,anim]
                
                if child2.tag == 'sphere':
                    params = {}
                    object_variables[child2.attrib['id']] = {}
                    for attrib in child2:
                        if attrib.attrib['type'] == 'eval':
                            params[attrib.tag] = eval(attrib.text)
                        elif attrib.attrib['type'] == 'str':
                            params[attrib.tag] = attrib.text
                        else:
                            params[attrib.tag] = eval('{}({})'.format(attrib.attrib['type'],attrib.text))
                    if 'animate' in params:
                        isanimated = True
                        id = child2.attrib['id']
                        anim = params['animate']
                        exec(params['animate_init'])
                    else:
                        isanimated = False
                        anim = ''
                    funcparams = [params['x'],params['y'],params['z'],params['r'],params['pitch'],params['roll'],params['yaw']]
                    result[child2.attrib['id']] = ['sphere',None,funcparams,[],isanimated,anim]
    
    return result
def get_calculate_hash():
    global camera, camera_facing
    res = ''
    for x in camera:
        res += str(x)
    for x in camera_facing:
        res += str(x)
    return sha1(res.encode('utf-8')).hexdigest()
def process_all_points(data):
    for point in data:
        draw_point(point)

    
if __name__=='__main__':
    black = 0, 0, 0
    size = width, height = 1000,700

    screen = pygame.display.set_mode(size)

    hash = pygame.image.load("#.png")
    menu_img = pygame.image.load("menu.png")
    clock = pygame.time.Clock()
    camera = [0,0,0]
    camera_facing = [0, 0] #lr ud
    r = 0
    myfont = pygame.font.SysFont('Lucida', 20)

    posa = [0,0,0,30,30,0]
    object_variables = {}

    objects = read_map_xml('map.xml')
    c = 90
    menu = False
    settings = {'updown':False}

    while True:
        dt = clock.tick(100)
        
        print('x: {} y: {} z: {} alpha: {}'.format(round(camera[0]),round(camera[1]),round(camera[2]),round(camera_facing[0])),end = '                           \r')
        textsurface = myfont.render('FPS: ' + str(round(clock.get_fps(),1)), False, (255, 0, 0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: menu = not menu
        
        keys=pygame.key.get_pressed()
        if keys[pygame.K_w]:
            camera[2] += 2 * math.sin((camera_facing[0] + c) * math.pi/180) * dt / 50
            camera[0] += 2 * math.cos((camera_facing[0] + c) * math.pi/180) * dt / 50
        if keys[pygame.K_a]:
            camera[2] -= 2 * math.sin((camera_facing[0]) * math.pi/180) * dt / 50
            camera[0] -= 2 * math.cos((camera_facing[0]) * math.pi/180) * dt / 50
        if keys[pygame.K_s]:
            camera[2] -= 2 * math.sin((camera_facing[0] + c) * math.pi/180) * dt / 50
            camera[0] -= 2 * math.cos((camera_facing[0] + c) * math.pi/180) * dt / 50
        if keys[pygame.K_d]:
            camera[2] += 2 * math.sin((camera_facing[0]) * math.pi/180) * dt / 50
            camera[0] += 2 * math.cos((camera_facing[0]) * math.pi/180) * dt / 50
        if keys[pygame.K_LSHIFT]:
            camera[1] += 2 * dt / 50
        if keys[pygame.K_SPACE]:
            camera[1] -= 2 * dt / 50
        if settings['updown']:
            if keys[pygame.K_UP]:
                camera_facing[1] += 2 * dt / 50
            if keys[pygame.K_DOWN]:
                camera_facing[1] -= 2 * dt / 50
        if keys[pygame.K_LEFT]:
            camera_facing[0] += 2 * dt / 50
        if keys[pygame.K_RIGHT]:
            camera_facing[0] -= 2 * dt / 50
        
        
        screen.fill(black)
        if not menu:
            for id in objects.keys():
                if objects[id][0] == 'cube':
                    if objects[id][1] != get_calculate_hash() or objects[id][4]:
                        objects[id][1] = get_calculate_hash()
                        if objects[id][4]:
                            exec(objects[id][5])
                        objects[id][3] = calculate_cube(objects[id][2][0],objects[id][2][1],objects[id][2][2],objects[id][2][3],objects[id][2][4],objects[id][2][5],objects[id][2][6],objects[id][2][7],objects[id][2][8])
                    process_all_points(objects[id][3])
                if objects[id][0] == 'sphere':
                    if objects[id][1] != get_calculate_hash() or objects[id][4]:
                        objects[id][1] = get_calculate_hash()
                        if objects[id][4]:
                            exec(objects[id][5])
                        objects[id][3] = calculate_sphere(objects[id][2][0],objects[id][2][1],objects[id][2][2],objects[id][2][3],objects[id][2][4],objects[id][2][5],objects[id][2][6])
                    process_all_points(objects[id][3])
        else:
            udoption = myfont.render('Updown camera rotation', False, (0, 255, 0))
            screen.blit(menu_img,(0,0))
            screen.blit(udoption,(10,10))
            b1,b2,b3 = pygame.mouse.get_pressed()
            if b1 == 1:
                if pygame.Rect(2,2,198,58).collidepoint(pygame.mouse.get_pos()):
                    settings['updown'] = not settings['updown']
                    camera_facing[1] = 0
                    menu = False
        screen.blit(textsurface,(0,0))
        pygame.display.flip()


