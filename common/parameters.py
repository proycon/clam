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

from lxml import etree as ElementTree
from StringIO import StringIO

class AbstractParameter(object):
    def __init__(self, id, name, description = '', **kwargs):
        self.id = id #a unique ID
        self.paramflag = None #the parameter flag passed to the command (include a trailing space!) #CHECK: space still necessary?
        self.name = name #a representational name
        self.description = description
        self.error = None                    
        self.value = False
        self.kwargs = kwargs #make a copy for XML generation later
        self.required = False
        self.nospace = False
        self.require = []
        self.forbid = []
        self.allowusers = []
        self.denyusers = []
        self.hasvalue = False
        for key, value in kwargs.items():
            if key == 'allowusers': 
                self.allowusers = value  #Users to allow access to this parameter (If not set, all users have access)
            elif key == 'denyusers': 
                self.denyusers = value   #Users to deny access to this parameter (If not set, nobody is denied)
            elif key == 'value' or key == 'default':
                #set an error message
                self.set(value)
            elif key == 'required': 
                self.required = value  #Mandatory parameter?  
            elif key == 'require':
                #if this argument is set, the ones with the following IDs should as well
                self.require = value
            elif key == 'forbid':
                #if this argument is set, the ones with the following IDs can not
                self.forbid = value
            elif key == 'nospace':
                #no space between option and it's value
                self.nospace = value
            elif key == 'error':
                #set an error message (if you also set a value, make sure this is set AFTER the value is set)
                self.error = value
            elif key == 'flag' or key == 'option' or key == 'paramflag':
                self.paramflag = value
            else:
                raise Exception("Unknown attribute specified for parameter: " + key + "=" + str(value))

    def validate(self,value):
        self.error = None #reset error
        return True

    def compilearg(self, value):
        """This method compiles the parameter into syntax that can be used on the shell, such as for example: --paramflag=value"""
        if self.paramflag and self.paramflag[-1] == '=' or self.nospace:
            sep = ''
        elif self.paramflag:
            sep = ' '
        return self.paramflag + sep + str(value)

    def xml(self, indent = ""):
        """This methods renders an XML representation of this parameter, along with 
        its selected value, and feedback on validation errors"""
        xml = indent + "<" + self.__class__.__name__
        xml += ' id="'+self.id + '"'
        if self.paramflag:
            xml += ' flag="'+self.paramflag + '"'
        xml += ' name="'+self.name + '"'
        xml += ' description="'+self.description + '"'
        for key, v in self.kwargs.items():    
            if not key in ['value','error','name','description']:
                if isinstance(v, bool):
                    xml += ' ' + key + '="' + str(int(v))+ '"'                    
                elif isinstance(v, list):
                    xml += ' ' + key + '="'+",".join(v)+ '"'        
                elif isinstance(v, unicode) or isinstance(v, str)  :
                    xml += ' ' + key + '="'+v+ '"'        
                else:
                    xml += ' ' + key + '="'+str(v)+ '"'        
        if self.hasvalue:
            xml += ' value="'+unicode(self.value) + '"'
        if self.error:
            xml += ' error="'+self.error + '"'
        xml += " />"
        return xml
        
    def __str__(self):
        if self.error:
            error = " (ERROR: " + self.error + ")"
        else:
            error = ""
        if self.value:
            return self.__class__.__name__ + " " + self.id + ": " + str(self.value) + error
        else: 
            return self.__class__.__name__ + " " + self.id + error

    def set(self, value):
        """This parameter method attempts to set a specific value for this parameter. The value will be validated first, and if it can not be set. An error message will be set in the error property of this parameter"""
        if self.validate(value):
            #print "Parameter " + self.id + " successfully set to " + repr(value)
            self.hasvalue = True
            self.value = value
            return True
        else:
            #print "Parameter " + self.id + " COULD NOT BE set to " + repr(value)
            return False

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.id in postdata and postdata[self.id]:
            return postdata[self.id]
        else: 
            return False


    def access(self, user):
        """This method checks if the given user has access to see/set this parameter, based on the denyusers and/or allowusers option."""
        if self.denyusers:
            if user in self.denyusers:
                return False
        if self.allowusers:
            if not user in self.allowusers:
                return False
        return True

    @staticmethod
    def fromxml(node):
        if not isinstance(node,ElementTree._Element):
            node = ElementTree.parse(StringIO(node)).getroot() 
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
            for subtag in node: #parse possible subtags
                if subtag.tag == 'choice': #extra parsing for choice parameter (TODO: put in a better spot)
                    if not 'choices' in kwargs: kwargs['choices'] = {}
                    kwargs['choices'][subtag.attrib['id']] = subtag.text
                    if 'selected' in subtag.attrib and (subtag.attrib['selected'] == '1' or subtag.attrib['selected'] == 'yes'):
                        if 'multi' in kwargs and kwargs['multi'] == '1':
                            if not 'value' in kwargs: kwargs['value'] = []
                            kwargs['value'].append(subtag.attrib['id'])
                        else:
                            kwargs['value'] = subtag.attrib['id']

            return globals()[node.tag](id, name, description, **kwargs) #return parameter instance
        else:
            raise Exception("No such parameter exists: " + node.tag)
            
        
class BooleanParameter(AbstractParameter):
    def __init__(self, id, name, description = '', **kwargs):
        
        #defaultinstance
        self.reverse = False
        for key, value in kwargs.items():
            if key == 'reverse': 
                self.reverse = value  #Option gets outputted when option is NOT checked

        super(BooleanParameter,self).__init__(id,name,description, **kwargs)

    def set(self, value = True):
        return super(BooleanParameter,self).set(value)

    def unset(self):
        super(BooleanParameter,self).set(False)


    def compilearg(self):
        if not self.paramflag:
            Exception("paramflag not set for BooleanParameter " + self.id)
        if self.reverse: self.value = not self.value
        if self.value:
            return self.paramflag
        else:
            return ""

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.id in postdata and (postdata[self.id] == '1' or postdata[self.id] == 'True' or postdata[self.id] == 'yes' or postdata[self.id] == 'enabled'):
            return True #postdata[self.id]
        else: 
            return False


class StaticParameter(AbstractParameter):
    """This is a parameter that can't be changed (it's a bit of a contradiction, I admit). But useful for some metadata specifications."""

    def __init__(self, id, name, description = '', **kwargs):    
        if not 'value' in kwargs:
            raise ValueError("Static parameter expects value= !")
        super(StaticParameter,self).__init__(id,name,description, **kwargs)
        


class StringParameter(AbstractParameter):
    def __init__(self, id, name, description = '', **kwargs):
        self.maxlength = 0 #unlimited

        for key, value in kwargs.items():
            if key == 'maxlength': 
                self.maxlength = int(value)
                del kwargs[key]

        super(StringParameter,self).__init__(id,name,description, **kwargs)


    def validate(self,value):
        self.error = None
        if self.maxlength > 0 and len(value) > self.maxlength:
            self.error = "Text too long, exceeding maximum of " + str(self.maxlength) + " characters allowed"
            return False
        else:
            return True            

    def compilearg(self, value):
        if value.find(" ") >= 0 or value.find(";") >= 0:            
            value = value.replace('"',r'\"')
            value = '"' + value + '"' #wrap in quotes
        return super(StringParameter,self).compilearg(value)


class ChoiceParameter(AbstractParameter):
    def __init__(self, id, name, description, **kwargs):    
        if not 'choices' in kwargs:
            raise Exception("No parameter choices specified for parameter " + id + "!")
        self.choices = [] #list of key,value tuples
        for x in kwargs['choices']:
            if not isinstance(x,tuple) or len(x) != 2:
                self.choices.append( (x,x) ) #list of two tuples
            else:
                self.choices.append(x) #list of two tuples
        del kwargs['choices']

        #defaults
        self.delimiter = ","
        self.showall = False
        self.multi = False
        if not 'value' in kwargs and not 'default' in kwargs:
            self.value = self.choices[0][0] #no default specified, first choice is default
                
        for key, value in kwargs.items():
            if key == 'multi': 
                self.multi = value #boolean 
                del kwargs[key]
            elif key == 'showall': 
                self.showall = value #show all options at once (radio instead of a pull down) 
                del kwargs[key]
            elif key == 'delimiter': 
                self.delimiter = value #char
                del kwargs[key]

        super(ChoiceParameter,self).__init__(id,name,description, **kwargs)

    def validate(self,values):
        self.error = None
        if not isinstance(values,list):
            values = [values]
        for v in values:
            if not v in [x[0] for x in self.choices]:
                self.error = "Selected value was not an option!"
                return False
        return True



    def compilearg(self, values): 
        """This method compiles the parameter into syntax that can be used on the shell, such as -paramflag=value"""
        if isinstance(values,list):
            value = self.delimiter.join(values)
        else:
            value = values
        if value.find(" ") >= 0:
            value = '"' + value + '"' #wrap all in quotes

        #for some odd, reason this procudes an error, as if we're not an instance of choiceparameter
        #return super(ChoiceParameter,self).compilearg(value)

        #workaround:
        if self.paramflag and self.paramflag[-1] == '=' or self.nospace:
            sep = ''
        elif self.paramflag:
            sep = ' '
        return self.paramflag + sep + str(value)

    def xml(self, indent = ""):
        """This methods renders an XML representation of this parameter, along with 
        its selected value, and feedback on validation errors"""
        xml = indent + "<" + self.__class__.__name__
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
        if self.error:
             xml += ' error="'+self.error + '"'               
        xml += ">"
        for key, value in self.choices:
            if self.value == key or (isinstance(self.value ,list) and key in self.value):
                xml += " <choice id=\""+key+"\" selected=\"1\">" + value + "</choice>"        
            else:
                xml += " <choice id=\""+key+"\">" + value + "</choice>"
        xml += "</" + self.__class__.__name__ + ">"
        return xml
        
    def __str__(self):
        if self.error:
            error = " (ERROR: " + self.error + ")"
        else:
            error = ""
        if self.value:
            return self.__class__.__name__ + " " + self.id + ": " + ",".join(self.value) + error
        else: 
            return self.__class__.__name__ + " " + self.id + error        

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.multi: #multi parameters can be passed as  parameterid=choiceid1,choiceid2 or by setting parameterid[choiceid]=1 (or whatever other non-zero value)
            found = False
            if self.id in postdata and postdata[self.id]:
                passedvalues = postdata[self.id].split(',')
                values = []                
                for choicekey in [x[0] for x in self.choices]:
                    if choicekey in passedvalues:
                            found = True
                            values.append(choicekey)
            else:
                values = []
                for choicekey in [x[0] for x in self.choices]:
                    if self.id+'['+choicekey+']' in postdata:
                        found = True
                        if postdata[self.id+'['+choicekey+']']:
                            values.append(choicekey)
            if not found: 
                return False
            else:
                return values
        else:
            if self.id in postdata and postdata[self.id]:
                return postdata[self.id]
            else:
                return False


class TextParameter(StringParameter): #TextArea based
    def __init__(self, id, name, description = '', **kwargs):
        super(TextParameter,self).__init__(id,name,description, **kwargs)

    def compilearg(self, value):
        if value.find(" ") >= 0 or value.find(";") >= 0:            
            value = value.replace('"',r'\"')
            value = '"' + value + '"' #wrap in quotes
        return super(TextParameter,self).compilearg(value)

class IntegerParameter(AbstractParameter):
    def __init__(self, id, name, description = '', **kwargs):
        self.minvalue = 0
        self.maxvalue = 0 #unlimited        
        
        #defaults
        if not 'default' in kwargs and not 'value' in kwargs:
            self.value = 0
        for key, value in kwargs.items():
            if key == 'minvalue' or key == 'min':
                self.minvalue = int(value)
                del kwargs[key]
            elif key == 'maxvalue' or key == 'max': 
                self.maxvalue = int(value)                
                del kwargs[key]
              
        super(IntegerParameter,self).__init__(id,name,description, **kwargs)


    def validate(self, value):
        self.error = None
        try:
            value = int(value)
        except:
            self.error = "Not a valid number, note that no decimals are allowed"
            return False
        if ((self.maxvalue < self.minvalue) or ((value >= self.minvalue) and  (value <= self.maxvalue))):
            return True
        else:
            self.error = "Number must be a whole number between " + str(self.minvalue) + " and " + str(self.maxvalue)
            return False

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.id in postdata and postdata[self.id].isdigit():
            return int(postdata[self.id])
        else: 
            return False


class FloatParameter(AbstractParameter):
    def __init__(self, id, name, description = '', **kwargs):
        self.minvalue = 0.0
        self.maxvalue = -1.0 #unlimited if maxvalue < minvalue

                
        #defaults
        if not 'default' in kwargs and not 'value' in kwargs:
            self.value = 0.0
        for key, value in kwargs.items():
            if key == 'minvalue' or key == 'min': 
                self.minvalue = float(value)
                del kwargs[key]
            elif key == 'maxvalue' or key == 'max': 
                self.maxvalue = float(value)
                del kwargs[key]

        super(FloatParameter,self).__init__(id,name,description, **kwargs)

    def validate(self, value):
        self.error = None
        try:
            value = float(value)
        except:
            self.error = "Not a valid number"
            return False
        if ((self.maxvalue < self.minvalue) or ((value >= self.minvalue) and  (value <= self.maxvalue))):
            return True
        else:
            self.error = "Number must be between " + str(self.minvalue) + " and " + str(self.maxvalue)
            return False
        

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.id in postdata and postdata[self.id] != "":
            return float(postdata[self.id])
        else: 
            return False

