import os

try:
    import rootpath
except ImportError:
    rootpath = None

DETECTED_PATH = (rootpath.detect() if rootpath else os.getcwd()) or "/srv/www/grounded.world/home"

if __name__ == "__main__":
    path = os.path.join(DETECTED_PATH, "data").replace("\\", "/")
    print(path)
