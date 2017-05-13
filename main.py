import mysql.connector

"""
TODO
пустая строка в конце файла
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

def get_r(paramLine, fromId, toId):
    return paramLine["r"][fromId:toId]

def isPropertyConst(paramVarLines, propertyGetter, *args):
    """
    Checks that in each line in paramVarLines contains
    at least one variation, for which propertyGetter remains constant (for all lines)
    """
    propertyVal = None
    for paramVarLine in paramVarLines:
        for paramLine in paramVarLine:
            if propertyVal is None:
                propertyVal = propertyGetter(paramLine, *args)
            elif propertyVal != propertyGetter(paramLine, *args):
                return False
    return True

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

    Rrk_isConst = isPropertyConst(monoAccLines, get_R_minus_rk) and isPropertyConst(varAccLines, get_R_minus_rk)
    k_isConst = isPropertyConst(monoAccLines, get_k) and isPropertyConst(varAccLines, get_k)

    if Rrk_isConst:
        if k_isConst:
            r_isConst = isPropertyConst(monoAccLines, get_r, 0, -1) and isPropertyConst(varAccLines, get_r, 0, -1)
            if r_isConst:
                return 4
            else:
                # something went wrong
                assert(False)
        else:
            return 5
    else:
        if k_isConst:
            r_isConst = isPropertyConst(monoAccLines, get_r, 1, -1) and isPropertyConst(varAccLines, get_r, 1, -1)
            if r_isConst:
                return 3
            else:
                return 2
        else:
            return 1

def main(fileName):
    with open(fileName, 'r') as poemFile:
        poem = readPoem(poemFile)
        print(poem)

    poemAccentCodes = []
    for line in poem:
        poemAccentCodes.append(getLineAccentCodes(line))

    poemParams = getPoemParametrised(poemAccentCodes)

    condNumber = selectMetricCondition(poemParams)

    for lineParams in poemParams:
        print(lineParams)

    print(condNumber)

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
