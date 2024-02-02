class Game:
    def __init__(self):
        self.ID = None
        self.start = None
        self.end = None


    def __repr__(self):
        return f'Game(ID={self.ID}, start={self.start}, end={self.end})'