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

def findNorm(first, second):
    #find distance between 2 points
    norm = math.sqrt((first[0] - second[0])**2 + (first[1] - second[1])**2)
    
    return norm

def bruteForce(grid, Tx, Rx1, Rx2, Rx3, r1, r2, r3):

    LArray = []
    
    for entry in grid:
        
        currentRange1 = findNorm(Tx, entry) + findNorm(Rx1, entry)
        currentRange2 = findNorm(Tx, entry) + findNorm(Rx2, entry)
        currentRange3 = findNorm(Tx, entry) + findNorm(Rx3, entry)

        L1 = (currentRange1 - r1)**2
        L2 = (currentRange2 - r2)**2
        L3 = (currentRange3 - r3)**2

        L = (L1 + L2 + L3)/3
        LArray.append(L)
    
    target = grid[LArray.index(min(LArray))]
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

    #Create grid + place objects
    grid = createGrid(xRange, yRange)
    grid = placeObjects(grid, Tx, Rx1, Rx2, Rx3, target)

    #calculate true ranges, in practical test this will be given as the output of the SDR
    r1 = findNorm(Tx, target) + findNorm(Rx1, target)
    r2 = findNorm(Tx, target) + findNorm(Rx2, target)
    r3 = findNorm(Tx, target) + findNorm(Rx3, target)
    
    #Perform Calculations
    result = bruteForce(grid, Tx, Rx1, Rx2, Rx3, r1, r2, r3)
    
    print(result)
    print(grid)


main()
