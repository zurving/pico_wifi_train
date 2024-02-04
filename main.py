import network
import socket
import time
import machine
import json

speed = 30
direction = True
m1 = machine.PWM(machine.Pin(21, machine.Pin.OUT))
m2 = machine.Pin(20, machine.Pin.OUT)
m1.freq(14000)

def setSpeedAndDir( new_speed, new_dir ):
    global speed
    global direction
    speed = new_speed
    if( speed < 0 ):
        speed = 0
    elif( speed > 100 ):
        speed = 100
    direction = new_dir
    # actually change the motors speed
    percent = speed/100
    if( not new_dir ):
        percent = 1.0 - percent
    duty = percent * 65025
    m1.duty_u16(int(duty)) #speed is a percent
    m2(direction)
    
def printStatus( cl ):
    data = { 'speed': speed, 'direction': direction }
    cl.send('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
    cl.send(json.dumps(data))
    cl.close()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

ssidfile = open('ssids.txt', 'r')

while wlan.status() !=3:
    # Get next line from file
    line = ssidfile.readline()
    parts = line.split('###', 1)
    ssid = parts[0]
    password = parts[1]
    print('ssid: ' + ssid)
    wlan.connect(ssid, password)
    network.hostname( "pico_train" )
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

# turn on the LED so we know it's working
machine.Pin("LED").value(1)
# enable the motor
machine.Pin(17, machine.Pin.OUT).value(1)


setSpeedAndDir( 25, 1 )

print('listening on', addr)

# Listen for connections
try:
    while True:
        try:
            cl, addr = s.accept()
            print('client connected from', addr)
            request = cl.recv(1024)
            print(request)

            stateis = ""
            request = str(request)
            isIndex = request.find('GET / HTTP')
            jquery = request.find('/jquery-3.7.0.js')
            isSpeed = request.find('GET /speed/')
            isDirection = request.find('GET /direction/')
            isStatus = request.find('GET /status/')
            isImage = request.find('GET /image.png')
            
            if jquery == 6:
                buffer_size = 2048
                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/javascript\r\n\r\n')
                with open('jquery-3.7.0.min.js', mode="rb") as f:
                    chunk = f.read(buffer_size)
                    while chunk:
                        cl.write( chunk )
                        chunk = f.read( buffer_size )
                cl.close()
            elif isImage == 2:
                buffer_size = 2048
                cl.send('HTTP/1.0 200 OK\r\nContent-type: image/x-png\r\n\r\n')
                with open('train.png', mode="rb") as f:
                    chunk = f.read(buffer_size)
                    while chunk:
                        cl.write( chunk )
                        chunk = f.read( buffer_size )
                cl.close()
            elif isIndex == 2:
                html = ""
                with open('index.html', 'r', encoding="utf-8") as file:
                    html = file.read()            
                response = html
                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                cl.send(response)
                cl.close()
            elif isSpeed == 2:
                request = request[13:]
                idx = request.find(" ")
                request = request[:idx]
                print( request )
                new_speed = int(request)
                setSpeedAndDir( new_speed, direction )
                printStatus( cl )
            elif isDirection == 2:
                setSpeedAndDir( speed, not( direction ) )
                printStatus( cl )
            elif isStatus == 2:
                printStatus( cl )
            else:
                cl.send('HTTP/1.0 404 NOT FOUND\r\nContent-type: text/plain\r\n\r\n')
                cl.send("404 NOT FOUND")
                cl.close()                

        except OSError as e:
            cl.close()
            print('connection closed')
except:
    s.close()