from multiprocessing import Process


class TimingHandler(Process):

    def __init__(self):
        Process.__init__(self)
