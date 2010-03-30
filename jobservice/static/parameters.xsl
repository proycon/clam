<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="BooleanParameter">
    <tr>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    </th>
    <td>
    <xsl:element name="input">
        <xsl:attribute name="type">checkbox</xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="value">1</xsl:attribute>
        <xsl:if test="@value = 1">
            <xsl:attribute name="checked">checked</xsl:attribute>     
        </xsl:if>
    </xsl:element>
    </td>
    </tr>
</xsl:template>

<xsl:template match="StringParameter">
    <tr>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    </th>
    <td>
    <xsl:element name="input">
        <xsl:attribute name="type">text</xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
    </xsl:element>  
    </td>
    </tr>
</xsl:template>

<xsl:template match="TextParameter">
    <tr>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    </th>
    <td>
    <textarea>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:value-of select="@value"/>    
    </textarea>
    </td>
    </tr>
</xsl:template>

<xsl:template match="IntegerParameter">
    <tr>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    </th>
    <td>
    <xsl:element name="input">
        <xsl:attribute name="type">text</xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
    </xsl:element>  
    </td>
    </tr>
</xsl:template>


<xsl:template match="FloatParameter">
    <tr>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    </th>
    <td>
    <xsl:element name="input">
        <xsl:attribute name="type">text</xsl:attribute>
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="name"><xsl:value-of select="@id"/></xsl:attribute>
        <xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
    </xsl:element>  
    </td>
    </tr>
</xsl:template>

<xsl:template match="ChoiceParameter">
    <tr>
    <th class="parameter">
    <xsl:value-of select="@name"/>
    <div class="description"><xsl:value-of select="@description"/></div>
    </th>
    <xsl:choose>
        <xsl:when test="@multi = true">
            <td></td></tr>
            <xsl:foreach select="choice">
                <tr>
                <td class="option"><xsl:value-of select="."/><td>
                <td>
                <xsl:element name="input">
                    <xsl:attribute name="type">checkbox</xsl:attribute>
                    <xsl:attribute name="id"><xsl:value-of select="../@id"/></xsl:attribute>
                    <xsl:attribute name="name"><xsl:value-of select="../@id"/></xsl:attribute>
                    <xsl:attribute name="value"><xsl:value-of select="@id"/></xsl:attribute>
                    <xsl:if test="@selected = 1">
                        <xsl:attribute name="checked">checked</xsl:attribute>     
                    </xsl:if>
                </xsl:element>
                </td>
                </tr>
            </xsl:foreach>
        </xsl:when>
        <xsl:when test="@showall = true">
            <td></td></tr>
            <xsl:foreach select="choice">
                <tr>
                <td class="option"><xsl:value-of select="."/><td>
                <td>
                <xsl:element name="input">
                    <xsl:attribute name="type">radio</xsl:attribute>
                    <xsl:attribute name="id"><xsl:value-of select="../@id"/></xsl:attribute>
                    <xsl:attribute name="name"><xsl:value-of select="../@id"/></xsl:attribute>
                    <xsl:attribute name="value"><xsl:value-of select="@id"/></xsl:attribute>
                    <xsl:if test="@selected = 1">
                        <xsl:attribute name="checked">checked</xsl:attribute>     
                    </xsl:if>
                </xsl:element>
                </td>
                </tr>
            </xsl:foreach>
        </xsl:when>
        <xsl:otherwise>
            <td>
            <select name="@id">
                <xsl:foreach select="choice">
                    <option><xsl:attribute name="value"><xsl:value-of select="@id"/></xsl:attribute><xsl:if test="@selected = 1"><xsl:attribute name="selected">selected</xsl:attribute></xsl:if><xsl:value-of select="."/></option>
                </xsl:foreach>
            </select>
            </td>
            </tr>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
