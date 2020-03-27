import math
import tkinter

def createGrid(xRange, yRange):
    #Create a grid
    
    grid = []
    for x in range(xRange):
      for y in range(yRange):
        grid.append([x, y, "N"])

    return grid
    
def placeObjects(grid, Tx, Rx1, Rx2, Rx3, Target):
    #Place transmitter, receivers and target on grid

    for entry in grid:

        if entry[0] == Tx[0] and entry[1] == Tx[1]:
            entry[2] = 'Tx'

        if entry[0] == Rx1[0] and entry[1] == Rx1[1]:
            entry[2] = 'Rx1'

        if entry[0] == Rx2[0] and entry[1] == Rx2[1]:
            entry[2] = 'Rx2'

        if entry[0] == Rx3[0] and entry[1] == Rx3[1]:
            entry[2] = 'Rx3'

        if entry[0] == Target[0] and entry[1] == Target[1]:
            entry[2] = 'Tar'

    return grid

def findDistance(first, second):
    #find distance between 2 points
    distance = math.sqrt((first[0] - second[0])**2 + (first[1] - second[1])**2)
    
    return distance

def bruteForce(grid, Tx, Rx1, Rx2, Rx3):

    rangeSumArray = []
    
    for entry in grid:
        
        currentRange1 = findDistance(Tx, entry) + findDistance(Rx1, entry)
        currentRange2 = findDistance(Tx, entry) + findDistance(Rx2, entry)
        currentRange3 = findDistance(Tx, entry) + findDistance(Rx3, entry)
        rangeSum = currentRange1 + currentRange2 + currentRange3
        
        rangeSumArray.append(rangeSum)

    target = grid[rangeSumArray.index(min(rangeSumArray))]
    return target

def main():

    #Set conditions for localisation testing
    Tx = (0, 0)
    Rx1 = (5, 2)
    Rx2 =(7, 7)
    Rx3 =(3, 7)
    target = (6, 9)
    xRange = 10
    yRange = 10
    
    grid = createGrid(xRange, yRange)
    grid = placeObjects(grid, Tx, Rx1, Rx2, Rx3, target)
    result = bruteForce(grid, Tx, Rx1, Rx2, Rx3)
    print(result)
    print(grid)


main()
