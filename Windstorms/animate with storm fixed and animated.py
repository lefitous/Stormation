import pandas as pd
import matplotlib.pyplot as plt
import PIL
PIL.Image.MAX_IMAGE_PIXELS = None
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.animation as animation
import matplotlib.font_manager as fm
import time
import cv2
from scipy.interpolate import interp1d, make_interp_spline

def get_data_points(raw):
    """
    this function is used to get the raw data as a panda dataframe input and format it the way we want.
    It will then create an entire list with all the points the storm needs to be at, in which order with which intensity

    output: lists of lon, lat, category, int of length of list, and timestamps
    """
    lat = raw['Latitude'].copy()
    lat = lat.dropna(0)
    lon = raw['Longitude'].copy()
    lon = lon.dropna(0)
    interpolate = list(range(1,len(lon)+1))
    for i in range(1,len(lat)+1):
        lat[i] = convert(lat[i]) #formatting lat and lon to numbers and not a mix of numbers and letters and make it if it's 360° for lon to be -180-180.
    for i in range(1,len(lon)+1):
        lon[i] = convert(lon[i])
    f_inter_x = make_interp_spline(interpolate, lon) #, kind='linear', bounds_error=False, fill_value="extrapolate")
    f_inter_y = make_interp_spline(interpolate, lat) #, kind='linear', bounds_error=False, fill_value='extrapolate')
    raw['Time'] = pd.to_datetime(raw['Time'], format='%Y%m%d%H')
    timedt = raw['Time'].copy()
    timedt = timedt.dropna(0)
    B_x = []
    B_y = []
    B_extra = []
    B_time = []
    i = 0
    while i < len(timedt)-1:
        checkdelta = [(timedt.iloc[i+1]- timedt.iloc[i]).total_seconds()/(3*3600)]
        k = 1
        while sum(checkdelta) < 1:
            checkdelta.append((timedt.iloc[i+1+k] - timedt.iloc[i+k]).total_seconds()/(3*3600))
            k += 1
        for h in range(0,len(checkdelta)):
            for t in range(0, int(checkdelta[h]*48)):
                t = t / int(checkdelta[h]*48)
                B_x.append(f_inter_x(i+t+1))
                B_y.append(f_inter_y(i+t+1))
                c = raw.at[i+1,'Category']
                B_extra.append(c)
            i += 1
        B_time.append(i)
    print(len(B_x))
    print(len(B_time)*48)
    return B_x,B_y,B_extra,len(B_x),B_time

def get_frame_timeline(date):
    """
    since the timeline takes exactly 22.523 frames for every quadrants to appear,
    that means that we have 4*22.523 frames per day.
    """
    fra = 22.523
    frame = date.day*fra*4 - 38 
    days_in_month = {1:31,
                     2:28,
                     3:31,
                     4:30,
                     5:31,
                     6:30,
                     7:31,
                     8:31,
                     9:30,
                     10:31,
                     11:30,
                     12:31}
    for i in range(1,date.month):
        frame += days_in_month[i]*4*fra
    if date.year%4 == 0 and date.month > 2:
        frame += 4*fra
        print('bisectile')
    if (date.hour == 0 or date.hour ==3 ) and date.day == 1 and date.month == 1:
        frame += 2*fra + 364*4*fra
    elif date.hour == 0 or date.hour == 3:
        frame -= 2*fra
    elif date.hour == 6 or date.hour == 9:
        frame -= fra
    elif date.hour == 18 or date.hour == 21:
        frame += fra
    #if it's 12 or 15 o'clock, we don't need to add or substract frames
    return frame

def get_transparent(img,step):
    b,g,r = cv2.split(img)
    _,rr = cv2.threshold(r, weights[extra[step]][0], 255, cv2.THRESH_TOZERO)
    _,gg = cv2.threshold(g, weights[extra[step]][1], 255, cv2.THRESH_TOZERO)
    _,bb = cv2.threshold(b, weights[extra[step]][2], 255, cv2.THRESH_TOZERO)
    _,alpha = cv2.threshold(rr+gg+bb, 255, 255, cv2.THRESH_TRUNC)
    rgba = [r,g,b,alpha]
    return cv2.merge(rgba,4)

def convert(x):
    try:
        x = float(x)
        if x > 180:
            return x-360
        else:
            return x
    except ValueError:
        multiplier = 1 if x[-1] in ['N', 'E'] else -1
        return multiplier * float(x[:-1])

def convertimg(latitude=None,longitude=None):
    """
    gets coordinates in latitude and longitude as input and outputs its equivalent as the shape of the background image
    """
    global background
    if latitude is not None:
        imglat = -(latitude-90)/180*(background.shape[0])
    if longitude is not None:
        imglon = (longitude+180)/360*(background.shape[1])
    if latitude is None:
        return int(imglon)
    elif longitude is None:
        return int(imglat)
    else:
        return int(imglat), int(imglon)

def anim(i):
    global ab
    global y
    global x
    global yfin
    global xfin
    global n
    global name
    global background_cropped
    global animvid
    global timeline
    global annotationtime
    global xpast
    global ypast
    global limitingside
    if i < length-1:
        x1, y1 = lon[i], lat[i]
        x2, y2 = lon[i+1], lat[i+1]
        if i % 48 != 0 and extra[i-1] != extra[i]:
            animvid = cv2.VideoCapture('icons/' + vidpath[extra[i]]+'.mp4')
            all = animvid.get(cv2.CAP_PROP_FRAME_COUNT)
            animvid.set(1,i-((i)//all)*all)
        if i % 48 == 0:
            animvid = cv2.VideoCapture('icons/' + vidpath[extra[i]]+'.mp4')
            all = animvid.get(cv2.CAP_PROP_FRAME_COUNT)
            animvid.set(1,i-((i)//all)*all)
            print(f'second : {i/steps}')
            print(timetable[int(i/48)])
            print(raw['Time'][timetable[int(i/48)]])
            if raw['Time'][timetable[int(i/48)]].year != raw['Time'][timetable[int(i/48)-1]].year:
                year.set_text(str(raw['Time'][timetable[int(i/48)]].year))
            frame = get_frame_timeline(raw['Time'][timetable[int(i/48)]])
            timeline.set(1,frame)
            _,imgtemp = timeline.read()
            blue,green,red = cv2.split(imgtemp)
            imgtemp = cv2.cvtColor(imgtemp, cv2.COLOR_BGR2GRAY)
            _,alpha = cv2.threshold(imgtemp,100,255,cv2.THRESH_BINARY)
            imgtemp = cv2.merge([red,green,blue,alpha],4)
            imgtemp = cv2.resize(imgtemp,[360,280])
            im = OffsetImage(imgtemp, zoom=1)
            annotationtime.offsetbox = im
        success,animage = animvid.read()
        if not success:
            animvid.set(1,1)
            success,animage = animvid.read()
        im = OffsetImage(get_transparent(animage,i), zoom=1)
        ab.offsetbox = im
        displacement = [0,0]
        xtemp = convertimg(longitude = x1 + (x2-x1)-10)
        ytemp = convertimg(latitude = y1 + (y2-y1)+10)
        t3 = time.time()
        for k in tracks: #afficher la trajectoire de la tempête au fur et à mesure que la tempête avance. (et ne plus les afficher quand ils quittent l'écran)
            temp = k.get_data(orig=True)
            futuretemp = [[temp[0][0]-xtemp+x,temp[0][1]-xtemp+x],[temp[1][0]-ytemp+y,temp[1][1]-ytemp+y]]
            if (futuretemp[0][0] < 0 and futuretemp[0][1] < 0 or futuretemp[1][0] < 0 and futuretemp[1][1] < 0) or  (futuretemp[0][0] > 1200 and futuretemp[0][1] > 1200 or futuretemp[1][0] > 1200 and futuretemp[1][1] > 1200):
                k.set_visible(False)
            elif not k.get_visible():
                k.set_visible(True)
            k.set(xdata=futuretemp[0],ydata=futuretemp[1])
        print(time.time()-t3)
        if i%2 == 0: #every two frames, add a piece of the track
            tracks.append(plt.plot([600-convertimg(longitude = x1 + (x2-x1)-10)+xpast,600],[600-convertimg(latitude = y1 + (y2-y1)+10)+ypast,600],color=categories[extra[i]],lw=15)[0])
        if convertimg(latitude = y1 + (y2-y1)+10) < background.shape[0]-1200 and convertimg(latitude = y1 + (y2-y1)+10) > 0:
            y = convertimg(latitude = y1 + (y2-y1)+10)
        else:
            displacement[1] = convertimg(latitude = y1 + (y2-y1)+10)
        if convertimg(longitude = x1 + (x2-x1)-10) < background.shape[1]-1200 and convertimg(longitude = x1 + (x2-x1)-10) > 0:
            x = convertimg(longitude = x1 + (x2-x1)-10)
        else:
            displacement[0] = convertimg(longitude = x1 + (x2-x1)-10)
        if displacement != [0,0]:
            name.xy = ((background_cropped.get_extent()[0]+background_cropped.get_extent()[1])/2 + displacement[0],(background_cropped.get_extent()[2]+background_cropped.get_extent()[3])/2 + displacement[1])
        ab.xybox = ((background_cropped.get_extent()[0]+background_cropped.get_extent()[1])/2 + displacement[0],(background_cropped.get_extent()[2]+background_cropped.get_extent()[3])/2 + displacement[1])
        if i ==1 or i %2 == 0:
            xpast = x
            ypast = y
        background_cropped.set_data(background[y:y+1200, x:x+1200,:])
    elif i == length-1: #when we finished the storm animation, start a zoom out animation.
        yfin = [convertimg(latitude=min(lat)-10),convertimg(latitude=max(lat)+10)]
        print(yfin)
        xfin = [convertimg(latitude=min(lon)-10),convertimg(latitude=max(lon)+10)]
        print(xfin)
        if xfin[1]-xfin[0] > (yfin[1]-yfin[0])*2: #to keep the ratio of the background image (0.5), we first need to determine which side is the smallest compared to the ratio.
            limitingside = "x"
        else:
            limitingside = "y"
        n = 1
        print(limitingside)
        if limitingside == "x":
            move = [int(x+(xfin[1]-x)/120*n)*0.5
                   ,int(x+1200+(xfin[0]-x)/120*n)*0.5
                   ,int(x+(xfin[1]-x)/120*n)
                   ,int(x+1200+(xfin[0]-x)/120*n)]
        else:
            move = [int(y+(yfin[1]-y)/120*n)
                   ,int(y+1200+(yfin[0]-y)/120*n)
                   ,int(y+(yfin[1]-y)/120*n)*2
                   ,int(y+1200+(yfin[0]-y)/120*n)*2]
            background_cropped.set_data(background[move[0]:move[1], move[2]:move[3],:])
    elif i > length-1:
        n+=1
        if limitingside == "x":
            move = [int(x+(xfin[1]-x)/120*n)*0.5
                   ,int(x+1200+(xfin[0]-x)/120*n)*0.5
                   ,int(x+(xfin[1]-x)/120*n)
                   ,int(x+1200+(xfin[0]-x)/120*n)]
        else:
            move = [int(y+(yfin[1]-y)/120*n)
                   ,int(y+1200+(yfin[0]-y)/120*n)
                   ,int(y+(yfin[1]-y)/120*n)*2
                   ,int(y+1200+(yfin[0]-y)/120*n)*2]
        background_cropped.set_data(background[move[0]:move[1], move[2]:move[3],:])

categories = {'C5':'magenta',
              'C4':'red',
              'C3':'orange',
              'C2':'gold',
              'C1':'yellow',
              'TS':'lime',
              'TD':'dodgerblue',
              'EX':'gray',
              'DB':'deepskyblue',
              'LO':'deepskyblue',
              'PTWS':'deepskyblue',
              'PSWS':'gray',
              'MNWS':'aquamarine',
              'MDWS':'lime',
              'STWS':'yellow',
              'SGWS':'orange',
              'SVWS':'red'}

impath = {'C5':'icons/C5.png',
          'C4':'icons/C4.png',
          'C3':'icons/C3.png',
          'C2':'icons/C2.png',
          'C1':'icons/C1.png',
          'TS':'icons/TS.png',
          'TD':'icons/TD.png',
          'EX':'icons/EX.png',
          'LO':'icons/LO.png',
          'DB':'icons/LO.png'}

weights = { 'TS' : (255,0,255),
            'TD': (255,255,0),
            'SD': (255,255,0),
            'IN': (0,0,0),
            'LO': (255,255,0),
            'DB': (255,255,0),
            'SS': (255,0,255),
            'C1': (255,0,255),
            'C2': (0,255,255),
            'C3': (0,255,255),
            'C4': (0,255,255),
            'C5': (0,255,255),
            'cat5-2alt': (0,255,255),
            'cat5-3alt': (255,255,0),
            'cat5-4alt': (255,255,0),
            'EX': (255,255,0),
            'PTWS': (255,255,0),
            'PSWS': (255,255,0),
            'MNWS': (255,0,255),
            'MDWS': (255,0,255),
            'STWS': (255,0,255),
            'SGWS': (0,255,255),
            'SVWS': (0,255,255)}

vidpath = { 'TS' : '_ts',
            'TD': '__td',
            'SD': '__sd',
            'IN': '___in',
            'LO': '___l',
            'DB': '___l',
            'SS': '_ss',
            'C1': 'cat1',
            'C2': 'cat2',
            'C3': 'cat3',
            'C4': 'cat4',
            'C5': 'cat5-1alt',
            'cat5-2alt': (0,255,255),
            'cat5-3alt': (255,255,0),
            'cat5-4alt': (255,255,0),
            'EX': 'ex',
            'PTWS':'(WS) PTWS',
            'PSWS':'(EX) PSWS',
            'MNWS':'(1) MNWS',
            'MDWS':'(2) MDWS',
            'STWS':'(3) STWS',
            'SGWS':'(4) SGWS',
            'SVWS':'(5) SVWS'}
plt.rcParams['animation.ffmpeg_path'] = 'C:\\Users\\Robin\\Downloads\\ffmpeg-6.0-essentials_build\\ffmpeg-6.0-essentials_build\\bin\\ffmpeg.exe'
answer = input("Name of the windstorm")
raw = pd.read_excel("Windstorm dataset modified.xlsx", sheet_name=answer)
raw = raw[1:]
raw.columns = ['Time', '1','2','3','Longitude','Latitude','6','7','8','9','10','11','12','Category']
for i in raw.loc[raw['Latitude']==1E+25].index:
    raw['Latitude'][i] = raw['2'][i]
for i in raw.loc[raw['Longitude']==1E+25].index:
    raw['Longitude'][i] = raw['1'][i]
raw = raw.set_index([pd.Index(range(1,len(raw)+1))])
lon, lat, extra, length, timetable = get_data_points(raw)
font_path = 'fonts/Typomoderno bold.ttf'
prop = fm.FontProperties(fname=font_path)
fig = plt.figure(figsize=[25,25],dpi=50)
ax = fig.add_subplot()
background = plt.imread('icons/background.jpg')
ax.axis('off')
steps = 48
x1, y1 = lon[0], lat[0]
x2, y2 = lon[1], lat[1]
y = convertimg(latitude = y1 + (y2-y1)/steps*1+10)
x = convertimg(longitude = x1 + (x2-x1)/steps*1-10)
background_cropped = background[y:y+1200, x:x+1200,:]
background_cropped = ax.imshow(background_cropped, aspect = 'auto')
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
img = PIL.Image.open('icons/' + vidpath[extra[0]] + ' Icon.png')
im = OffsetImage(img, zoom=1)
ab = AnnotationBbox(im, ((background_cropped.get_extent()[0]+background_cropped.get_extent()[1])/2,(background_cropped.get_extent()[2]+background_cropped.get_extent()[3])/2), xycoords='data', frameon=False)
ax.add_artist((ab))
name = plt.annotate(answer,((background_cropped.get_extent()[0]+background_cropped.get_extent()[1])/2,(background_cropped.get_extent()[2]+background_cropped.get_extent()[3])/2), xytext=(130,130),textcoords='offset points', size=100, color ='w', weight='bold', fontproperties=prop)
ax.add_artist((name))
animvid = cv2.VideoCapture('icons/'+ vidpath[extra[0]]+'.mp4')
timeline = cv2.VideoCapture('icons/timeline_cropped.mp4')
timeline.set(1,get_frame_timeline(raw['Time'][1]))
_,imgtemp = timeline.read()
b,g,r = cv2.split(imgtemp)
imgtemp = cv2.cvtColor(imgtemp, cv2.COLOR_BGR2GRAY)
_,alpha = cv2.threshold(imgtemp,100,255,cv2.THRESH_BINARY)
imgtemp = cv2.merge([r,g,b,alpha],4)
imgtemp = cv2.resize(imgtemp,[360,280])
im = OffsetImage(imgtemp, zoom=1)
annotationtime = AnnotationBbox(im,(150,1050), xycoords='data', frameon=False)
ax.add_artist((annotationtime))
year = plt.annotate(str(raw['Time'][1].year), (100,1180), xycoords='data', xytext=(0,0), textcoords='offset points', size=70, color='w', weight='bold', fontproperties=prop)
ax.add_artist((year))
tracks = []

ani = animation.FuncAnimation(fig, anim, frames=range(1,length-1+120), interval=5, blit = False) #on prend 48 frames pour le dezoom puis on reprend la trajectoire mais en plus rapide.
writervideo = animation.FFMpegWriter(fps=48)
t1 = time.time()
answer = input('name of the output file : ')
ani.save(filename='output/animations/'+ answer + '.mp4', writer = writervideo)
print(time.time()-t1)