from app.controller import Controller
import app.http_server as server


def main():
    controller = Controller()
    server.init(controller)
    server.start_server_in_separate_thread()
    controller.run()


if __name__ == '__main__':
    main()
