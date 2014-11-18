import socket, time, sys
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(2)
client_socket.connect((sys.argv[1], 4001))

def send(data):
  if (data <> 'Q' and data <> 'q'):
      for char in data:
        client_socket.send(char)
        client_socket.recv(1)
      client_socket.send('\r')
      client_socket.recv(1)
  else:
      client_socket.close()
      quit()

send('V')

while 1:
    buffer = ''
    while 1:
      try:
        buffer += client_socket.recv(1024)
      except socket.timeout: 
        break
      if buffer.endswith('\r\n'):
        result =buffer[:-2]
        break

    # We now have all data we can in "buffer"
    print '%r' % result
    data = raw_input ( "SEND( TYPE q or Q to Quit):" )
    send(data)

