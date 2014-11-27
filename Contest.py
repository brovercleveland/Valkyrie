#! /usr/bin/env python
import re
import string
import collections
from random import shuffle, seed
import copy
import threading
from operator import attrgetter

def loadValues(valueFile):
  valDict = {}
  with open(valueFile) as vf:
    for pair in vf:
      try:
        valDict[pair[0].lower()] = float(re.search(r'\d+', pair).group())
      except:
        continue
  return valDict

def getFrequencies(wordFile):
  startingDict = {}
  endingDict = {}
  for letter in string.ascii_lowercase:
    startingDict[letter] = 0
    endingDict[letter] = 0
  with open(wordFile) as wf:
    for wordLine in wf:
      wordLine = wordLine.strip('\n\r').lower()
      startingDict[wordLine[0]]+=1
      endingDict[wordLine[-1]]+=1
  return startingDict, endingDict

class Word:
  word = None
  val = None
  connectivity = None
  quality = None
  connectors = None

  def __init__(self, wordString, valDict, startingDict, endingDict):
    self.word = wordString.strip('\n\r').lower()
    self.getValue(valDict)
    self.connectors = self.word[0]+self.word[-1]
    self.connectivity = (startingDict[self.word[0]]+endingDict[self.word[-1]])/4000.0
    self.quality = self.connectivity-abs(self.val/10.0)

  def getValue(self, valDict):
    if len(self.word) != 4: Exception('word '+self.word+' is not 4 letters!')
    lv1 = valDict[self.word[0]]
    lv2 = valDict[self.word[1]]
    lv3 = valDict[self.word[2]]
    lv4 = valDict[self.word[3]]
    self.val = (lv1-lv2)*lv3/lv4

class Sequence:
  seq = []
  num = len(seq)
  denom = 0
  val = 0

  def append(self, word):
    self.seq.append(word.word)
    self.num = len(self.seq)
    self.denom += word.val
    self.val = self.num/(abs(self.denom) if (abs(self.denom)>0.5) else 0.5)

  def insert(self,i, word):
    self.seq.insert(i,word.word)
    self.num = len(self.seq)
    self.denom += word.val
    self.val = self.num/(abs(self.denom) if (abs(self.denom)>0.5) else 0.5)

  def __len__(self):
    return len(self.seq)

  def remove(self,wordString, wordDict):
    self.denom -= wordDict[wordString].val
    self.val = self.num/(abs(self.denom) if (self.denom>0.5) else 0.5)
    self.seq.remove(wordString)
    self.num = len(self.seq)
    return wordDict[wordString]

  def clear(self):
    del self.seq[:]
    self.num = len(self.seq)
    self.denom = 0
    self.val = 0



class WordSequencer:
  mySeq = Sequence()
  wordList = []
  wordStringList = []
  wordDict = {}
  def __init__(self, wordFile, valDict, startingDict, endingDict):
    self.loadWords(wordFile, valDict, startingDict, endingDict)

  def loadWords(self, wordFile, valDict, startingDict, endingDict):
    with open(wordFile) as wf:
      for wordLine in wf:
        newWord = Word(wordLine, valDict, startingDict, endingDict)
        self.wordList.append(newWord)
        self.wordStringList.append(wordLine.strip('\n\r').lower())
    self.wordDict = dict(zip(self.wordStringList, self.wordList))

  def checkValid(self):
    uniq = set(self.mySeq.seq)
    if len(uniq) != len(self.mySeq.seq):
      print len(uniq), len(self.mySeq.seq)
      print [x for x, y in collections.Counter(self.mySeq.seq).items() if y > 1]
      raise Exception('WARNING, SEQUENCE NOT UNIQUE')
    for i,wordString in enumerate(self.mySeq.seq):
      if i==0 or i==len(self.mySeq.seq)-1: continue
      else:
        if self.mySeq.seq[i-1][-1] != self.mySeq.seq[i][0]:
          print self.mySeq.seq[i-1], self.mySeq.seq[i]
          raise Exception('WARNING, SEQUENCE FAILS PATTERN')

  def growSequence(self, myFilterList):
    grow = True
    while grow:
      myFilterList.sort(key=lambda x:abs((x.val-self.mySeq.denom)+1.0*x.connectivity),reverse=True)
      for word in myFilterList:
        #print word.word, self.mySeq.seq[-1]
        if word.word[0]==self.mySeq.seq[-1][-1]:
          newWord = myFilterList.pop(myFilterList.index(word))
          self.mySeq.append(word)
          break
      else:
        grow = False

  def pruneSequence(self, myFilterList):
    prune = True
    while prune:
      for i,wordString in enumerate(self.mySeq.seq):
        if i==0 or i==len(self.mySeq.seq)-1 or wordString[0]==wordString[-1]:
          if abs(self.mySeq.denom-self.wordDict[wordString].val)<abs(self.mySeq.denom) and abs(self.mySeq.denom)>0.5:
            myFilterList.append(self.mySeq.remove(wordString, self.wordDict))
            break
      else:
        prune = False

  def growSequenceMore(self, myFilterList, alpha=1.0):
    grow = True
    while grow:
      myFilterList.sort(key=lambda x:abs((x.val-self.mySeq.denom)+alpha*x.connectivity),reverse=True)
      for i,wordString in enumerate(self.mySeq.seq[:]):
        for word in myFilterList:
          if ((i == 0 and word.word[-1]==wordString[0]) or (i!=0 and word.word[-1]==self.mySeq.seq[i][0] and word.word[0]==self.mySeq.seq[i-1][-1])):
            #print word.word[-1], self.mySeq.seq[i][0]
            newWord = myFilterList.pop(myFilterList.index(word))
            self.mySeq.insert(i,word)
            break
      else:
        grow = False

  def makeSequence(self, firstWordString):
    self.mySeq.clear()
    filterList = self.wordList
    firstWord = next(i for i in self.wordList if i.word==firstWordString)
    filterList = [i for i in filterList if i.word != firstWordString]
    self.mySeq.append(firstWord)

    self.growSequence(filterList)

    self.pruneSequence(filterList)

    self.growSequenceMore(filterList)

    self.growSequence(filterList)

    self.growSequenceMore(filterList)

    self.pruneSequence(filterList)

    self.growSequenceMore(filterList, alpha = 10.0)

    self.pruneSequence(filterList)
    print self.mySeq.val, self.mySeq.denom, self.mySeq.num
    self.checkValid()

    return self.mySeq

class runSequencer(threading.Thread):
    def __init__(self, wordList, sequencer):
      super(runSequencer, self).__init__()
      self.wordList = wordList
      self.sequencer = sequencer
      self.bestSeq = Sequence()

    def run(self):
      usedWords = set()
      for wordString in self.wordList:
        if wordString not in usedWords:
          usedWords.add(wordString)
          print wordString
          newSeq = self.sequencer.makeSequence(wordString)
          if newSeq.val > self.bestSeq.val:
            self.bestSeq = copy.copy(newSeq)
          usedWords = usedWords.union(set(newSeq.seq))
          print len(usedWords)
          print 'best', self.bestSeq.val, 'new', newSeq.val

      print self.bestSeq.seq, self.bestSeq.val, self.bestSeq.denom, self.bestSeq.num

if __name__=="__main__":
  startingFreq, endingFreq = getFrequencies('4_letter_words.txt')
  valDict = loadValues('letter_values.txt')
  mySequencer1 = WordSequencer('4_letter_words.txt', valDict, startingFreq, endingFreq)
  #mySequencer2 = WordSequencer('4_letter_words.txt', valDict, startingFreq, endingFreq)
  #mySequencer3 = WordSequencer('4_letter_words.txt', valDict, startingFreq, endingFreq)
  #mySequencer4 = WordSequencer('4_letter_words.txt', valDict, startingFreq, endingFreq)
  #list1 = randomList[0:1000]
  #list2 = randomList[1000:2000]
  #list3 = randomList[2000:3000]
  #list4 = randomList[3000:-1]
  #list1 = randomList[0:5]
  #list2 = randomList[5:10]
  #list3 = randomList[10:15]
  #list4 = randomList[15:20]
  #thread1 = runSequencer(list1, mySequencer1)
  #thread2 = runSequencer(list2, mySequencer2)
  #thread3 = runSequencer(list3, mySequencer3)
  #thread4 = runSequencer(list4, mySequencer4)
  #thread1.start()
#  thread2.start()
#  thread3.start()
#  thread4.start()
  #thread1.join()
#  thread2.join()
#  thread3.join()
#  thread4.join()
  #bestSeq = max([thread1,thread2,thread3,thread4], key=attrgetter('bestSeq.val'))

  randomList = mySequencer1.wordStringList
  seed(8675309)
  shuffle(randomList)

  bestSeq = Sequence()
  usedWords = set()
  for wordString in randomList:
    if wordString not in usedWords:
      usedWords.add(wordString)
      print wordString
      newSeq = mySequencer1.makeSequence(wordString)
      if newSeq.val > bestSeq.val:
        bestSeq = copy.copy(newSeq)
      usedWords = usedWords.union(set(newSeq.seq))
      print len(usedWords)
      print 'best', bestSeq.val, 'new', newSeq.val

  print bestSeq.seq, bestSeq.val, bestSeq.denom, bestSeq.num

