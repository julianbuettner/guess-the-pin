#!/usr/bin/python3

from requests import post
from time import sleep
from datetime import datetime
from time import time
from random import shuffle, seed
import requests.exceptions
from enum import Enum
from typing import Tuple, Optional
from re import compile

# If you are a pro, you can configure this script

# If you want to spread across multiple machines
# to parallelize across IP-addresses, you can
# increase your agent count and set ids.

AGENT_COUNT = 1
AGENT_ID = 0  # start counting from 0
SEED = 1415926535  # must be the same across all agents
LOGFILE = "guess-the-pin.log"


def log(*args, end="\n"):
    """
    A poor man's (or woman's) logging.
    """
    time_prefix = datetime.now().strftime("%Y-%m-%dT%H:%M:%S ")
    with open(LOGFILE, 'a') as f:
        string = time_prefix + " ".join(str(x) for x in args)
        string = ("\n" + time_prefix).join(string.split("\n"))
        print(string)
        f.write(string + end)


class GuessResult(Enum):
    WRONG = 1
    RIGHT = 2
    UNEXPECTED = 3
    KICKED = 4


def perform_guess(i) -> Tuple[GuessResult, Optional[int]]:
    try:
        res = post("https://www.guessthepin.com/prg.php", data={"guess": "{:04}".format(i)})
    except requests.exceptions.ConnectionError:
        return GuessResult.KICKED, None

    text = res.text.lower()

    if "You guessed the PIN" in res.text:
        return GuessResult.RIGHT, None

    # he current PIN has been incorrectly guessed <strong>12,795&nbsp;times</strong> in the last <str
    counter_and_suffix = text.split("pin has been incorrectly guessed <strong>")[1]
    counter = counter_and_suffix.split("&nbsp;times</strong>")[0]

    counter_int = int(counter.replace(",", ""))

    if "is not the PIN" in res.text:
        return GuessResult.WRONG, counter_int

    print(res.text)
    log("Unknown result:")
    log("=" * 30)
    log(guess.text)
    return GuessResult.UNEXPECTED, counter_int


class OpenGuesses:
    def __init__(self, agent_id, agent_count):
        self.agent_id = agent_id
        self.agent_count = agent_count
        self.reset()

    def reset(self):
        self.count = 0
        self.random_mode = False
        self.guesses_per_agent = int(10000 / self.agent_count) + 1
        values = [i for i in range(10000)]
        seed(SEED)
        shuffle(values)
        
        start = self.agent_id * self.guesses_per_agent
        end = (self.agent_id + 1) * self.guesses_per_agent
        self.values = values[start:end]
        seed(int(time()))
        shuffle(self.values)

    def _generate_fallback(self):
        self.values = [i for i in range(10000)]
        seed(int(time()))
        shuffle(self.values)

    def pop(self):
        self.count += 1
        if len(self.values) == 0:
            log("Agent trials done. Try random numbers now.")
            self.random_mode = True
            self._generate_fallback()
        return self.values.pop()


def main():
    last_guess_count = 0

    open_guesses = OpenGuesses(AGENT_ID, AGENT_COUNT)
    open_guesses.reset()

    i = open_guesses.pop()

    log("Start...")

    while True:
        print(
            "{:04} - {:04} : ".format(open_guesses.count, i),
            end=""
        )

        result, guess_count = perform_guess(i)
        if guess_count is not None:
            if guess_count < last_guess_count:
                log("Some one else guessed correctly. Reset.")
                open_guesses.reset()
            last_guess_count = guess_count

        if result == GuessResult.UNEXPECTED:
            print()
            log("Unexpected result")
            print("Sleep 10s")
            sleep(10)
            continue

        if result == GuessResult.KICKED:
            print()
            log("Oooops, we got kicked :)")
            print("Sleep 20s")
            sleep(20)
            continue

        if result == result.RIGHT:
            print()
            log("Hell yeah! Right guess:", i)
            open_guesses.reset()

        if result.WRONG:
            print("Nope")

        i = open_guesses.pop()


if __name__ == "__main__":
    main()


def test_agent_split():
    for agent_count in range(1, 9):
        agent_open_guesses = [OpenGuesses(i, agent_count) for i in range(0, agent_count)]

        values = set(i for i in range(0, 10000))

        for agent_guesses in agent_open_guesses:
            while True:
                trial = agent_guesses.pop()
                if agent_guesses.random_mode == True:
                    break
                assert trial in values
                values.remove(trial)
        assert len(values) == 0
