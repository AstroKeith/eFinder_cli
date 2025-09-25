with open ("/boot/firmware/config.txt") as h:
    for line in h:
        if "dtoverlay=vc4-kms-v3d" in line:
            line = '#'+line
        elif "max_framebuffers=2" in line:
            line = '#'+line
        with open("newconfig.txt","a") as j:
            j.write(line)
            