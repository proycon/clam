###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Parameter Classes --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#
#       Centre for Language and Speech Technology / Language Machines
#       Radboud University Nijmegen
#
#       Licensed under GPLv3
#
###############################################################

#pylint: disable=redefined-builtin


import sys
from lxml import etree as ElementTree
from io import StringIO #pylint: disable=wrong-import-order
from clam.common.util import xmlescape

class AbstractParameter(object):
    """This is the base class from which all parameter classes have to be derived."""

    def __init__(self, id, name, description = '', **kwargs):
        #: A unique alphanumeric ID
        self.id = id

        #: The parameter flag that will be used when this parameter is passed on the commandline (using COMMAND= and $PARAMETERS) (by default set to None)
        self.paramflag = None

        #: A representational name for this parameter, which the user will see
        self.name = name

        #: A clear description for this parameter, which the user will see
        self.description = description

        #: If this parameter has any validation errors, this will be set to an error message (by default set to None, meaning no error)
        self.error = None

        self.value = False
        self.kwargs = kwargs #make a copy for XML generation later
        self.required = False
        self.nospace = False
        self.require = []
        self.forbid = []
        self.validator = None
        self.default = None #None is a viable default for ALL parameter types because None means that the parameter is unset, so do not set this to False, 0, "" or 0.0 or something, only the user may do that with a default= parameter.

        #: You can restrict this parameter to only be available to certain users, set the usernames you want to allow here, all others are denied
        self.allowusers = []

        #: You can restrict this parameter to only be available to certain users, set the usernames you want to deny access here, all others are allowed
        self.denyusers = []
        self.hasvalue = False
        for key, value in kwargs.items():
            if key == 'allowusers':
                self.allowusers = value  #Users to allow access to this parameter (If not set, all users have access)
            elif key == 'denyusers':
                self.denyusers = value   #Users to deny access to this parameter (If not set, nobody is denied)
            elif key == 'default':
                if 'value' not in kwargs:
                    if self.set(value):
                        self.default = value
            elif key == 'value':
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
            elif key == 'validator':
                self.validator = value
            else:
                raise Exception("Unknown attribute specified for parameter: " + key + "=" + str(value))

    def constrainable(self):
        """Should this  parameter be used in checking contraints?"""
        return self.hasvalue

    def validate(self,value):
        """Validate the parameter"""
        if self.validator is not None:
            try:
                valid = self.validator(value)
            except Exception as e:
                import pdb; pdb.set_trace()
            if isinstance(valid, tuple) and len(valid) == 2:
                valid, errormsg = valid
            elif isinstance(valid, bool):
                errormsg = "Invalid value"
            else:
                raise TypeError("Custom validator must return a boolean or a (bool, errormsg) tuple.")
            if valid:
                self.error = None
            else:
                self.error = errormsg
            return valid
        else:
            self.error = None #reset error
            return True

    def compilearg(self):
        """This method compiles the parameter into syntax that can be used on the shell, such as for example: --paramflag=value"""
        if self.paramflag and self.paramflag[-1] == '=' or self.nospace:
            sep = ''
        elif self.paramflag:
            sep = ' '
        else:
            return str(self.value)
        return self.paramflag + sep + str(self.value)

    def xml(self, indent = ""):
        """This methods renders an XML representation of this parameter, along with
        its selected value, and feedback on validation errors"""
        xml = indent + "<" + self.__class__.__name__
        xml += ' id="'+self.id + '"'
        xml += ' name="'+xmlescape(self.name) + '"'
        xml += ' description="'+xmlescape(self.description) + '"'
        if self.paramflag:
            xml += ' flag="'+self.paramflag + '"'
        for key, v in self.kwargs.items():
            if key not in ('value','error','name','description','flag','paramflag', 'validator'):
                if isinstance(v, bool):
                    xml += ' ' + key + '="' + str(int(v))+ '"'
                elif isinstance(v, list):
                    xml += ' ' + key + '="'+xmlescape(",".join(v))+ '"'
                elif isinstance(v, str): #pylint: disable=undefined-variable
                    xml += ' ' + key + '="'+xmlescape(v)+ '"'
                else:
                    xml += ' ' + key + '="'+xmlescape(str(v))+ '"'
        if self.hasvalue:
            xml += ' value="'+xmlescape(str(self.value)) + '"'
        if self.error:
            xml += ' error="'+xmlescape(self.error) + '"'
        xml += " />"
        return xml

    def __str__(self):
        if self.value:
            return str(self.value)
        else:
            return ""

    def __repr__(self):
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
        if self.id in postdata:
            return postdata[self.id]
        else:
            return None


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
        """Create a Parameter instance (of any class derived from AbstractParameter!) given its XML description. Node can be a string containing XML or an lxml _Element"""
        if not isinstance(node,ElementTree._Element): #pylint: disable=protected-access
            node = ElementTree.parse(StringIO(node)).getroot()
        if node.tag in globals():
            id = ''
            paramflag = ''
            name = ''
            description = ''
            kwargs = {}
            error = None
            for attrib, value in node.attrib.items():
                if attrib == 'id':
                    id = value
                elif attrib == 'paramflag':
                    paramflag = value
                elif attrib == 'name':
                    name = value
                elif attrib == 'description':
                    description = value
                elif attrib == 'error':
                    error = value
                else:
                    kwargs[attrib] = value

            #extra parsing for choice parameter (TODO: put in a better spot)
            if 'multi' in kwargs and (kwargs['multi'] == 'yes' or kwargs['multi'] == '1' or kwargs['multi'] == 'true'):
                kwargs['value'] = []

            for subtag in node: #parse possible subtags
                if subtag.tag == 'choice': #extra parsing for choice parameter (TODO: put in a better spot)
                    if 'choices' not in kwargs: kwargs['choices'] = {}
                    kwargs['choices'][subtag.attrib['id']] = subtag.text
                    if 'selected' in subtag.attrib and (subtag.attrib['selected'] == '1' or subtag.attrib['selected'] == 'yes'):
                        if 'multi' in kwargs and (kwargs['multi'] == 'yes' or kwargs['multi'] == '1' or kwargs['multi'] == 'true'):
                            kwargs['value'].append(subtag.attrib['id'])
                        else:
                            kwargs['value'] = subtag.attrib['id']

            parameter = globals()[node.tag](id, name, description, **kwargs) #return parameter instance
            if error:
                parameter.error = error #prevent error from getting reset
            return parameter
        else:
            raise Exception("No such parameter exists: " + node.tag)


class BooleanParameter(AbstractParameter):
    """A parameter that takes a Boolean (True/False) value. """

    def __init__(self, id, name, description = '', **kwargs):
        """Keyword arguments:
            reverse = True/False  - If True, the command line option flag gets outputted when the option is NOT checked.
        """

        #defaultinstance
        self.reverse = False
        for key, value in kwargs.items():
            if key == 'reverse':
                self.reverse = value  #Option gets outputted when option is NOT checked

        super(BooleanParameter,self).__init__(id,name,description, **kwargs)


    def constrainable(self):
        """Should this parameter be used in checking contraints?"""
        return self.value

    def set(self, value = True):
        """Set the boolean parameter"""
        value = value in (True,1) or (isinstance(value, str) and (value.lower() in ("1","yes","true","enabled"))) #pylint: disable=undefined-variable
        return super(BooleanParameter,self).set(value)

    def unset(self):
        super(BooleanParameter,self).set(False)


    def compilearg(self):
        if not self.paramflag:
            return ""
        if self.reverse: self.value = not self.value
        if self.value:
            return self.paramflag
        else:
            return ""

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set(). It typically returns the default None when something is left unset (but that default can be overridden)"""
        if self.id in postdata:
            if ( (isinstance(postdata[self.id], bool) and postdata[self.id]) or postdata[self.id] == 1 or postdata[self.id].lower() in ('true','yes','enabled','1')):
                return True #postdata[self.id]
            else:
                return False
        else:
            return None


class StaticParameter(AbstractParameter):
    """This is a parameter that can't be changed (it's a bit of a contradiction, I admit). But useful for some metadata specifications."""

    def __init__(self, id, name, description = '', **kwargs):
        if not 'value' in kwargs:
            raise ValueError("Static parameter expects value= !")
        super(StaticParameter,self).__init__(id,name,description, **kwargs)



class StringParameter(AbstractParameter):
    """String Parameter, taking a text value, presented as a one line input box"""

    def __init__(self, id, name, description = '', **kwargs):
        """Keyword arguments::

            ``maxlength`` - The maximum length of the value, in number of characters
            ``validator`` - A custom validator function expecting one parameter (the value) and returning either a boolean or a (boolean, errormsg) tuple.
        """

        self.maxlength = 0 #unlimited

        for key, value in list(kwargs.items()):
            if key == 'maxlength':
                self.maxlength = int(value)
                del kwargs['maxlength']

        super(StringParameter,self).__init__(id,name,description, **kwargs)


    def validate(self,value):
        self.error = None
        if self.maxlength > 0 and len(value) > self.maxlength:
            self.error = "Text too long, exceeding maximum of " + str(self.maxlength) + " characters allowed"
            return False
        else:
            return super(StringParameter,self).validate(value)

    def compilearg(self):
        needsquotes = False
        check = (' ',';','|','&','!',"'",'"','`','>','<','\n','\r','\t')
        for c in self.value:
            if c in check:
                needsquotes = True
                break

        if needsquotes:
            #make sure it's shell-safe
            value = '"' + self.value.replace('"',r'\"') + '"' #wrap in quotes
        else:
            value = self.value
        if self.paramflag and self.paramflag[-1] == '=' or self.nospace:
            sep = ''
        elif self.paramflag:
            sep = ' '
        else:
            return str(self.value)
        return self.paramflag + sep + str(value)


class ChoiceParameter(AbstractParameter):
    """Choice parameter, users have to choose one of the available values, or multiple values if instantiated with multi=True."""

    def __init__(self, id, name, description, **kwargs):
        """Keyword arguments:

        choices - A list of choices. If keys and values are not the same, you can
                  specify a list of two-tuples:
                  choices=[('y','yes'),('n',no')]
        multi   - (boolean) User may select multiple values? (parameter value will be a list)
        delimiter - The delimiter between multiple options (if multi=True), and
                    when used on the command line.
        ``validator`` - A custom validator function expecting one parameter (the value) and returning either a boolean or a (boolean, errormsg) tuple.
        """


        if 'choices' not in kwargs:
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
        if  'value' not in kwargs and 'default' not in kwargs and ('multi' not in kwargs or not kwargs['multi']):
            self.value = self.choices[0][0] #no default specified, first choice is default

        if 'multi' in kwargs and kwargs['multi']:
            self.value = []

        for key, value in list(kwargs.items()):
            if key == 'multi':
                self.multi = bool(value) #boolean
                del kwargs[key]
            elif key == 'showall':
                self.showall = bool(value) #show all options at once (radio instead of a pull down)
                del kwargs[key]
            elif key == 'delimiter':
                self.delimiter = value #char
                del kwargs[key]

        super(ChoiceParameter,self).__init__(id,name,description, **kwargs)

    def validate(self,values):
        self.error = None
        if not isinstance(values,list) and not isinstance(values, tuple):
            values = [values]
        if not self.multi and len(values) > 1:
            self.error = "Multiple values were specified, but only one is allowed!"
            return False
        for v in values:
            if not v in [x[0] for x in self.choices]:
                self.error = "Selected value was not an option! (" + str(v) + ")"
                return False
        return super(ChoiceParameter,self).validate(values)


    def set(self, value):
        if self.multi:
            if not isinstance(value,list) and not isinstance(value, tuple):
                value = [value]
        return super(ChoiceParameter,self).set(value)

    def compilearg(self):
        """This method compiles the parameter into syntax that can be used on the shell, such as -paramflag=value"""
        if isinstance(self.value,list):
            value = self.delimiter.join(self.value)
        else:
            value = self.value
        if value.find(" ") >= 0:
            value = '"' + value + '"' #wrap all in quotes

        #for some odd, reason this produced an error, as if we're not an instance of choiceparameter
        #return super(ChoiceParameter,self).compilearg(value)

        #workaround:
        if self.paramflag and self.paramflag[-1] == '=' or self.nospace:
            sep = ''
        elif self.paramflag:
            sep = ' '
        else:
            return str(value)
        return self.paramflag + sep + str(value)

    def xml(self, indent = ""):
        """This methods renders an XML representation of this parameter, along with
        its selected value, and feedback on validation errors"""
        xml = indent + "<" + self.__class__.__name__
        xml += ' id="'+self.id + '"'
        xml += ' name="'+xmlescape(self.name) + '"'
        xml += ' description="'+xmlescape(self.description) + '"'
        if self.paramflag:
            xml += ' flag="'+self.paramflag + '"'
        if self.multi:
            xml += ' multi="true"'
        for key, value in self.kwargs.items():
            if key != 'choices' and key != 'default' and key != 'flag' and key != 'paramflag':
                if isinstance(value, bool):
                    xml += ' ' + key + '="' + str(int(value))+ '"'
                elif isinstance(value, list):
                    xml += ' ' + key + '="'+",".join(value)+ '"'
                else:
                    xml += ' ' + key + '="'+xmlescape(value)+ '"'
        if self.error:
            xml += ' error="'+self.error + '"'
        xml += ">"
        for key, value in self.choices:
            if self.value == key or (isinstance(self.value ,list) and key in self.value):
                xml += " <choice id=\""+key+"\" selected=\"1\">" + xmlescape(value) + "</choice>"
            else:
                xml += " <choice id=\""+key+"\">" + xmlescape(value) + "</choice>"
        xml += "</" + self.__class__.__name__ + ">"
        return xml

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.multi: #multi parameters can be passed as  parameterid=choiceid1,choiceid2 or by setting parameterid[choiceid]=1 (or whatever other non-zero value)
            found = False
            if self.id in postdata:
                found = True
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
                return None
            else:
                return values
        else:
            if self.id in postdata:
                return postdata[self.id]
            else:
                return None


class TextParameter(StringParameter): #TextArea based
    """Text Parameter, taking a text value, presented as a multiline input box"""

    def __init__(self, id, name, description = '', **kwargs):
        super(TextParameter,self).__init__(id,name,description, **kwargs)

    def compilearg(self):
        if self.value.find(" ") >= 0 or self.value.find(";") >= 0:
            value = '"' + self.value.replace('"',r'\"') + '"' #wrap in quotes
        else:
            value = self.value
        if self.paramflag and self.paramflag[-1] == '=' or self.nospace:
            sep = ''
        elif self.paramflag:
            sep = ' '
        else:
            return str(self.value)
        return self.paramflag + sep + str(value)

class IntegerParameter(AbstractParameter):
    def __init__(self, id, name, description = '', **kwargs):
        self.minvalue = 0
        self.maxvalue = 0 #unlimited

        #defaults
        if 'value' not in kwargs:
            self.value = 0
        for key, value in list(kwargs.items()):
            if key == 'minvalue' or key == 'min':
                self.minvalue = int(value)
                del kwargs[key]
            elif key == 'maxvalue' or key == 'max':
                self.maxvalue = int(value)
                del kwargs[key]

        super(IntegerParameter,self).__init__(id,name,description, **kwargs)

    def constrainable(self):
        """Should this parameter be used in checking contraints?"""
        return self.value

    def validate(self, value):
        self.error = None
        try:
            value = int(value)
        except ValueError:
            self.error = "Not a number"
            return False
        if self.minvalue == self.maxvalue and self.maxvalue == 0: #no restraints
            return super(IntegerParameter,self).validate(value)
        elif (self.maxvalue < self.minvalue) or ((value >= self.minvalue) and  (value <= self.maxvalue) ) :
            return super(IntegerParameter,self).validate(value)
        else:
            self.error = "Number must be a whole number between " + str(self.minvalue) + " and " + str(self.maxvalue)
            return False

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.id in postdata and postdata[self.id] != '':
            return int(postdata[self.id])
        else:
            return None

    def set(self, value):
        """This parameter method attempts to set a specific value for this parameter. The value will be validated first, and if it can not be set. An error message will be set in the error property of this parameter"""
        if self.validate(value):
            #print "Parameter " + self.id + " successfully set to " + repr(value)
            self.hasvalue = True
            if isinstance(value, float):
                self.value = round(value)
            else:
                self.value = int(value)
            return True
        else:
            #print "Parameter " + self.id + " COULD NOT BE set to " + repr(value)
            return False



class FloatParameter(AbstractParameter):
    def __init__(self, id, name, description = '', **kwargs):
        self.minvalue = 0.0
        self.maxvalue = -1.0 #unlimited if maxvalue < minvalue


        #defaults
        if 'value' not in kwargs:
            self.value = 0.0
        for key, value in list(kwargs.items()):
            if key == 'minvalue' or key == 'min':
                self.minvalue = float(value)
                del kwargs[key]
            elif key == 'maxvalue' or key == 'max':
                self.maxvalue = float(value)
                del kwargs[key]

        super(FloatParameter,self).__init__(id,name,description, **kwargs)

    def constrainable(self):
        """Should this parameter be used in checking contraints?"""
        return self.value


    def validate(self, value):
        self.error = None
        try:
            value = float(value)
        except ValueError:
            self.error = "Not a valid number"
            return False
        if self.minvalue == self.maxvalue and self.maxvalue == 0: #no restraints
            return super(FloatParameter,self).validate(value)
        elif (self.maxvalue < self.minvalue) or ((value >= self.minvalue) and  (value <= self.maxvalue)):
            return super(FloatParameter,self).validate(value)
        else:
            self.error = "Number must be between " + str(self.minvalue) + " and " + str(self.maxvalue)
            return False

    def set(self, value):
        """This parameter method attempts to set a specific value for this parameter. The value will be validated first, and if it can not be set. An error message will be set in the error property of this parameter"""
        if self.validate(value):
            #print "Parameter " + self.id + " successfully set to " + repr(value)
            self.hasvalue = True
            self.value = float(value)
            return True
        else:
            #print "Parameter " + self.id + " COULD NOT BE set to " + repr(value)
            return False

    def valuefrompostdata(self, postdata):
        """This parameter method searches the POST data and retrieves the values it needs. It does not set the value yet though, but simply returns it. Needs to be explicitly passed to parameter.set()"""
        if self.id in postdata and postdata[self.id] != '':
            return float(postdata[self.id])
        else:
            return None

