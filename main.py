import math
import mysql.connector

"""
TODO
пустая строка в конце файла
генератор
пустой varCounts
меня \ меня
"""

abc = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
vowels = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"
particles = {"де" : "*",
             "ка" : "*",
             "кое" : "**",
             "кой" : "*",
             "кась" : "*",
             "либо" : "**",
             "нибудь" : "**",
             "с" : "",
             "тка" : "*",
             "тко" : "*",
             "то" : "*",}
masks = [
    ({"mask": ['cC', 'cC'],  "place": 0, "step": 2}, "ямб"),
    ({"mask": ['cC', 'cCc'], "place": 0, "step": 2}, "ямб"),
    ({"mask": ['cCc', 'Cc'], "place": 0, "step": 2}, "ямб"),

    ({"mask": ['Cc', 'Cc'], "place": 0, "step": 2}, "хорей"),

    ({"mask": ['Cc', 'cC'],   "place": 0, "step": 3}, "дактиль"),
    ({"mask": ['Cc', 'cCc'],  "place": 0, "step": 3}, "дактиль"),
    ({"mask": ['Cc', 'cCcc'], "place": 0, "step": 3}, "дактиль"),

    ({"mask": ['cCc', 'cC'],  "place": 0, "step": 3}, "амфибрахий"),
    ({"mask": ['cCc', 'cCc'], "place": 0, "step": 3}, "амфибрахий"),

    ({"mask": ['cCc', 'cC'], "place": 2, "step": 3}, "анапест"),
    ({"mask": ['Cc', 'cCc'], "place": 2, "step": 3}, "анапест"),
]
perfectMasks = {
    "ямб": "cC",
    "хорей": "Cc",
    "дактиль": "Ccc",
    "амфибрахий": "cCc",
    "анапест": "ccC",
}
conn = mysql.connector.connect(host='localhost', database='accents', user='root', password='1234')


def getSyllablesCount(word):
    count = 0
    for latter in word:
        if latter in vowels:
            count += 1
    return count


def getLineAccentCodes(line):
    """
    :return: Returns list of all possible accentuations for line
    as lists of word codes in cC notation
    """
    allLineCodes = []
    accentSequences = getAccentSeqeunces(line)
    for accentSeq in accentSequences:
        lineCode = []
        assert(len(accentSeq) == len(line))

        for wordId in range(len(line)):
            word = line[wordId]

            accentId = accentSeq[wordId]
            syllCount = getSyllablesCount(word)

            vowelId = -1
            asterisksBefore = 0
            asterisksAfter = 0
            for latter in reversed(word):
                if latter in vowels:
                    vowelId += 1
                if latter == '*':
                    if vowelId < accentId:
                        asterisksAfter += 1
                    else:
                        asterisksBefore += 1

            syllsBefore = (syllCount - accentId - 1) + asterisksBefore
            syllsAfter = accentId + asterisksAfter

            wordCode = (syllsBefore * 'c') + 'C' + (syllsAfter * 'c')
            lineCode.append(wordCode)
        allLineCodes.append(lineCode)
    return allLineCodes


def getPoemParametrised(poemAccentCodes):
    """
    Translates poem line codes list into list of dictionaries
    containing line code and some useful line parameters
    """
    parametrised = []
    for lineCodesVariations in poemAccentCodes:
        lineParamsVariations = []
        for lineCode in lineCodesVariations:
            lineCodeMerged = "".join(lineCode)
            k = 0
            r = [0]
            R = len(lineCodeMerged)
            for syllCode in lineCodeMerged:
                if syllCode == 'c':
                    r[k] += 1
                elif syllCode == 'C':
                    k += 1
                    r.append(0)
                else:
                    assert(False)
            lineParamsVariations.append({"word_codes": lineCode, "k": k, "r": r, "R": R})
        parametrised.append(lineParamsVariations)
    return parametrised

def get_R_minus_rk(paramLine):
    R = paramLine["R"]
    r = paramLine["r"]
    k = paramLine["k"]
    return R - r[k]

def get_k(paramLine):
    return paramLine["k"]

def get_r(paramLine):
    return paramLine["r"]

def get_r1_ifConst(paramLine):
    r = get_r(paramLine)[1: -1]
    if not all([r[i] == r[0] for i in range(len(r))]):
        return None # in case of non const r[i]
    return r[1]

def isPropertyConst(paramVarLines, propertyGetter):
    """
    Checks that in each line in paramVarLines contains
    at least one variation, for which propertyGetter remains constant (for all lines)
    """
    propertyVal = None
    varCounts = [len(line) for line in paramVarLines]
    for varSet in genVarSets(varCounts):
        propIsConst = True
        for lineId, varLine in enumerate(paramVarLines):
            paramLine = varLine[varSet[lineId]]
            if propertyVal is None:
                propertyVal = propertyGetter(paramLine)
                if propertyVal is None:
                    return False, None  # in case of non const r[i]
            elif propertyVal != propertyGetter(paramLine):
                propIsConst = False
        if propIsConst:
            return True, propertyVal
    return False, None

def getMonoAccentedLines(poem):
    monoAccLines = []
    for line in poem:
        if len(line) == 1:
            monoAccLines.append(line)
    return monoAccLines


def selectMetricCondition(varAccLines):
    """
    Selects which metric condition is correct for this poem
    :return: condition number from 1 to 5
    """
    monoAccLines = getMonoAccentedLines(varAccLines)

    mono_RrkConst, mono_Rrk = isPropertyConst(monoAccLines, get_R_minus_rk)
    var_RrkConst,  var_Rrk  = isPropertyConst(varAccLines,  get_R_minus_rk)
    mono_kConst,   mono_k   = isPropertyConst(monoAccLines, get_k)
    var_kConst,    var_k    = isPropertyConst(varAccLines,  get_k)

    selectedParams = {"Rrk": mono_Rrk or var_Rrk, "k": mono_k or var_k, "r1": None}

    if mono_RrkConst and var_Rrk:
        if mono_kConst and var_kConst:
            mono_rConst, mono_r = isPropertyConst(monoAccLines, get_r1_ifConst)
            var_rConst,  var_r  = isPropertyConst(varAccLines, get_r1_ifConst)
            if mono_rConst or var_rConst:
                selectedParams["r1"] = mono_r or var_r
                return 4, selectedParams
            else:
                # something went wrong
                assert(False)
        else:
            return 5, selectedParams
    else:
        if mono_kConst and var_kConst:
            mono_rConst, mono_r = isPropertyConst(monoAccLines, get_r1_ifConst)
            var_rConst,  var_r  = isPropertyConst(varAccLines, get_r1_ifConst)
            if mono_rConst or var_rConst:
                selectedParams["r1"] = mono_r or var_r
                return 3, selectedParams
            else:
                return 2, selectedParams
        else:
            return 1, selectedParams

def genVarSets(varCounts):
    if len(varCounts) == 0:
        return []

    if len(varCounts) == 1:
        return [[i] for i in range(varCounts[0])]
    else:
        return product(genVarSets([varCounts[0]]), genVarSets(varCounts[1:]))

def processFirstCond(varAccLines):
    varCounts = [len(line) for line in varAccLines]
    for varSet in genVarSets(varCounts):
        deltas = []
        for line1Id, line1 in enumerate(varAccLines):
            var1Id = varSet[line1Id]
            Rrk1 = get_R_minus_rk(line1[var1Id])
            for line2Id, line2 in enumerate(varAccLines):
                var2Id = varSet[line2Id]
                Rrk2 = get_R_minus_rk(line2[var2Id])
                deltas.append(abs(Rrk1 - Rrk2))

        if all([(delta % 2 == 0) for delta in deltas]):
            return 1
        if all([(delta % 3 == 0) for delta in deltas]):
            return 2
        if all([(delta % 5 == 0) for delta in deltas]):
            return 3
    return 0


def processSecondCond(varAccLines, selParams):
    condMatched = {0}
    geqThen4 = False
    geqThen3 = False
    geqThen2 = False
    geqThen1 = False
    lssThen1 = False
    for paramVarLine in varAccLines:
        for paramLine in paramVarLine:
            k = get_k(paramLine)
            if k != selParams["k"]:
                continue
            r = get_r(paramLine)[1:-1]
            for i in range(len(r)):
                if r[i] >= 4:
                    geqThen4 = True
                if r[i] >= 3:
                    geqThen3 = True
                if r[i] >= 2:
                    geqThen2 = True
                if r[i] >= 1:
                    geqThen1 = True
                else:
                    lssThen1 = True

    if geqThen4:
        condMatched.add(1)
    if not lssThen1 and not geqThen4:
        condMatched.add(2)
    if lssThen1 and not geqThen3:
        condMatched.add(3)
    if not lssThen1 and not geqThen3:
        condMatched.add(4)
    if not geqThen1:
        condMatched.add(5)

    return max(condMatched)


def processFourthCond(varAccLines, selParams):
    for paramVarLine in varAccLines:
        for paramLine in paramVarLine:
            Rrk = get_R_minus_rk(paramLine)
            if Rrk != selParams["Rrk"]:
                continue
            k = get_k(paramLine)
            if k != selParams["k"]:
                continue
            r = get_r(paramLine)
            if r[1] != selParams["r1"]:
                continue

            if r[1] == 1:
                if r[0] == 0:
                    return 1
                elif r[0] == 1:
                    return 2
            if r[1] == 2:
                if r[0] == 0:
                    return 3
                elif r[0] == 1:
                    return 4
                elif r[0] == 2:
                    return 5
            if r[1] == 3:
                if r[0] == 0:
                    return 6
                elif r[0] == 1:
                    return 7
                elif r[0] == 2:
                    return 8
                elif r[0] == 3:
                    return 9
            if r[1] == 4:
                if r[0] == 0:
                    return 10
                elif r[0] == 1:
                    return 11
                elif r[0] == 2:
                    return 12
                elif r[0] == 3:
                    return 13
                elif r[0] == 4:
                    return 14
            return 0

def findAll(str, subStr):
    start = 0
    while True:
        start = str.find(subStr, start)
        if start == -1:
            return
        yield start
        start += len(subStr)

def getMetricbyMask(mask):
    for key, val in masks:
        if key == mask:
            return val

def genLineMask(maskPattern, length):
    count = math.ceil(length / len(maskPattern))
    return (maskPattern * count)[:length]

def processFifthCond(varAccLines, selParams):
    monoAccLines = getMonoAccentedLines(varAccLines)

    matchedMasks = []
    for mask, metric in masks:
        maskCode = "|".join([""] + mask["mask"] + [""])
        for paramLine in monoAccLines:
            wordCodes = paramLine[0]["word_codes"]
            lineCode = "|".join([""] + wordCodes + [""])
            ocurances = []
            for ocur in findAll(lineCode, maskCode):
                if (ocur - mask["place"]) % mask["step"] == 0:
                    ocurances.append(ocur)
            if len(ocurances) > 0:
                matchedMasks.append(mask)

    maskErrors = []
    for mask in matchedMasks:
        Rrk = selParams["Rrk"]
        perfectMask = perfectMasks[getMetricbyMask(mask)]
        lineMask = genLineMask(perfectMask, Rrk)

        maxError = 0
        for varLine in varAccLines:
            minVarError = None
            for paramLine in varLine:
                lineCode = "".join(paramLine["word_codes"])
                varError = 0
                for i in range(Rrk):
                    if lineMask[i] != lineCode[i]:
                        varError += 1
                if minVarError is None:
                    minVarError = varError
                minVarError = min(minVarError, varError)
            maxError = max(maxError, minVarError)
        maskErrors.append((mask, maxError))

    bestMask = None
    minError = None
    for mask, error in maskErrors:
        print("mask: {}, error: {}, type: {}".format(mask, error, getMetricbyMask(mask)))
        if bestMask is None:
            bestMask = mask
            minError = error
        if error < minError:
            bestMask = mask
            minError = error

    perfectMask = perfectMasks[getMetricbyMask(bestMask)]
    lineMask = genLineMask(perfectMask, selParams["Rrk"])
    footStep = lineMask.count("C")
    return getMetricbyMask(bestMask), footStep


def main(fileName):
    with open(fileName, 'r') as poemFile:
        poem = readPoem(poemFile)
        print(poem)

    poemAccentCodes = []
    for line in poem:
        poemAccentCodes.append(getLineAccentCodes(line))

    #for line in poemAccentCodes:
    #    print(line)

    varParamizedPoem = getPoemParametrised(poemAccentCodes)

    for lineParams in varParamizedPoem:
        print(lineParams)

    condNumber, selParams = selectMetricCondition(varParamizedPoem)

    print("condNumber {}".format(condNumber))

    subCond = 0
    if condNumber == 1:
        subCond = processFirstCond(varParamizedPoem)
    elif condNumber == 2:
        subCond = processSecondCond(varParamizedPoem, selParams)
    elif condNumber == 4:
        subCond = processFourthCond(varParamizedPoem, selParams)
    elif condNumber == 5:
        subCond, footStep = processFifthCond(varParamizedPoem, selParams)
        print(footStep)

    print("subCond {}".format(subCond))

def clearSpeciallChars(line):
    clearLine = ""
    for i in range(0, len(line)):
        char = line[i]
        if char in abc or char == " ":
            clearLine += char
        elif char == "-":
            if (i > 0 and line[i-1] != " ") and (i < len(line) - 1 and line[i+1] != " "):
                clearLine += char

    return clearLine


def splitToWords(line):
    words = line.split(" ")

    while "" in words:
        words.remove("")

    cleanWords = []
    for word in words:
        if not any([(latter in vowels) for latter in word]):
            # no vowels in word, skip it
            continue

        if "-" in word:
            parts = word.split("-")
            assert (len(parts) == 2)

            hasParticle = False
            if parts[0] in particles:
                hasParticle = True
                parts[0] = particles[parts[0]]

            if parts[1] in particles:
                hasParticle = True
                parts[1] = particles[parts[1]]

            if hasParticle:
                cleanWords.append("".join(parts))
            else:
                cleanWords.append(parts[0])
                cleanWords.append(parts[1])
        else:
            cleanWords.append(word)

    return cleanWords

def readPoem(file):
    rawLines = [line[:-1] for line in file.readlines()]

    poem = []
    for line in rawLines:
        line = clearSpeciallChars(line)
        lineWords = splitToWords(line)
        if len(lineWords) > 0:
            poem.append(splitToWords(line))

    return poem


def parseWord(word):
    word = word.replace("*", "")

    global conn
    cursor = conn.cursor()  # обращение коннектору
    cursor.execute('SELECT accent FROM accent_aot WHERE word_form="' + word + '"')
    rows = cursor.fetchall()
    uniq = set([row[0] for row in rows])
    if len(uniq) == 0 or 255 in uniq:
        print("[ERROR] Word \"{}\" is not in accents DB (or has no accent)".format(word))
        return set(range(getSyllablesCount(word)))
    return uniq


def getAccentSeqeunces(line):
    """
    Generates all possible sequences of accentuation for given line
    :return: list of sequences (as lists of accents)
    """
    if len(line) == 1:
        return [[i] for i in parseWord(line[0])]
    else:
        return product(getAccentSeqeunces([line[0]]), getAccentSeqeunces(line[1:]))


def product(heads, tails):
    """
    Descartes product of two lists
    :param heads: list of single-element lists
    :param tails: list of lists
    :return: list of products [heads[i] + tails[j] forall i,j]
    """
    products = []
    for head in heads:
        for tail in tails:
            products.append(head + tail)
    return products



main("poem.txt")
# print(parseWord('чудное'))
