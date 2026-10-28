"""Temporary bridge until Marty has its own speaker: the robot publishes text,
a client on another machine speaks it. Delete this once voice.say runs on the robot.

Robot side:   say = VoicePublisher().say
Client side:  python voice_link.py [host]     (default marty.local)
"""
import sys

import zmq

PORT = 5556


class VoicePublisher:
    """Fire-and-forget: never blocks, and messages are dropped if no client is listening."""

    def __init__(self, port=PORT):
        self.socket = zmq.Context.instance().socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{port}")

    def say(self, text):
        print(f"SAY: {text}")
        self.socket.send_json({'say': text})


def main():
    import voice
    from calibration import PHRASES

    host = sys.argv[1] if len(sys.argv) > 1 else 'marty.local'
    for text in PHRASES:  # render ahead so the first prompt isn't delayed
        voice.render(text)

    socket = zmq.Context.instance().socket(zmq.SUB)
    socket.connect(f"tcp://{host}:{PORT}")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    print(f"Listening to tcp://{host}:{PORT}")
    try:
        while True:
            text = socket.recv_json()['say']
            print(text)
            voice.say(text)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
