def confirm(message: str):
    print(message)
    while True:
        resp = input("Please answer Y or N: ")
        if resp == "Y":
            return True
        elif resp == "N":
            return False


def manual(message: str):
    print(message)
    while True:
        resp = input("Write 'done' without quotes when done: ")
        if resp == "done":
            return
