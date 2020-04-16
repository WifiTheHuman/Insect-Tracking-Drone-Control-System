import math
import tkinter

from gps import GPSCoord

#current problems: bad formatting converting lat/long to xy
#inaccurate method, won't work if they're too far away
#using 100000 to convert lat/long to xyz, if units are different won't work

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

        L = (L1 + L2 + L3) / 3
        LArray.append(L)

    target = grid[LArray.index(min(LArray))]
    return target

def calcX(RxiCoord, TxCoord, Tx):
    #converts gps coords to cartesian X coord
    x = TxCoord.x_distance(RxiCoord)
    xGrid = Tx[0] + x
    return round(xGrid)

def calcY(RxiCoord, TxCoord, Tx):
    #converts gps coords to cartesian Y coord
    y = TxCoord.y_distance(RxiCoord)
    yGrid = Tx[1] + y
    return round(yGrid)

def cartesianToLatLong(target, Tx, TxCoord):
    #converts cartesian coords to GPS coords
    x = target[0] - Tx[0]
    y = target[1] - Tx[1]
    return TxCoord.add_x_offset(x).add_y_offset(y)
    
def estimate_target_position(tx, rx1, rx2, rx3, range1, range2, range3):
    # TODO: Implement
    # tx, rx1, rx2, rx3 and the return value are of type GPSCoord from gps.py
    # The ranges are floats in meters

    #Determine size of grid (metres), create grid
    xRange = 20
    yRange = 20
    grid = createGrid(xRange, yRange)

    #Transmitter drone always centre of grid
    Tx = (xRange/2, yRange/2)
    
    #Set conditions for localisation testing
    TxCoord = tx

    Rx1Coord = rx1
    Rx2Coord = rx2
    Rx3Coord = rx3

    #targetCoord = GPSCoord(-43.52059, 172.58315)

    #Map from GPS to grid locations
    Rx1 = (calcX(Rx1Coord, TxCoord, Tx), calcY(Rx1Coord, TxCoord, Tx))
    Rx2 = (calcX(Rx2Coord, TxCoord, Tx), calcY(Rx2Coord, TxCoord, Tx))
    Rx3 = (calcX(Rx3Coord, TxCoord, Tx), calcY(Rx3Coord, TxCoord, Tx))
    #target = (calcX(targetCoord, TxCoord, Tx), calcY(targetCoord, TxCoord, Tx))
    
    #Place objects
    # grid = placeObjects(grid, Tx, Rx1, Rx2, Rx3, target)

    #calculate true ranges, in practical test this will be given as the output of the SDR
    r1 = range1
    r2 = range2
    r3 = range3

    #Perform Calculations
    result = bruteForce(grid, Tx, Rx1, Rx2, Rx3, r1, r2, r3)

    #convert back to GPS coord
    result = cartesianToLatLong(result, Tx, TxCoord)
    #print(result)
    #print(grid)
    
    return result

def main():

    #Determine size of grid (metres), create grid
    xRange = 20
    yRange = 20
    grid = createGrid(xRange, yRange)

    #Transmitter drone always centre of grid
    Tx = (xRange/2, yRange/2)
    
    #Set conditions for localisation testing
    TxCoord = GPSCoord(-43.52051, 172.58310)

    Rx1Coord = GPSCoord(-43.52046, 172.58305)
    Rx2Coord = GPSCoord(-43.52046, 172.58315)
    Rx3Coord = GPSCoord(-43.52056, 172.58305)

    targetCoord = GPSCoord(-43.52059, 172.58315)

    #Map from GPS to grid locations
    Rx1 = (calcX(Rx1Coord, TxCoord, Tx), calcY(Rx1Coord, TxCoord, Tx))
    Rx2 = (calcX(Rx2Coord, TxCoord, Tx), calcY(Rx2Coord, TxCoord, Tx))
    Rx3 = (calcX(Rx3Coord, TxCoord, Tx), calcY(Rx3Coord, TxCoord, Tx))
    target = (calcX(targetCoord, TxCoord, Tx), calcY(targetCoord, TxCoord, Tx))
    
    #Place objects
    grid = placeObjects(grid, Tx, Rx1, Rx2, Rx3, target)

    #calculate true ranges, in practical test this will be given as the output of the SDR
    r1 = findNorm(Tx, target) + findNorm(Rx1, target)
    r2 = findNorm(Tx, target) + findNorm(Rx2, target)
    r3 = findNorm(Tx, target) + findNorm(Rx3, target)

    #Perform Calculations
    result = bruteForce(grid, Tx, Rx1, Rx2, Rx3, r1, r2, r3)

    #convert back to GPS coord
    result = cartesianToLatLong(result, Tx, TxCoord)
    print(result)
    print(grid)


if __name__ == "__main__":
    main()
