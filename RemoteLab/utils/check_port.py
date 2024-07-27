import sys
import socket

def checkPort(port):
    """
    Check if port is open
    return:  0  -- port open
             1  -- port closed
            -1  -- error
    """
    ret = 0
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ret = sock.connect_ex(('127.0.0.1',port))
        sock.close()
    except:
        ret = -1

    return ret

def main():
    try:
        port = int(sys.argv[1])
    except:
        exit(-1)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1',port))
        sock.close()
    except:
        exit(-1)

    if result == 0:
        print("0")
        exit(0)
    else:
        print("1")
        exit(1)
    

if __name__=="__main__":
    main()
