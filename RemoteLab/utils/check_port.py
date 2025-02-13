import sys
import socket
import subprocess


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
        ret = sock.connect_ex(("127.0.0.1", port))
        sock.close()
    except:
        ret = -1

    return ret


def check_active_connection(servers: list = ["openocd"]):
    """
    Check if given application passed as a server list has
    ports that listen or have established connection
    is listening or established

    Returns a dictionary with port as key and holding a dictionary
    with keys:
    - user
    - listen (might be not present)
    - established (might be not present)
    """

    # run lsof, on TCP connections: listen or establish
    # display numerical value of ports
    proc = subprocess.Popen(
        ["lsof", "-PiTCP", "-sTCP:ESTABLISHED,LISTEN"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    result, _ = proc.communicate()
    result = result.decode("utf-8")
    data = result.split("\n")
    header = data[0]
    header = " ".join(header.split())
    header = header.split(" ")
    lines = data[1:]

    ports = {}

    user_idx = -1
    address_idx = -1
    for idx, col in enumerate(header):
        if col.lower() == "user":
            user_idx = idx
        elif col.lower() == "name":
            address_idx = idx

    def find_server(line, servers):
        for server in servers:
            if line.find(server) != -1:
                return True
        return False

    for line in lines:
        if find_server(line, servers):
            parts = " ".join(line.split())
            parts = parts.split(" ")
            user = parts[user_idx]
            address = parts[address_idx]

            if line.find("LISTEN") != -1:
                # example
                # openocd 855782   pi   10u  IPv4 4345609      0t0  TCP localhost:3018 (LISTEN)
                other = address.split(":")
                port = int(other[1])

                if port not in ports:
                    ports[port] = {"user": user}

                ports[port]["listen"] = True

            if line.find("ESTABLISHED") != -1:
                # example
                # openocd 855782   pi   11u  IPv4 4443174      0t0  TCP localhost:3018->localhost:45528 (ESTABLISHED)
                other = address.split("->")
                other = other[0].split(":")
                port = int(other[1])

                if port not in ports:
                    ports[port] = {"user": user}

                ports[port]["established"] = True

    return ports


def main():
    try:
        port = int(sys.argv[1])
    except:
        exit(-1)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
    except:
        exit(-1)

    if result == 0:
        print("0")
        exit(0)
    else:
        print("1")
        exit(1)


if __name__ == "__main__":
    main()
