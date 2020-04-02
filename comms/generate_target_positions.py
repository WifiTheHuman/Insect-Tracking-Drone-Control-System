import random

FILENAME = "target_positions.txt"
NUM_READINGS = 1000
MAX_X = 10
MAX_Y = 10


def main():
    file = open(FILENAME, "w")

    for i in range(NUM_READINGS):
        x = random.randrange(MAX_X)
        y = random.randrange(MAX_Y)

        file.write("{},{}\n".format(x, y))

    file.close()


main()
