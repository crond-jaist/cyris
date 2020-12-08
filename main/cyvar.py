#!/usr/bin/python
#
# Variables for Cy series
#

import urllib
import string

class CyVarBase(string.Template):
    delimiter = '@'

class CyVarForm:
    def __init__(self, formsource):
        self.formbackup = formsource
        self.form = CyVarBase(formsource)
        self.dict = {}

    # entry dictionary enititis 1 or many by dictionary style
    def entry1(self, key, val):
        self.dict[key] = val

    def entrymany(self, **kwargs):
        for k,v in kwargs.items():
            self.dict[k] = v

    # output form content with dictionary values
    def output(self):
        return self.form.substitute(self.dict)

    def safe_output(self):
        return self.form.safe_substitute(self.dict)

    # print contents
    def dump(self):
        print "form |"+self.formbackup+"|"
        for k in sorted(self.dict.keys()):
            print "  {0:<16} {1:<16}".format(k,str(self.dict[k]))

class CyVarBox:
    def __init__(self):
       self.dict = {}

    # entry dictionary enititis 1 or many by dictionary style
    def entry1(self, key, val):
        self.dict[key] = val

    def entrymany(self, **kwargs):
        for k,v in kwargs.items():
            self.dict[k] = v

    # output form content with dictionary values
    def project(self, source, safe=0):
        box = CyVarBase(source)
        if(safe==0):
            rv  = box.substitute(self.dict)
        else:
            rv  = box.safe_substitute(self.dict)
        return rv

    def safe_project(self, source):
        return self.project(source, safe=1)

    def project_URL(self, source, safe=0):
        owr = x
        if "%" in x:
            orw = urllib.unquote(owr)
            crw = self.project(orw, safe)
            cwr = urllib.quote(crw)
        else:
            cwr = owr
        return cwr

    def safe_project_URL(self, source):
        return self.project_URL(source, safe=1)

    def project_URLchunks(self, source, safe=0):
        parts = []
        for x in source.split(" "):
            owr = x
            if "%" in x:
                orw = urllib.unquote(owr)
                crw = self.project(orw, safe)
                cwr = urllib.quote(crw)
            else:
                cwr = owr
            parts.append(cwr)
        return " ".join(parts)

    def safe_project_URLchunks(self, source):
        return self.project_URLchunks(source, safe=1)
     

###
### TEST CODE
###
if __name__ == '__main__':

   form = CyVarBase('cr@crid,ins@incid,@guestname,@guestindex')
   a1   = form.substitute(crid='3', incid='1', guestname="desktop", guestindex="1")
   print "a1  ",a1

   v  = CyVarForm('cr@crid,ins@incid,@guestname,@guestindex\n@{incid}name')
   v.entry1("guestname","websrv")
   v.entrymany(crid=4,incid=3)
   v.dump()
   b1 = v.safe_output()
   print "b1  ",b1

   v.entry1("guestindex","8")
   v.dump()
   b1 = v.output()
   print "b1  ",b1

   qbox = CyVarBox()
   qbox.entry1("name","orange")
   mixin = "abc def %40name ghi"
   mixou = qbox.safe_project(mixin)
   print "mixin |"+mixin+"|"
   print "mixou |"+mixou+"|"
   mixin = "abc def %40name ghi"
   mixou = qbox.safe_project_URLchunks(mixin)
   print "mixin |"+mixin+"|"
   print "mixou |"+mixou+"|"





