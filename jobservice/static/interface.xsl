<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:import href="parameters.xsl" />

<xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes"/>

<xsl:template match="/clam">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <xsl:call-template name="head" />
  <body>
    <div id="header"><h1><xsl:value-of select="@name"/></h1><h2><xsl:value-of select="@project"/></h2></div>
    <xsl:apply-templates select="status"/>
    <xsl:choose>
      <xsl:when test="status/@code = 0">              
        <xsl:apply-templates select="input"/>
        <!-- upload form transformed from input formats -->
        <xsl:apply-templates select="inputformats"/>             
        <xsl:apply-templates select="parameters"/>  
      </xsl:when>
      <xsl:when test="status/@code = 2">
        <xsl:apply-templates select="output"/>            
      </xsl:when>
    </xsl:choose>
    <xsl:call-template name="footer" />
  </body>
  </html>
</xsl:template>


<xsl:template name="head">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title><xsl:value-of select="@name"/> :: <xsl:value-of select="@project"/></title>
    <link rel="stylesheet" href="/static/style.css" type="text/css" />
  </head>
</xsl:template>

<xsl:template name="footer">
    <div id="footer">Powered by <strong>CLAM</strong> - Computational Linguistics Application Mediator<br />by Maarten van Gompel<br /><a href="http://ilk.uvt.nl">Induction of Linguistic Knowledge Research Group</a>, <a href="http://www.uvt.nl">University of Tilburg</a></div>
</xsl:template>


<xsl:template match="/clam/status">
    <div id="status">
     <h3>Status</h3>
     <xsl:choose>
      <xsl:when test="@code = 0">
        <div class="ready"><xsl:value-of select="@message"/></div>
      </xsl:when>
      <xsl:when test="@code = 1">
        <div class="running"><xsl:value-of select="@message"/></div>
      </xsl:when>
      <xsl:when test="@code = 2">
        <div class="done"><xsl:value-of select="@message"/></div>
      </xsl:when>
      <xsl:otherwise>
        <div class="other"><xsl:value-of select="@message"/></div>
      </xsl:otherwise>
     </xsl:choose>
    </div>
</xsl:template>

<xsl:template match="/clam/inputformats">
        <div id="uploadform">
            <h3>Upload a file from disk</h3>
            <form method="POST" enctype="multipart/form-data" action="upload/">
                <input type="hidden" name="uploadcount" value="1" />
                <table>
                 <tr><td><label for="upload1">Upload file:</label></td><td><input type="file" name="upload1" /></td></tr>
                 <tr><td><label for="uploadformat1">Format:</label></td><td>
                    <select name="uploadformat1">
                    <xsl:for-each select="*">
                        <option><xsl:attribute name="value"><xsl:value-of select="name(.)" /></xsl:attribute><xsl:value-of select="@name" /></option>
                    </xsl:for-each>
                    </select>
                 </td></tr>
                 <tr><td></td><td><input class="uploadbutton" type="submit" value="Upload file" /></td></tr>
                </table>
            </form>
        </div>
</xsl:template>

<xsl:template match="/clam/input">
    <div id="input">
        <h3>Input files</h3>
        <table>
            <xsl:apply-templates select="path" />
        </table>
    </div>
</xsl:template>

<xsl:template match="/clam/output">
    <div id="output">
        <h3>Output files</h3>
        <table>
            <xsl:apply-templates select="path" />
        </table>
    </div>
</xsl:template>

<xsl:template match="/clam/input/path">
    <tr><th><xsl:value-of select="."/></th><td><xsl:value-of select="@format"/></td><td><xsl:value-of select="@encoding" /></td></tr>
</xsl:template>


<xsl:template match="/clam/output/path">
    <tr>
    <th><a><xsl:attribute name="href">output/<xsl:value-of select="."/></xsl:attribute></a></th>
    <td><xsl:value-of select="@format"/></td><td><xsl:value-of select="@encoding"/></td>
    </tr>
</xsl:template>

<xsl:template match="/clam/parameters">
    <form method="POST" enctype="multipart/form-data" action="upload">
    <div id="parameters">
        <h3>Parameter Selection</h3>
        <table>
        <xsl:apply-templates />
        </table>

        <div id="corpusselection">
        <label for="usecorpus">Input source:</label>
        <select name="usecorpus">
            <option value="" selected="selected">Use uploaded files</option>
            <xsl:for-each select="../corpora/corpus">
                <option><xsl:attribute name="value"><xsl:value-of select="." /></xsl:attribute><xsl:value-of select="." /></option>
            </xsl:for-each>
        </select>
        </div>
        <div id="startbutton">
            <input type="submit" class="start" value="Start" />
        </div>
    </div>
    </form>
</xsl:template>


<xsl:template match="/clamupload">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <xsl:call-template name="head" />
  <body>
    <div id="header"><h1><xsl:value-of select="@name"/></h1><h2><xsl:value-of select="@project"/></h2></div>
    <xsl:for-each select="upload">
        <div id="upload">
            <ul>
              <xsl:apply-templates select="file"/>  
            </ul>
        </div>
    </xsl:for-each>
    <xsl:call-template name="footer" />
  </body>
  </html>
</xsl:template>

<xsl:template match="file">
    <xsl:choose>
    <xsl:when test="@validated = yes">
        <li class="ok"><tt><xsl:value-of select="@name" /></tt>: OK</li>    
    </xsl:when>
    <xsl:otherwise>
        <li class="failed"><tt><xsl:value-of select="@name" /></tt>: Failed</li>    
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>


<xsl:template match="/clamindex">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <xsl:call-template name="head" />
  <body>
    <div id="header"><h1><xsl:value-of select="@name"/></h1><h2><xsl:value-of select="@project"/></h2></div>
    <div id="startproject">
        <h3>Start a new Project</h3>    
        <form id="startprojectform" action="">
            Project ID: <input type="projectname" />
            <!-- TODO: Add javascript thingies -->
            <input type="submit" value="Start project" />
        </form>
    </div>
    <div id="index">
    <h3>Projects</h3>
    <xsl:for-each select="project">
            <ul>
              <li><a><xsl:attribute name="href"><xsl:value-of select="." /></xsl:attribute><xsl:value-of select="." /></a></li>
            </ul>
    </xsl:for-each>
    </div>
    <xsl:call-template name="footer" />
  </body>
  </html>
</xsl:template>

</xsl:stylesheet>
