<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes" cdata-section-elements="script"/>

<xsl:template match="/parameters"> <!-- Will only match when stylesheet is used standalone outside of interface.xsl -->
    <table>
     <xsl:apply-templates />
    </table>
</xsl:template>


<xsl:template match="StaticParameter|staticparameter">  <!-- lowercase variant is required because of some XSLT issues in Mozilla -->
    <tr>
    <xsl:if test="@error">
         <xsl:attribute name="class">error</xsl:attribute>
    </xsl:if>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    <xsl:if test="@error">
         <div class="error alert alert-danger"><xsl:value-of select="@error"/></div>
    </xsl:if>
    </th>
    <td><xsl:value-of select="@value"/></td>
    </tr>
</xsl:template>

<xsl:template match="BooleanParameter|booleanparameter">
    <tr>
    <xsl:if test="@error">
         <xsl:attribute name="class">error</xsl:attribute>
    </xsl:if>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    <xsl:if test="@error">
         <div class="error alert alert-danger"><xsl:value-of select="@error"/></div>
    </xsl:if>
    </th>
    <td>
    <xsl:element name="input">
        <xsl:attribute name="type">hidden</xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:choose>
        <xsl:when test="@value = 1 or @value = 'yes' or @value = 'True'">
            <xsl:attribute name="value">1</xsl:attribute>
            <xsl:attribute name="checked">checked</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
            <xsl:attribute name="value">0</xsl:attribute>
            <xsl:attribute name="checked">unchecked</xsl:attribute>
        </xsl:otherwise>
        </xsl:choose>
    </xsl:element><xsl:element name="input"><!--no whitespace is important here-->
        <xsl:attribute name="type">checkbox</xsl:attribute>
        <xsl:attribute name="class">form-control</xsl:attribute>
        <xsl:if test="@value = 1 or @value = 'yes' or @value = 'True'">
            <xsl:attribute name="checked">checked</xsl:attribute>
        </xsl:if>
        <xsl:attribute name="onclick">this.previousSibling.value=1-this.previousSibling.value</xsl:attribute>
    </xsl:element>
    </td>
    </tr>
</xsl:template>

<xsl:template match="StringParameter|stringparameter">
    <tr>
    <xsl:if test="@error">
         <xsl:attribute name="class">error</xsl:attribute>
    </xsl:if>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    <xsl:if test="@error">
         <div class="error alert alert-danger"><xsl:value-of select="@error"/></div>
    </xsl:if>
    </th>
    <td>
    <xsl:element name="input">
        <xsl:attribute name="type">text</xsl:attribute>
        <xsl:attribute name="class">form-control</xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
    </xsl:element>
    </td>
    </tr>
</xsl:template>

<xsl:template match="TextParameter|textparameter">
    <tr>
    <xsl:if test="@error">
         <xsl:attribute name="class">error</xsl:attribute>
    </xsl:if>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    <xsl:if test="@error">
         <div class="error alert alert-danger"><xsl:value-of select="@error"/></div>
    </xsl:if>
    </th>
    <td>
    <textarea>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="class">form-control</xsl:attribute>
        <xsl:value-of select="@value"/>
    </textarea>
    </td>
    </tr>
</xsl:template>

<xsl:template match="IntegerParameter|integerparameter">
    <tr>
    <xsl:if test="@error">
         <xsl:attribute name="class">error</xsl:attribute>
    </xsl:if>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    <xsl:if test="@error">
         <div class="error alert alert-danger"><xsl:value-of select="@error"/></div>
    </xsl:if>
    </th>
    <td>
    <xsl:element name="input">
        <xsl:attribute name="type">text</xsl:attribute>
        <xsl:attribute name="class">form-control</xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
    </xsl:element>
    </td>
    </tr>
</xsl:template>


<xsl:template match="FloatParameter|floatparameter">
    <tr>
    <xsl:if test="@error">
         <xsl:attribute name="class">error</xsl:attribute>
    </xsl:if>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    <xsl:if test="@error">
         <div class="error alert alert-danger"><xsl:value-of select="@error"/></div>
    </xsl:if>
    </th>
    <td>
    <xsl:element name="input">
        <xsl:attribute name="type">text</xsl:attribute>
        <xsl:attribute name="class">form-control</xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
    </xsl:element>
    </td>
    </tr>
</xsl:template>

<xsl:template match="ChoiceParameter|choiceparameter">
    <xsl:choose>
        <xsl:when test="@multi">
            <tr>
            <xsl:if test="@error">
             <xsl:attribute name="class">error</xsl:attribute>
            </xsl:if>
            <th class="parameter">
            <xsl:value-of select="@name"/>
            <div class="description"><xsl:value-of select="@description"/></div>
            <xsl:if test="@error">
             <div class="error alert alert-danger"><xsl:value-of select="@error"/></div>
            </xsl:if>
            </th>
            <td></td></tr>
            <xsl:for-each select="choice">
                <tr>
                <td class="option"><xsl:value-of select="."/></td>
                <td>
                <xsl:element name="input">
                    <xsl:attribute name="type">checkbox</xsl:attribute>
                    <xsl:attribute name="class">form-control</xsl:attribute>
                    <xsl:attribute name="id"><xsl:value-of select="../@id"/></xsl:attribute>
                    <xsl:attribute name="name"><xsl:value-of select="../@id"/>[<xsl:value-of select="@id"/>]</xsl:attribute>
                    <xsl:attribute name="value">1</xsl:attribute>
                    <xsl:if test="@selected">
                        <xsl:attribute name="checked">checked</xsl:attribute>
                    </xsl:if>
                </xsl:element>
                </td>
                </tr>
            </xsl:for-each>
        </xsl:when>
        <xsl:when test="@showall">
            <tr>
            <xsl:if test="@error">
             <xsl:attribute name="class">error</xsl:attribute>
            </xsl:if>
            <th class="parameter">
            <xsl:value-of select="@name"/>
            <div class="description"><xsl:value-of select="@description"/></div>
            <xsl:if test="@error">
             <div class="error alert alert-danger"><xsl:value-of select="@error"/></div>
            </xsl:if>
            </th>
            <td></td></tr>
            <xsl:for-each select="choice">
                <tr>
                <td class="option"><xsl:value-of select="."/></td>
                <td>
                <xsl:element name="input">
                    <xsl:attribute name="type">radio</xsl:attribute>
                    <xsl:attribute name="class">form-control</xsl:attribute>
                    <xsl:attribute name="id"><xsl:value-of select="../@id"/></xsl:attribute>
                    <xsl:attribute name="name"><xsl:value-of select="../@id"/></xsl:attribute>
                    <xsl:attribute name="value"><xsl:value-of select="@id"/></xsl:attribute>
                    <xsl:if test="@selected">
                        <xsl:attribute name="checked">checked</xsl:attribute>
                    </xsl:if>
                </xsl:element>
                </td>
                </tr>
            </xsl:for-each>
        </xsl:when>
        <xsl:otherwise>
            <tr>
            <xsl:if test="@error">
             <xsl:attribute name="class">error</xsl:attribute>
            </xsl:if>
            <th class="parameter">
            <xsl:value-of select="@name"/>
            <div class="description"><xsl:value-of select="@description"/></div>
            <xsl:if test="@error">
             <div class="error alert alert-danger"><xsl:value-of select="@error"/></div>
            </xsl:if>
            </th>
            <td>
            <select>
                <xsl:attribute name="class">form-control</xsl:attribute>
                <xsl:attribute name="name"><xsl:value-of select="@id" /></xsl:attribute>
                <xsl:for-each select="choice">
                    <option><xsl:attribute name="value"><xsl:value-of select="@id"/></xsl:attribute><xsl:if test="@selected = 1"><xsl:attribute name="selected">selected</xsl:attribute></xsl:if><xsl:value-of select="."/></option>
                </xsl:for-each>
            </select>
            </td>
            </tr>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
