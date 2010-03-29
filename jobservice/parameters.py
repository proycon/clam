###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Parameter classes --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

import lxml
from lxml import etree as ElementTree
from StringIO import StringIO


def parameterfromxml(node):
    if not isinstance(node,ElementTree._Element):
        node = ElementTree.parse(StringIO(node)).getroot() #verify this works? (may need .root?) 
    if node.tag in globals():
        id = ''
        paramflag = ''
        name = ''
        description = ''
        kwargs = {}
        for attrib, value in node.attrib.items():
            if attrib == 'id':
                id = value
            elif attrib == 'paramflag':
                paramflag = value       
            elif attrib == 'name':
                name = value
            elif attrib == 'description':
                description = value
            else:
                kwargs[attrib] = value
        if mask:
            return globals()[node.tag](id, paramflag, name, description, **kwargs) #return parameter instance
    else:
        raise Exception("No such parameter exists: " + node.tag)

    pass

class AbstractParameter(object):
    def __init__(self, id, paramflag, name, description, **kwargs):
        self.id = id #a unique ID
        self.paramflag = paramflag #the parameter flag passed to the command (include a trailing space!)        
        self.name = name #a representational name
        self.description = description

        self.value = False
        self.kwargs = kwargs #make a copy for XML generation later
        self.guest = True
        self.required = False
        self.nospace = False
        for key, value in kwargs.items():
            if key == 'guest': 
                self.guest = value  #Show parameter for guests?
            elif key == 'required': 
                self.required = value  #Show parameter for guests?    
            elif key == 'force':
                #if this argument is set, the ones with the following IDs should as well
                self.force = value
            elif key == 'restrict':
                #if this argument is set, the ones with the following IDs can not
                self.force = value
            elif key == 'nospace':
                #no space between option and it's value
                self.nospace = value

    def validate(self,value):
        return True

    def compilearg(self, value):
        if self.paramflag[-1] == '=' or self.nospace:
            sep = ''
        else:
            sep = ' '
        return self.paramflag + sep + value

    def xml(self):
        xml = "<" + self.__class__.__name__
        xml += ' id="'+self.id + '"'
        xml += ' name="'+self.name + '"'
        xml += ' description="'+self.description + '"'
        for key, v in self.kwargs.items():    
            if isinstance(v, bool):
                xml += ' ' + key + '="' + str(int(v))+ '"'                    
            elif isinstance(v, list):
                xml += ' ' + key + '="'+",".join(v)+ '"'        
            else:
                xml += ' ' + key + '="'+v+ '"'        
        if self.value:
            xml += ' value="'+self.value + '"'
        xml += " />"
        return xml

    @staticmethod
    def xsl():
        #TODO: implement
        xml = ''
        return xml
        


    def set(self, value):
        if self.validate(value):
            self.value = value
            return True
        else:
            return False

        
class BooleanParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description, **kwargs):
        super(BooleanParameter,self).__init__(id,paramflag,name,description, **kwargs)
        
        #defaultsisisntance
        self.reverse = False
        for key, value in kwargs.items():
            if key == 'reverse': 
                self.reverse = value  #Option gets outputted when option is NOT checked


    def compilearg(self, value):
        if self.reverse: value = not value
        if value:
            return self.paramflag  
        else:
            return ""



class StringParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description, **kwargs):
        super(StringParameter,self).__init__(id,paramflag,name,description, **kwargs)

        #defaults
        self.value = ""
        self.maxlength = 0 #unlimited
        for key, value in kwargs.items():
            if key == 'default': 
                self.value = value  
            elif key == 'maxlength': 
                self.maxlength = int(value)

    def validate(self,value):
        return ((self.maxlength == 0) or(len(value) <= self.maxlength))

    def compilearg(self, value):
        if value.find(" ") >= 0 or value.find(";") >= 0:            
            value = value.replace('"',r'\"')
            value = '"' + value + '"' #wrap in quotes
        super(StringParameter,self).compilearg(value)


class ChoiceParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description, choices, **kwargs):
        super(ChoiceParameter,self).__init__(id,paramflag,name,description, **kwargs)

        #defaults
        self.delimiter = ","
        self.choices = [] #list of key,value tuples
        for x in choices:
            if not isinstance(x,tuple) or len(x) != 2:
                self.choices.append( (x,x) ) #list of two tuples
            else:
                self.choices.append(x) #list of two tuples
        self.value = self.choices[0][0] #first choice is default
                
        for key, value in kwargs.items():
            if key == 'default': 
                self.value = value  
            elif key == 'multi': 
                self.multi = value #boolean 
            elif key == 'showall': 
                self.showall = value #show all options at once (radio instead of a pull down) 
            elif key == 'delimiter': 
                self.delimiter = value #char

    def validate(self,values):
        if not isinstance(values,list):
            values = [values]
        for v in values:
            if not v in [x[0] for x in self.choices]:
                return False
        return True



    def compilearg(self, values): 
        if isinstance(values,list):
            value = self.delimiter.join(values)
        else:
            value = values
        if value.find(" ") >= 0:
            value = '"' + value + '"' #wrap all in quotes
        super(ChoiceParameter,self).compilearg(value)

    def xml(self):
        xml = "<" + self.__class__.__name__
        xml += ' id="'+self.id + '"'
        xml += ' name="'+self.name + '"'
        xml += ' description="'+self.description + '"'
        for key, value in self.kwargs.items():    
            if key != 'choices' and key != 'default':
                if isinstance(value, bool):
                    xml += ' ' + key + '="' + str(int(value))+ '"'                    
                elif isinstance(value, list):
                    xml += ' ' + key + '="'+",".join(value)+ '"'        
                else:
                    xml += ' ' + key + '="'+value+ '"'        
        xml += ">"
        for key, value in self.choices:
            if self.value == key:
                xml += " <choice id=\""+key+"\" selected=\"1\">" + value + "</choice>"
            else:
                xml += " <choice id=\""+key+"\">" + value + "</choice>"
        xml += "</" + self.__class__.__name__ + ">"
        return xml

class TextParameter(StringParameter): #TextArea based
    def __init__(self, id, paramflag, name, description, **kwargs):
        super(TextParameter,self).__init__(id,paramflag,name,description, **kwargs)

        

class IntegerParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description, **kwargs):
        super(IntegerParameter,self).__init__(id,paramflag,name,description, **kwargs)
        
        
        #defaults
        self.default = 0
        self.minvalue = 0
        self.maxvalue = 0 #unlimited
        for key, value in kwargs.items():
            if key == 'default': 
                self.value = int(value)
            elif key == 'minvalue': 
                self.minvalue = int(value)
            elif key == 'maxvalue': 
                self.maxvalue = int(value)

    def validate(self, value):
        try:
            value = int(value)
        except:
            return False
        return  ((self.maxvalue < self.minvalue) or ((value >= self.minvalue) and (value <= self.maxvalue)))


class FloatParameter(AbstractParameter):
    def __init__(self, id, paramflag, name, description, **kwargs):
        super(FloatParameter,self).__init__(id,paramflag,name,description, **kwargs)
                
        #defaults
        self.default = 0
        self.minvalue = 0
        self.maxvalue = -1 #unlimited if maxvalue < minvalue
        for key, value in kwargs.items():
            if key == 'default': 
                self.value = float(value)
            elif key == 'minvalue': 
                self.minvalue = float(value)
            elif key == 'maxvalue': 
                self.maxvalue = float(value)

    def validate(self, value):
        try:
            value = float(value)
        except:
            return False
        return  ((self.maxvalue < self.minvalue) or ((value >= self.minvalue) and  (value <= self.maxvalue)))
        

