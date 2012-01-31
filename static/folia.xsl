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
            div.tokenannotations { display: none; }
            body {
                background: #424242;
                font-size: 14px;
            }
            body, p, h1,h2,h3,h4,h5 {
                font-family: sans-serif;                
            }
            div.text {
                margin-left: 340px;
                margin-right: auto;
                width: 60%;
                padding: 20px;
                background: white;
                border: solid 1px black;
            }
            pre.gap {
                display: block;
                background: white;
                border: #fff solid dashed;
                padding: 5px;
            }
            div.tokenannotations {
                font-family: sans-serif;
                font-size: 14px;
            }
            span.word:hover {
                background: #A5C5D1;
            }
            span.word:hover div.tokenannotations { 
                display: block; 
                position: fixed;
                width: 320px; 
                left: 5px;
                top: 5px;
                background: #b4d4d1; /*#FCFFD0;*/
                opacity: 0.9; filter: alpha(opacity = 90); 
                border: 1px solid #628f8b; 
                padding: 5px; 
                text-decoration: none;
            }
            dt {
                font-weight: bold;
                width: 90%;
            }
            dd {
                width: 90%;
                font-weight: normal;
            }
            dd.errors {
                color: red;
            }
            div.figure {
                text-align: center;
            }
            div.caption {
                font-style: italic;
                text-align: center;
            }
        </style>
        <link rel="StyleSheet" href="style.css" type="text/css" />
  </head>
  <body>     
   <xsl:apply-templates select="folia:text" />    
  </body>
  </html>
</xsl:template>

<xsl:template match="/folia:FoLiA/folia:text">
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
<span id="{@xml:id}" class="word"><xsl:value-of select=".//folia:t[1]"/><xsl:call-template name="tokenannotations" /></span>
<xsl:choose>
   <xsl:when test="@space = 'no'"></xsl:when>
   <xsl:otherwise>
    <xsl:text> </xsl:text>
   </xsl:otherwise>
</xsl:choose>
</xsl:if>
</xsl:template>

<xsl:template name="tokenannotations">
 <div id="TOKENANNOTATIONS.{@xml:id}" class="tokenannotations">
    <dl>
        <dt>ID</dt>
        <dd><xsl:value-of select="@xml:id" /></dd>        
        <xsl:if test="folia:phon">
            <dt>Phonetics</dt>
            <dd><xsl:value-of select="folia:phon/@class" /></dd>
        </xsl:if>
        <xsl:if test="folia:pos">
            <dt>PoS</dt>
            <dd><xsl:value-of select="folia:pos/@class" /></dd>
        </xsl:if>
        <xsl:if test="folia:lemma">
            <dt>Lemma</dt>
            <dd><xsl:value-of select="folia:lemma/@class" /></dd>
        </xsl:if>
        <xsl:if test="folia:sense">
            <dt>Sense</dt>
            <dd><xsl:value-of select="folia:sense/@class" /></dd>
        </xsl:if>
        <xsl:if test="folia:subjectivity">
            <dt>Subjectivity</dt>
            <dd><xsl:value-of select="folia:subjectivity/@class" /></dd>
        </xsl:if>
        <xsl:if test="folia:errordetection[@errors='yes']">
            <dt>Error detection</dt>
            <dd class="errors">There may be errors!</dd>
        </xsl:if>
        <xsl:if test="folia:correction">
            <xsl:if test="folia:correction/folia:suggestion/folia:t">
                <dt>Suggestion(s) for text correction</dt>
                <xsl:for-each select="folia:correction/folia:suggestion/folia:t">
                    <dd><xsl:value-of select="." /></dd>
                </xsl:for-each>
            </xsl:if>
            <xsl:if test="folia:correction/folia:original/folia:t">
                <dt>Original pre-corrected text</dt>
                <xsl:for-each select="folia:correction/folia:original/folia:t[1]">
                    <dd class="errors"><xsl:value-of select="." /></dd>
                </xsl:for-each>                
            </xsl:if>            
        </xsl:if>
    </dl>
 </div>
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

