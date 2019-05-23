import malmo.minecraftbootstrap

if __name__ == "__main__":
    ports = input("Ports:")
    ports = eval(ports)
    malmo.minecraftbootstrap.launch_minecraft(ports)