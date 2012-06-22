<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet version="1.0" xmlns="http://www.w3.org/1999/xhtml" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:imdi="http://www.mpi.nl/IMDI/Schema/IMDI" xmlns:folia="http://ilk.uvt.nl/folia">

<xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes" />

<xsl:template match="/folia:FoLiA">
  <html> 
  <head>
        <meta http-equiv="content-type" content="application/xhtml+xml; charset=utf-8"/>
        <meta name="generator" content="folia2html.xsl" />
        <xsl:choose>
            <xsl:when test="folia:metadata/folia:meta[@id='title']">
                <title><xsl:value-of select="folia:metadata/folia:meta[@id='title']" /></title>
            </xsl:when>
            <xsl:when test="folia:metadata[@type='imdi']//imdi:Session/imdi:Title">
                <title><xsl:value-of select="folia:metadata[@type='imdi']//imdi:Session/imdi:Title" /></title>
            </xsl:when>
            <xsl:otherwise>
                <title><xsl:value-of select="@xml:id" /></title>
            </xsl:otherwise>
        </xsl:choose>
        <style type="text/css">
            				body {
					/*background: #222222;*/
					background: #b7c8c7;
					font-family: sans-serif;
					font-size: 12px;
					margin-bottom:240px;
				}

				div.text {
					width: 700px;
					margin-top: 50px;
					margin-left: auto;
					margin-right: auto;
					padding: 10px;    
					padding-left: 50px;
					padding-right: 50px;
					text-align: left;
					background: white;
					border: 2px solid black;
				}

				div.div {
					padding-left: 0px;
					padding-top: 10px;
					padding-bottom: 10px;    
				}

				#metadata {
					font-family: sans-serif;
					width: 700px;
					font-size: 90%;
					margin-left: auto;
					margin-right: auto;
					margin-top: 5px;
					margin-bottom: 5px;
					background: #b4d4d1; /*#FCFFD0;*/
					border: 1px solid #628f8b;
					width: 40%;
					padding: 5px;
				}
				#metadata table {
					text-align: left;
				}

				#text {
					border: 1px solid #628f8b;
					width: 60%; 
					max-width: 1024px;
					background: white;
					padding: 20px;
					padding-right: 100px; 
					margin-top: 5px;
					margin-left: auto; 
					margin-right: auto; 
					color: #222;
				}
				.s {
					background: white;
					display: inline;
					border-left: 1px white solid;
					border-right: 1px white solid;
				}
				.s:hover {
					background: #e7e8f8;
					border-left: 1px blue solid;
					border-right: 1px blue solid;
				}
				.word { 
					display: inline; 
					color: black; 
					position: relative; 
					text-decoration: none; 
					z-index: 24; 
				}
				#text {
					border: 1px solid #628f8b;
					width: 60%; 
					max-width: 1024px;
					background: white;
					padding: 20px;
					padding-right: 100px; 
					margin-top: 5px;
					margin-left: auto; 
					margin-right: auto; 
					color: #222;
				}

				.word { 
					display: inline; 
					color: black; 
					position: relative; 
					text-decoration: none; 
					z-index: 24;
				}
				
				.t {
					display: inline;
					text-decoration: none;
					z-index: 24;
				}

				.word>.attributes { display: none; font-size: 12px; font-weight: normal; }
				.word:hover { 
					/*text-decoration: underline;*/ 
					z-index: 25;
				}
				.word:hover>.t {
					background: #bfc0ed;
					text-decoration: underline;
				}
				
				.word:hover>.attributes { 
					display: block; 
					position: absolute;
					width: 320px; 
					font-size: 12px;
					left: 2em; 
					top: 2em;
					background: #b4d4d1; /*#FCFFD0;*/
					opacity: 0.9; filter: alpha(opacity = 90); 
					border: 1px solid #628f8b; 
					padding: 5px; 
					text-decoration: none !important;
				}
				.attributes dt {
					color: #254643;
					font-weight: bold;
				}
				.attributes dd {
					color: black;
					font-family: monospace;
				}
				.attributes .wordid {
					display: inline-block:
					width: 100%;
					font-size: 75%;
					color: #555;
					font-family: monospace;
					text-align: center;
				}
				.event {
					padding: 10px;
					border: 1px solid #4f7d87;
				}
				.gap pre {
					padding: 5px;
					background: #ddd;
					border: 1px dashed red;
				}           
				span.attrlabel {
					display: inline-block;
					color: #254643;
					font-weight: bold;
					width: 90px;				
				}	
				span.attrvalue {
					font-weight: 12px;
					font-family: monospace;
				}
				div#iewarning {
					width: 90%;
					padding: 10px;
					color: red;
					font-size: 16px;
					font-weight: bold;
					text-align: center;					
				}	

        </style>
  </head>
    <body>
    	<xsl:comment><![CDATA[[if lte IE 10]>
		<div id="iewarning">
			The FoLiA viewer does not work properly with Internet Explorer, please consider upgrading to Mozilla Firefox or Google Chrome instead. 
		</div>
		<![endif]]]></xsl:comment>       
        <xsl:apply-templates />
    </body> 
  </html>
</xsl:template>

<xsl:template match="folia:text">
 <div class="text">
 	<xsl:apply-templates />
 </div>
</xsl:template>

<xsl:template match="folia:div">
 <div class="div"> 
   <xsl:apply-templates />
 </div>
</xsl:template>

<xsl:template match="folia:p">
 <p id="{@xml:id}">
  <xsl:apply-templates />
 </p>
</xsl:template>


<xsl:template match="folia:gap">
 <pre class="gap">
  <xsl:value-of select="folia:content" />
 </pre>
</xsl:template>


<xsl:template match="folia:head">
<xsl:choose>
 <xsl:when test="count(ancestor::folia:div) = 1">
    <h1>
        <xsl:apply-templates />
    </h1>
 </xsl:when>
 <xsl:when test="count(ancestor::folia:div) = 2">
    <h2>
        <xsl:apply-templates />
    </h2>
 </xsl:when> 
 <xsl:when test="count(ancestor::folia:div) = 3">
    <h3>
        <xsl:apply-templates />
    </h3>
 </xsl:when>  
 <xsl:when test="count(ancestor::folia:div) = 4">
    <h4>
        <xsl:apply-templates />
    </h4>
 </xsl:when>  
 <xsl:when test="count(ancestor::folia:div) = 5">
    <h5>
        <xsl:apply-templates />
    </h5>
 </xsl:when>   
 <xsl:otherwise>
    <h6>
        <xsl:apply-templates />
    </h6>
 </xsl:otherwise>
</xsl:choose> 
</xsl:template>

<xsl:template match="folia:list">
<ul>
    <xsl:apply-templates />
</ul>
</xsl:template>

<xsl:template match="folia:listitem">
<li><xsl:apply-templates /></li>
</xsl:template>

<xsl:template match="folia:s">
 <span id="{@xml:id}" class="s"><xsl:apply-templates select=".//folia:w|folia:whitespace|folia:br" /></span>
</xsl:template>

<xsl:template match="folia:w">
<xsl:if test="not(ancestor::folia:original) and not(ancestor::folia:suggestion) and not(ancestor::folia:alternative)">
<span id="{@xml:id}" class="word"><span class="t"><xsl:value-of select=".//folia:t[1]"/></span><xsl:call-template name="tokenannotations" /></span>
<xsl:choose>
   <xsl:when test="@space = 'no'"></xsl:when>
   <xsl:otherwise>
    <xsl:text> </xsl:text>
   </xsl:otherwise>
</xsl:choose>
</xsl:if>
</xsl:template>

<xsl:template name="tokenannotations">
 <span class="attributes">
 	<span class="attrlabel">ID</span><span class="attrvalue"><xsl:value-of select="@xml:id" /></span><br />
	<xsl:if test="folia:phon">
        	<span class="attrlabel">Phonetics</span><span class="attrvalue"><xsl:value-of select="folia:phon/@class" /></span><br />
    </xsl:if>
        <xsl:if test="folia:pos">
        	<span class="attrlabel">PoS</span><span class="attrvalue"><xsl:value-of select="folia:pos/@class" /></span><br />
        </xsl:if>
        <xsl:if test="folia:lemma">
			<span class="attrlabel">Lemma</span><span class="attrvalue"><xsl:value-of select="folia:lemma/@class" /></span><br />
        </xsl:if>
        <xsl:if test="folia:sense">
			<span class="attrlabel">Sense</span><span class="attrvalue"><xsl:value-of select="folia:sense/@class" /></span><br />
        </xsl:if>
        <xsl:if test="folia:subjectivity">
			<span class="attrlabel">Subjectivity</span><span class="attrvalue"><xsl:value-of select="folia:subjectivity/@class" /></span><br />
        </xsl:if>
        <xsl:if test="folia:errordetection[@errors='yes']">
			<span class="attrlabel">Error detection</span><span class="attrvalue">Possible errors</span><br />        
        </xsl:if>
        <xsl:if test="folia:correction">
            <xsl:if test="folia:correction/folia:suggestion/folia:t">
            	<span class="attrlabel">Suggestion(s) for text correction</span><span class="attrvalue"><xsl:for-each select="folia:correction/folia:suggestion/folia:t">
                    <em><xsl:value-of select="." /></em><xsl:text> </xsl:text>
                </xsl:for-each></span><br />        
            </xsl:if>
            <xsl:if test="folia:correction/folia:original/folia:t">
            	<span class="attrlabel">Original pre-corrected text</span>
            	<span class="attrvalue">                
                <xsl:for-each select="folia:correction/folia:original/folia:t[1]">
                    <em><xsl:value-of select="." /></em><xsl:text> </xsl:text>
                </xsl:for-each>      
                </span><br />            
            </xsl:if>            
        </xsl:if>
 </span>
</xsl:template>

<xsl:template match="folia:whitespace">
 <br /><br />
</xsl:template>

<xsl:template match="folia:figure">
 <div class="figure">
  <img>
      <xsl:attribute name="src">
        <xsl:value-of select="@src" />
      </xsl:attribute>
      <xsl:attribute name="alt">
        <xsl:value-of select="folia:desc" />
      </xsl:attribute>      
  </img>
  <xsl:if test="folia:caption">
   <div class="caption">
     <xsl:apply-templates select="folia:caption/*" />
   </div>
  </xsl:if>
 </div>
</xsl:template>

</xsl:stylesheet>

