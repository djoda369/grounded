import time

from conversation_checker import analyze_meetings

if __name__ == "__main__":
    print("Checking conversations")
    while True:
        analyze_meetings()
        time.sleep(60*30)
    