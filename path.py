import os

import rootpath

DETECTED_PATH = rootpath.detect() or "/srv/www/grounded.world/home"

if __name__ == "__main__":
    path = os.path.join(DETECTED_PATH, "data").replace("\\", "/")
    print(path)
