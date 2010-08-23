<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:dcoi="http://lands.let.ru.nl/projects/d-coi/ns/1.0" xmlns:imdi="http://www.mpi.nl/IMDI/Schema/IMDI">
	<xsl:output method="html" encoding="iso-8859-15" omit-xml-declaration="yes" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes" cdata-section-elements="script" />	
	<xsl:template match="/dcoi:DCOI">
	    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="nl" lang="nl">
	    <head>
	    	<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-15" />
		    <title><xsl:value-of select="//imdi:METATRANSCRIPT/imdi:Session/imdi:Title"/></title>
		    <link rel="stylesheet" href="sonar.css" type="text/css" />
		</head>
		<body>
				<div id="metadata">
					<xsl:apply-templates select="//imdi:METATRANSCRIPT"/>
				</div>
				<xsl:apply-templates select="//dcoi:text"/>
		</body>
		</html>
	</xsl:template>
	<xsl:template match="dcoi:text">
			<div id="text">
				<xsl:apply-templates select="//dcoi:head"/>
				<xsl:apply-templates select="//dcoi:p"/>
			</div>
	</xsl:template>
	<xsl:template match="dcoi:head">
		<h2 id="{@xml:id}">
			<xsl:apply-templates select="dcoi:s"/>
		</h2>
	</xsl:template>
	<xsl:template match="dcoi:p">
		<p id="{@xml:id}">
			<xsl:apply-templates select="dcoi:s"/>
		</p>
	</xsl:template>
	<xsl:template match="dcoi:s">
		<span id="{@xml:id}" class="sentence">
			<xsl:apply-templates select="dcoi:w"/>
		</span>
	</xsl:template>
	<xsl:template match="dcoi:w">
		<span id="{@xml:id}" class="word">
			<span class="attributes">
				<span class="wordid"><xsl:value-of select="@xml:id" /></span>
				<dl>
					<dt>PoS</dt><dd><xsl:value-of select="@pos"/></dd>
					<dt>Lemma</dt><dd><xsl:value-of select="@lemma"/></dd>
				</dl>
			</span>
			<xsl:value-of select="."/>
		</span>
		<xsl:text> </xsl:text>
	</xsl:template>
	<xsl:template match="imdi:METATRANSCRIPT">
		<table>
		<tr><th>Name:</th><td><xsl:value-of select="imdi:Session/imdi:Name"/></td></tr>
		<tr><th>Title:</th><td><strong><xsl:value-of select="imdi:Session/imdi:Title"/></strong></td></tr>
		<tr><th>Date:</th><td><xsl:value-of select="imdi:Session/imdi:Date"/></td></tr>
		<xsl:if test="//imdi:Source/imdi:Access/imdi:Availability">
			<tr><th>Availability:</th><td><xsl:value-of select="//imdi:Source/imdi:Access/imdi:Availability"/></td></tr>
		</xsl:if>
		<xsl:if test="//imdi:Source/imdi:Access/imdi:Publisher">
			<tr><th>Publisher:</th><td><xsl:value-of select="//imdi:Source/imdi:Access/imdi:Publisher"/></td></tr>
		</xsl:if>
		</table>
	</xsl:template>
</xsl:stylesheet>
