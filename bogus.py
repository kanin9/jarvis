from random import randint, randrange
from datetime import timedelta, datetime

names = [
    "Анастасия",
    "Илья",
    "Алтынай",
    "Иван",
    "Арман",
    "Альнур",
    "Лука",
    "Улан",
    "Айша"
]


class Call:
    def __init__(self, date, type, caller, file, commentaries, status):
        self.date = date
        self.type = type
        self.caller = caller
        self.file = file
        self.commentaries = commentaries
        self.status = status


def randomDate(start, end):
    delta = end - start
    idelta = delta.days * 24 * 60 * 60 + delta.seconds
    randomseconds = randrange(idelta)
    return start + timedelta(seconds=randomseconds)


def randomName():
    return names[randrange(len(names))]


def getFillerData():
    start = datetime.strptime('1/15/2023 1:30 PM', '%m/%d/%Y %I:%M %p')
    end = datetime.strptime('4/7/2023 4:50 AM', '%m/%d/%Y %I:%M %p')
    while True:
        yield Call(randomDate(start, end).strftime('%d/%m/%Y %H:%M'), "Исходящий", randomName(), randrange(24, 400),
                   "Нет комментариев", ["Продано", "Отказано"][randrange(2)])
