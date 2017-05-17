import operator
from enum import Enum

import math

import diplom


class Metric(Enum):
    IAMB = "ямб"
    CHOREE = "хорей"
    DACTYL = "дактиль"
    AMPHIBRACH = "амфибрахий"
    ANAPAEST = "анапест"
    DOLNIK = "дольник"
    OTHER = "другой"


footLength = {
    Metric.IAMB: 2,
    Metric.CHOREE: 2,
    Metric.DACTYL: 3,
    Metric.AMPHIBRACH: 3,
    Metric.ANAPAEST: 3,
    Metric.DOLNIK: None,
    Metric.OTHER: None,
}

def getNumVector(ccLine):
    lineVect = []
    for ccWord in ccLine:
        syllCount = len(ccWord)
        for syllId, syllCode in enumerate(ccWord):
            if syllCode == "c":
                lineVect.append(1)
            elif syllCode == "C":
                if syllCount == 1:
                    lineVect.append(2)
                elif syllCount == 2:
                    if syllId == 0:
                        lineVect.append(3)
                    else:
                        lineVect.append(4)
                else:
                    lineVect.append(5)
    return lineVect


def checkFirstCond(line):
    for id, symbCode in enumerate(line):
        if (id + 1) % 2 != 0:
            if symbCode != 1 and symbCode != 2:
                return False
    return True


def checkSecondCond(line):
    for id, symbCode in enumerate(line):
        if (id + 1) % 2 == 0:
            if symbCode != 1 and symbCode != 2:
                return False
    return True


def checkThirdCond(line):
    for id, symbCode in enumerate(line):
        if ((id + 1) - 2) % 3 == 0:
            if symbCode != 1 and symbCode != 2 and symbCode != 3:
                return False
            if (id + 1) % 3 == 0:
                if symbCode != 1 and symbCode != 2 and symbCode != 4:
                    return False
    return True


def checkFourthCond(line):
    for id, symbCode in enumerate(line):
        if ((id + 1) - 1) % 3 == 0:
            if symbCode != 1 and symbCode != 2 and symbCode != 4:
                return False
            if (id + 1) % 3 == 0:
                if symbCode != 1 and symbCode != 2 and symbCode != 3:
                    return False
    return True


def checkFifthCond(line):
    for id, symbCode in enumerate(line):
        if ((id + 1) - 1) % 3 == 0:
            if symbCode != 1 and symbCode != 2 and symbCode != 3:
                return False
            if ((id + 1) - 2) % 3 == 0:
                if symbCode != 1 and symbCode != 2 and symbCode != 4:
                    return False
    return True

def checkSixthCond(line):
    for i in range(len(line)):
        if line[i:i+3] == [1, 1, 1]:
            return False
    return True

def analyse(poemNumVectors):
    metricMatchCounts = {
        Metric.IAMB: 0,
        Metric.CHOREE: 0,
        Metric.DACTYL: 0,
        Metric.AMPHIBRACH: 0,
        Metric.ANAPAEST: 0,
        Metric.DOLNIK: 0,
        Metric.OTHER: 0,
    }

    for varLine in poemNumVectors:
        for line in varLine:
            if checkFirstCond(line):
                metricMatchCounts[Metric.IAMB] += 1
            elif checkSecondCond(line):
                metricMatchCounts[Metric.CHOREE] += 1
            elif checkThirdCond(line):
                metricMatchCounts[Metric.DACTYL] += 1
            elif checkFifthCond(line):
                metricMatchCounts[Metric.AMPHIBRACH] += 1
            elif checkSixthCond(line):
                metricMatchCounts[Metric.ANAPAEST] += 1
            else:
                metricMatchCounts[Metric.OTHER] += 1

    return metricMatchCounts


def countFoot(poemNumVectors, metric):
    footMatchCounts = {}

    for varLine in poemNumVectors:
        for line in varLine:
            footLen = footLength[metric]
            probableFoot = math.floor(len(line) / footLen)
            if probableFoot not in footMatchCounts:
                footMatchCounts[probableFoot] = 0
            footMatchCounts[probableFoot] += 1

    return footMatchCounts


def main(fileName):
    with open(fileName, 'r') as poemFile:
        poem = diplom.readPoem(poemFile)
        print(poem)

    poemCcLInes = []
    for line in poem:
        poemCcLInes.append(diplom.getLineAccentCodes(line))

    poemNumVectors = []
    for ccVarLine in poemCcLInes:
        varVect = []
        for ccLine in ccVarLine:
            varVect.append(getNumVector(ccLine))
        poemNumVectors.append(varVect)

    metricMatchCounts = analyse(poemNumVectors)
    print(metricMatchCounts)
    metric = max(metricMatchCounts.items(), key = operator.itemgetter(1))[0]

    footMatchCounts = countFoot(poemNumVectors, metric)
    foot = max(footMatchCounts.items(), key=operator.itemgetter(1))[0]

    print(metric.value)
    print(foot)

main("poem.txt")

