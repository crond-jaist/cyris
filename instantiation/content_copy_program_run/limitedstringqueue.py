#!/usr/bin/python
#
# LimitedStringQueue:
#   - store result string lines as queue
#   - if orient is 0, store first several lines
#   - if orient is 1, store last several lines
#   - "several" is exprain by qnummax
#
# typical example:
#       x = LimitedStringQueue()
#       x.push("a")
#       x.push("b")
#       ...
#       x.dump()
#       x.dumpconcat()
#       x.dumpconcaturlenc()
#

import urllib

class LimitedStringQueue:
    def __init__(self, xqorient=0, xqnummax=10, xqelelenmax=10):
        self.q = []
        self.qorient = xqorient
        self.qnummax = xqnummax
        self.qelelenmax = xqelelenmax

    def printprop(self,xprefix=""):
        if(xprefix==""):
            pre = ""
        else:
            pre = xprefix + ": "
        print pre+"orient    ",self.qorient
        print pre+"num*      ",len(self.q)
        print pre+"nummax    ",self.qnummax
#       print pre+"elelenmax ",self.qelelenmax

    def clear(self):
        self.q = []

    def push(self, x):
#        print self.qorient," ",len(self.q)," vs ",self.qnummax
        if(self.qorient==0):
            if(len(self.q)<self.qnummax):
                self.q.append(x)
        elif(self.qorient==1):
            if(len(self.q)>=self.qnummax):
                self.q.pop(0)
            self.q.append(x)
        else:
            self.q.append(x)
    
    def dump(self):
        for x in self.q:
            print x

    def dumpwc(self):
        i = 0
        for x in self.q:
            print i,x
            i = i + 1

    def dumpconcat(self,xprefix="",xsep=""):
        i = 0
        cont = ""
        for x in self.q:
            if(xsep==""):
                cont = cont + x
            else:
                if(i==0):
                    cont = x
                else:
                    cont = cont + xsep + x
            i = i + 1
        if(xprefix==""):
            print cont
        else:
            print xprefix,cont

    def dumpconcaturlenc(self,xprefix="",xsep=""):
        i = 0
        cont = ""
        for x in self.q:
            if(xsep==""):
                cont = cont + x
            else:
                if(i==0):
                    cont = x
                else:
                    cont = cont + xsep + x
            i = i + 1
        if(xprefix==""):
            print urllib.quote(cont)
        else:
            print xprefix,urllib.quote(cont)


    def concat(self,xsep=""):
        i = 0
        cont = ""
        for x in self.q:
            if(xsep==""):
                cont = cont + x
            else:
                if(i==0):
                    cont = x
                else:
                    cont = cont + xsep + x
            i = i + 1
        return cont

    def concaturlenc(self,xsep=""):
        i = 0
        cont = ""
        for x in self.q:
            if(xsep==""):
                cont = cont + x
            else:
                if(i==0):
                    cont = x
                else:
                    cont = cont + xsep + x
            i = i + 1
        return urllib.quote(cont)

###
### TEST CODE
###
if __name__ == '__main__':

    q1 = LimitedStringQueue()
    q1.push("a")
    q1.push("b")
    q1.push("c")
    q1.push("d")
#    q1.dumpwc()

    q2 = LimitedStringQueue(xqnummax=3)
    q2.push("a")
    q2.push("b")
    q2.push("c")
    q2.push("d")
#    q2.dumpwc()

    q3 = LimitedStringQueue(xqnummax=3,xqorient=1)
    q3.push("a")
    q3.push("b")
    q3.push("c")
    q3.push("d")
#    q3.dumpwc()

    q1.printprop(xprefix="q1")
    q2.printprop(xprefix="q2")
    q3.printprop(xprefix="q3")

    q1.dumpconcat()
    q2.dumpconcat(xprefix="q2")
    q3.dumpconcat(xprefix="q3",xsep="|")
    q3.dumpconcaturlenc(xprefix="q3-urlenc",xsep="|")
    q3.dumpconcaturlenc(xprefix="q3-urlenc",xsep="\n")

    print "q3-urlenc",q3.concaturlenc(xsep="\n")," <- print w/o dump*"

