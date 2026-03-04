import argparse
import zmq
from robot import Arm


def main():
    parser = argparse.ArgumentParser(description="ZMQ server bridging gym env to robot hardware")
    parser.add_argument('--port', type=int, default=5555)
    args = parser.parse_args()

    arm = Arm()

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{args.port}")
    print(f"Listening on tcp://*:{args.port}")

    try:
        while True:
            message: dict = socket.recv_json()  # type: ignore[assignment]
            cmd = message.get('cmd')

            if cmd == 'reset':
                arm.reset_position()
                obs = arm.get_position()
                socket.send_json({'obs': obs, 'info': {}})

            elif cmd == 'step':
                action = message.get('action')
                obs = arm.step(action)
                socket.send_json({'obs': obs})

            elif cmd == 'stop':
                obs = arm.stop()
                socket.send_json({'obs': obs})

            else:
                socket.send_json({'error': f'Unknown command: {cmd}'})

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        arm.stop()
        socket.close()
        context.term()


if __name__ == '__main__':
    main()
