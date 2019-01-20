from app.controller import Controller
from app.http_server import start_server_in_separate_thread


def main():
    main_controller = Controller()
    start_server_in_separate_thread(main_controller)
    main_controller.run()


if __name__ == '__main__':
    main()
