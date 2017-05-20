import math
import mysql.connector

abc = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

vowels = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"

particles = {"де": "*",
             "ка": "*",
             "кое": "**",
             "кой": "*",
             "кась": "*",
             "либо": "**",
             "нибудь": "**",
             "с": "",
             "тка": "*",
             "тко": "*",
             "то": "*", }

masks = [
    ({"mask": ['cC', 'cC'], "place": 0, "step": 2}, "ямб"),
    ({"mask": ['cC', 'cCc'], "place": 0, "step": 2}, "ямб"),
    ({"mask": ['cCc', 'Cc'], "place": 0, "step": 2}, "ямб"),

    ({"mask": ['Cc', 'Cc'], "place": 0, "step": 2}, "хорей"),
    ({"mask": ['cC', 'cC'], "place": 1, "step": 2}, "хорей"),

    ({"mask": ['Cc', 'cC'], "place": 0, "step": 3}, "дактиль"),
    ({"mask": ['Cc', 'cCc'], "place": 0, "step": 3}, "дактиль"),
    ({"mask": ['Cc', 'cCcc'], "place": 0, "step": 3}, "дактиль"),

    ({"mask": ['cCc', 'cC'], "place": 0, "step": 3}, "амфибрахий"),
    ({"mask": ['cCc', 'cCc'], "place": 0, "step": 3}, "амфибрахий"),

    ({"mask": ['cCc', 'cC'], "place": 1, "step": 3}, "анапест"),
    ({"mask": ['Cc', 'cCc'], "place": 2, "step": 3}, "анапест"),
]

perfectMasks = {
    "ямб": "cC",
    "хорей": "Cc",
    "дактиль": "Ccc",
    "амфибрахий": "cCc",
    "анапест": "ccC",
}

resultCodes = {
    1: {
        1: "неравностопный метрический стих",
        2: "неравностопный метрический стих",
        3: "неравностопный метрический стих",
        0: "дисметрический стих",
    },
    2: {
        1: "неурегулированный {k}-акцентный тонический стих",
        2: "4-сложный {k}-акцентный тактовик",
        3: "3-сложный {k}-акцентный тактовик",
        4: "3-сложный {k}-акцентный дольник",
        5: "2-сложный {k}-акцентный дольник",
    },
    3: {
        0: "неурегулированный {K}-стопный силлабо-тониеский стих"
    },
    4: {
        1: "{k}-стопный хорей",
        2: "{k}-стопный ямб",
        3: "{k}-стопный дактиль",
        4: "{k}-стопный амфибрахий",
        5: "{k}-стопный анапест",
        6: "{k}-стопный пэон-1",
        7: "{k}-стопный пэон-2",
        8: "{k}-стопный пэон-3",
        9: "{k}-стопный пэон-4",
        10: "{k}-стопный пэнтон-1",
        11: "{k}-стопный пэнтон-2",
        12: "{k}-стопный пэнтон-3",
        13: "{k}-стопный пэнтон-4",
        14: "{k}-стопный пэнтон-5",
        0: "многосложный размер",
    },
}


def main(fileName):
    with open(fileName, 'r') as poemFile:
        poem = readPoem(poemFile)

    poemAccentCodes = []
    for line in poem:
        poemAccentCodes.append(getLineAccentCodes(line))

    varParamizedPoem = getPoemParametrised(poemAccentCodes)

    condNumber, selParams = selectMetricCondition(varParamizedPoem)

    subCondNumber = 0
    metric = None
    foot = None
    if condNumber == 1:
        subCondNumber = processFirstCond(varParamizedPoem)
    elif condNumber == 2:
        subCondNumber = processSecondCond(varParamizedPoem, selParams)
    elif condNumber == 4:
        subCondNumber = processFourthCond(varParamizedPoem, selParams)
    elif condNumber == 5:
        metric, foot = processFifthCond(varParamizedPoem, selParams)

    print("")
    if condNumber == 5:
        print("{}-стопный {}".format(foot, metric))
    else:
        print(resultCodes[condNumber][subCondNumber].format(k = selParams["k"]))


def readPoem(file):
    rawLines = file.readlines()

    poem = []
    for line in rawLines:
        line = clearSpeciallChars(line)
        lineWords = splitToWords(line)
        if len(lineWords) > 0:
            poem.append(lineWords)

    return poem


def clearSpeciallChars(line):
    clearLine = ""
    for i in range(0, len(line)):
        char = line[i]
        if char in abc or char == " ":
            clearLine += char
        elif char == "-":
            if (i > 0 and line[i - 1] != " ") and (i < len(line) - 1 and line[i + 1] != " "):
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


def getLineAccentCodes(line):
    """
    :return: Returns list of all possible accentuations for line
    as lists of word codes in cC notation
    """
    allLineCodes = []
    accentSequences = getAccentSeqeunces(line)
    for accentSeq in accentSequences:
        lineCode = []
        assert (len(accentSeq) == len(line))

        for wordId, word in enumerate(line):

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


def getAccentSeqeunces(line):
    """
    Generates all possible sequences of accentuation for given line
    :return: list of sequences (as lists of accents)
    """
    if len(line) == 1:
        return [[i] for i in getAccents(line[0])]
    else:
        return product(getAccentSeqeunces([line[0]]), getAccentSeqeunces(line[1:]))


def getAccents(word):
    """
    Queries accents for given word from DB
    "*" chars are ignored
    :return: set of numbers each denotes stressed syllable 0-based number from last to first
    """
    word = word.replace("*", "")

    global conn
    cursor = conn.cursor()
    cursor.execute('SELECT accent FROM accent_aot WHERE word_form="' + word + '"')
    rows = cursor.fetchall()
    uniq = set([row[0] for row in rows])
    if len(uniq) == 0 or 255 in uniq:
        print("[ERROR] Word \"{}\" is not in accents DB (or has no accent)".format(word))
        return set(range(getSyllablesCount(word)))
    return uniq


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


def getSyllablesCount(word):
    count = 0
    for latter in word:
        if latter in vowels:
            count += 1
    return count


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
                    assert (False)
            lineParamsVariations.append({"word_codes": lineCode, "k": k, "r": r, "R": R})
        parametrised.append(lineParamsVariations)
    return parametrised


def selectMetricCondition(varAccLines):
    """
    Selects which metric condition is correct for this poem
    :return: condition number from 0 to 5 and parameters values wich stays const to satisfy this condition
    """

    RrkIsConst, RrkVal = isPropertyConst(varAccLines, get_R_minus_rk)
    kIsConst, kVal = isPropertyConst(varAccLines, get_k)

    selectedParams = {"Rrk": RrkVal, "k": kVal, "r1": None}

    if RrkIsConst:
        if kIsConst:
            r1IsConst, r1Val = isPropertyConst(varAccLines, get_r1_ifConst)

            if r1IsConst:
                selectedParams["r1"] = r1Val
                return 4, selectedParams
            else:
                return 0, None
        else:
            return 5, selectedParams
    else:
        if kIsConst:
            r1IsConst, r1Val = isPropertyConst(varAccLines, get_r1_ifConst)
            if r1IsConst:
                selectedParams["r1"] = r1Val
                return 3, selectedParams
            else:
                return 2, selectedParams
        else:
            return 1, selectedParams


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


def genVarSets(varCounts):
    """
    Generates all possible sequences of line variations for poem
    :return: list lists of (variation numbers for each line)
    """
    varSet = [0 for i in range(len(varCounts))]
    while True:
        yield varSet

        varSet[0] += 1
        for i, val in enumerate(varSet):
            if val == varCounts[i]:
                if i == len(varSet) - 1:
                    return
                varSet[i] = 0
                varSet[i + 1] += 1


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
        return None  # in case of non const r[i]
    if len(r) == 0:
        return None
    return r[0]


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


def processFifthCond(varAccLines, selParams):
    matchedMasks = []
    for mask, metric in masks:
        for varLine in varAccLines:
            for paramLine in varLine:
                wordCodes = paramLine["word_codes"]
                for ocur in findAll(wordCodes, mask["mask"]):
                    inStrOcur = sum([len(c) for c in wordCodes[0:ocur]])
                    if (inStrOcur - mask["place"]) % mask["step"] == 0:
                        matchedMasks.append(mask)
                        break

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

    metric = getMetricbyMask(bestMask)
    if metric is None:
        return "unknown", -1

    perfectMask = perfectMasks[metric]
    lineMask = genLineMask(perfectMask, selParams["Rrk"])
    footStep = lineMask.count("C")
    return metric, footStep


def findAll(lst, subLst):
    for i in range(len(lst)):
        if lst[i] == subLst[0] and lst[i:i + len(subLst)] == subLst:
            yield i


def getMetricbyMask(mask):
    for key, val in masks:
        if key == mask:
            return val


def genLineMask(maskPattern, length):
    count = math.ceil(length / len(maskPattern))
    return (maskPattern * count)[:length]


conn = mysql.connector.connect(host='localhost', database='accents', user='root', password='1234')
main("poem.txt")
