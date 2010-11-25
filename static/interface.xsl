<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xlink="http://www.w3.org/1999/xlink">

<xsl:import href="parameters.xsl" />

<xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes" cdata-section-elements="script"/>

<xsl:template match="/clam">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <xsl:call-template name="head" />
  <body>
    <div id="container">
        <xsl:choose>
         <xsl:when test="@project">
            <div id="header"><h1><xsl:value-of select="@name"/></h1><h2><xsl:value-of select="@project"/></h2></div>
            <xsl:apply-templates select="status"/>
            <xsl:choose>
              <xsl:when test="status/@code = 0">  
                <div id="input" class="box">            
                 <xsl:apply-templates select="input"/><!-- upload form transformed from input formats -->
                 <xsl:apply-templates select="profiles"/> 
                </div>
                <xsl:apply-templates select="parameters"/>  
              </xsl:when>
              <xsl:when test="status/@code = 2">
                <xsl:apply-templates select="output"/>
              </xsl:when>
            </xsl:choose>
         </xsl:when>
         <xsl:otherwise>
             <xsl:call-template name="clamindex" />
         </xsl:otherwise>
        </xsl:choose>    
        <xsl:call-template name="footer" />
    </div>
  </body>
  </html>
</xsl:template>


<xsl:template name="head">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <xsl:if test="status/@code = 1">
      <meta http-equiv="refresh" content="10" />            
    </xsl:if>
    <title><xsl:value-of select="@name"/> :: <xsl:value-of select="@project"/></title>
    <link rel="stylesheet" href="{/clam/@baseurl}/static/style.css" type="text/css"></link>
    <!--<link rel="stylesheet" href="/static/humanity/jquery-ui-1.8.1.custom.css" type="text/css" />-->
    <link rel="stylesheet" href="{/clam/@baseurl}/static/table.css" type="text/css" />
    <script type="text/javascript" src="{/clam/@baseurl}/static/jquery-1.4.2.min.js"></script>
    <!--<script type="text/javascript" src="/static/jquery-ui-1.8.1.custom.min.js"></script>-->
    <script type="text/javascript" src="{/clam/@baseurl}/static/jquery.dataTables.min.js"></script>
    <script type="text/javascript" src="{/clam/@baseurl}/static/ajaxupload.js"></script>
    <script type="text/javascript" src="{/clam/@baseurl}/data.js"></script>
    <script type="text/javascript" src="{/clam/@baseurl}/static/clam.js"></script>
  </head>
</xsl:template>

<xsl:template name="footer">
    <div id="footer" class="box">Powered by <strong>CLAM</strong> - Computational Linguistics Application Mediator<br />by Maarten van Gompel<br /><a href="http://ilk.uvt.nl">Induction of Linguistic Knowledge Research Group</a>, <a href="http://www.uvt.nl">Tilburg University</a>

<span class="extracredits">
Funded under CLARIN-NL projects TICCLops (09-011) and WP1 of TTNWW, coordinated by Martin Reynaert. Development continues in further TTNWW work packages, coordinated by Antal van den Bosch.
</span>
</div>
</xsl:template>


<xsl:template match="/clam/status">
    <div id="status" class="box">
     <h2>Status</h2>
     <xsl:if test="@errors = 'yes'">
      <div class="error">
            <strong>Error: </strong> <xsl:value-of select="@errormsg"/>
      </div>
     </xsl:if>     
     <xsl:choose>
      <xsl:when test="@code = 0">
        <div class="ready"><xsl:value-of select="@message"/><input id="abortbutton" type="button" value="Abort and delete project" /></div>
      </xsl:when>
      <xsl:when test="@code = 1">
        <div class="running"><xsl:value-of select="@message"/><input id="abortbutton" type="button" value="Abort and delete project" /></div>
        <xsl:choose>
         <xsl:when test="@completion > 75">
           <div id="progressbar">
                <span id="progressvalue"><xsl:attribute name="style">width: <xsl:value-of select="@completion"/>%;</xsl:attribute><xsl:value-of select="@completion"/>%</span>
           </div>
         </xsl:when>
         <xsl:when test="@completion > 0">
           <div id="progressbar">
                <span id="progressvalue"><xsl:attribute name="style">width: <xsl:value-of select="@completion"/>%;</xsl:attribute></span><xsl:value-of select="@completion"/>%
           </div>
         </xsl:when>
         <xsl:otherwise>
           <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
         </xsl:otherwise>
        </xsl:choose>
        <p>You may safely close your browser or shut down your computer during this process, the system will keep running and be available when you return another time.</p>
        <xsl:call-template name="log" />
      </xsl:when>
      <xsl:when test="@code = 2">
        <div class="done"><xsl:value-of select="@message"/><input id="indexbutton" type="button" value="Return to projects" title="Leaves the project intact and returns you to the project list"/><input id="abortbutton" type="button" value="Cancel and delete project" /><input id="restartbutton" type="button" value="Discard output and restart" /></div>
        <xsl:call-template name="log" />
      </xsl:when>
      <xsl:otherwise>
        <div class="other"><xsl:value-of select="@message"/></div>
      </xsl:otherwise>
     </xsl:choose>
    </div>
</xsl:template>

<xsl:template name="log">
     <xsl:if test="log">
        <div id="statuslog">
            <table>
                <xsl:apply-templates select="log" />
            </table>
        </div>
     </xsl:if>
</xsl:template>

<xsl:template match="/clam/status/log">
    <tr><td class="time"><xsl:value-of select="@time" /></td><td class="message"><xsl:value-of select="." /></td></tr>
</xsl:template>

<xsl:template match="/clam/profiles">
        <div id="uploadarea">
            
            <div class="uploadform">
                <h3>Upload a file from disk</h3>
                <p>Use this to upload files from your computer to the system.</p>
                <!--
                <div id="simpleupload">
                 <form id="uploadform" method="POST" enctype="multipart/form-data" action="upload/">
                    <input type="hidden" name="uploadcount" value="1" />
                    <table>
                     <tr><th><label for="upload1">Upload file:</label></th><td><input type="file" name="upload1" /></td></tr>
                     <tr><th><label for="uploadformat1">Format:</label></th><td>
                        <select name="uploadformat1">
                        <xsl:for-each select="*">
                            <option><xsl:attribute name="value"><xsl:value-of select="name(.)" /></xsl:attribute><xsl:value-of select="@name" /><xsl:if test="@encoding"> [<xsl:value-of select="@encoding" />]</xsl:if></option>
                        </xsl:for-each>
                        </select>
                     </td></tr>
                     <tr><td></td><td><input id="uploadbutton" type="submit" value="Upload input file" /></td></tr>
                    </table>
                 </form>
                </div>
                -->

                <div id="clientupload">
                    <strong>Step 1)</strong><xsl:text> </xsl:text><em>First select what type of file you want to add:</em><xsl:text> </xsl:text><select id="uploadinputtemplate" class="inputtemplates"></select><br />
                    <strong>Step 2)</strong><xsl:text> </xsl:text><em>Set the metadata parameters for this type of file:</em><xsl:text> </xsl:text><div id="uploadparameters" class="parameters"><em>Select a type first</em></div>
                    <strong>Step 3)</strong><xsl:text> </xsl:text><input id="uploadbutton" class="uploadbutton" type="submit" value="Select and upload a file" />
                </div>
                <div id="uploadprogress">
                        <strong>Upload in progress... Please wait...</strong><br />
                        <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
                </div>
            

            </div>
            
            <h3>Grab a file from the web</h3>
            <div id="urlupload">
                <p>Retrieves an input file from another location on the web.</p>
                <strong>Step 1)</strong><xsl:text> </xsl:text><em>First select the desired input type:</em><xsl:text> </xsl:text><select id="urluploadinputtemplate" class="inputtemplates"></select><br />
                <strong>Step 2)</strong><xsl:text> </xsl:text><em>Set the metadata parameters for this type of file:</em><xsl:text> </xsl:text><div id="urluploadparameters" class="parameters"><em>Select a type first</em></div>
                <strong>Step 3)</strong><xsl:text> </xsl:text><em>Enter the URL where to retrieve the file</em><xsl:text> </xsl:text><input id="urluploadfile" value="http://" /><br />
                <strong>Step 4)</strong><xsl:text> </xsl:text><input id="urluploadsubmit" class="uploadbutton" type="submit" value="Retrieve and add file" />
            </div>
            
            <div id="urluploadprogress">
                        <strong>Download in progress... Please wait...</strong><br />
                        <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
            </div>    

            <h3>Add input from browser</h3>
            <p>You can create and add new files from within your browser: <button id="openeditor">Open Live Editor</button></p>
            <div id="mask"></div>
            <div id="editor">
                <h3>Add input from browser</h3>
                    <table>
                     <tr><th><label for="editorcontents">Input:</label></th><td><textarea id="editorcontents"></textarea></td></tr>                     
                     <tr><th><label for="editorinputtemplate">Input type:</label></th><td>
                      <select id="editorinputtemplate" class="inputtemplates"></select>
                     </td></tr>
                     <tr><th><label for="editorparameters">Parameters:</label></th><td>
                        <div id="editorparameters" class="parameters"><em>Select a type first</em></div>
                     </td></tr>
                     <tr><th><label for="editorfilename">Desired filename:</label></th><td><input id="editorfilename" /></td></tr>
                     <tr><th></th><td class="buttons"><input id="editorsubmit" class="uploadbutton" type="submit" value="Add to input files" /> <button id="canceleditor">Cancel</button></td></tr>
                    </table>
            </div>
            
        </div>
</xsl:template>



<!-- OBSOLETE
<xsl:template name="inputformats"> 
    <xsl:for-each select="/clam/inputformats/*">
        <option><xsl:attribute name="value"><xsl:value-of select="name(.)" /></xsl:attribute><xsl:value-of select="@name" /><xsl:if test="@encoding"> [<xsl:value-of select="@encoding" />]</xsl:if></option>
    </xsl:for-each>
</xsl:template>

<xsl:template name="outputformats">
    <xsl:for-each select="/clam/outputformats/*">
        <option><xsl:attribute name="value"><xsl:value-of select="name(.)" /></xsl:attribute><xsl:value-of select="@name" /><xsl:if test="@encoding"> [<xsl:value-of select="@encoding" />]</xsl:if></option>
    </xsl:for-each>
</xsl:template>
-->


<xsl:template match="/clam/input">
        <h2>Input</h2>
        
        <xsl:if test="/clam/corpora/corpus">
            <div id="corpusselection">
            <label>Input source: </label>
            <select onchange="setinputsource(this);">
                <option value="" selected="selected">Use uploaded files</option>
                <xsl:for-each select="/clam/corpora/corpus">
                    <option><xsl:attribute name="value"><xsl:value-of select="." /></xsl:attribute><xsl:value-of select="." /></option>
                </xsl:for-each>
            </select>
            </div>
        </xsl:if>

        <div id="inputfilesarea">
        <h3>Input files</h3>
        <table id="inputfiles" class="files">
            <thead>
                <tr>
                    <th>Input File</th>
                    <th>Template</th>
                    <th>Format</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <xsl:apply-templates select="file" /> 
            </tbody>
        </table>
        </div>
</xsl:template>

<xsl:template match="/clam/output">
    <div id="output" class="box">
        <h2>Output files</h2>
        <p>(Download all as archive: <a href="output/?format=zip">zip</a> | <a href="output/?format=tar.gz">tar.gz</a> | <a href="output/?format=tar.bz2">tar.bz2</a>)</p>
        <table id="outputfiles" class="files">
            <thead>
                <tr>
                    <th>Output File</th>
                    <th>Template</th>
                    <th>Format</th>
                    <th>Viewers</th>
                </tr>
            </thead>
            <tbody>
                <xsl:apply-templates select="file" />
            </tbody>
        </table>
    </div>
</xsl:template>

<xsl:template match="/clam/input/file">
    <tr>
        <td class="file"><a><xsl:attribute name="href"><xsl:value-of select="@href"/></xsl:attribute><xsl:value-of select="./name"/></a></td>
        <xsl:variable name="template" select="@template" />
        <td><xsl:value-of select="/clam/profiles/profile/input/InputTemplate[@id = $template]/@label"/></td>
        <td><xsl:value-of select="/clam/profiles/profile/input/InputTemplate[@id = $template]/@format"/></td>
        <td class="actions"><img src="{/clam/@baseurl}/static/delete.png" title="Delete this file">
            <xsl:attribute name="onclick">deleteinputfile('<xsl:value-of select="."/>');</xsl:attribute>
        </img></td>
    </tr>
</xsl:template>


<xsl:template match="/clam/output/file">
    <tr>
        
        <td class="file">
        <xsl:choose>
        <xsl:when test="./viewers/viewer[1]">
            <a><xsl:attribute name="href"><xsl:value-of select="@xlink:href" /></xsl:attribute><xsl:value-of select="."/></a>
        </xsl:when>
        <xsl:otherwise>
            <a><xsl:attribute name="href"><xsl:value-of select="@xlink:href" /></xsl:attribute><xsl:value-of select="./name"/></a>
        </xsl:otherwise>
        </xsl:choose>
        </td>

        <xsl:variable name="template" select="@template" />
        <td><xsl:value-of select="/clam/profiles/profile/output/OutputTemplate[@id = $template]/@label"/></td>
        <td><xsl:value-of select="/clam/profiles/profile/output/OutputTemplate[@id = $template]/@format"/></td>
        
        <td> <!--TODO: Readd viewer support -->
            <xsl:for-each select="./viewers/viewer">
                <a><xsl:attribute name="href"><xsl:value-of select="@href" />/<xsl:value-of select="@id" /></xsl:attribute><xsl:value-of select="." /></a> |
            </xsl:for-each>
            <a><xsl:attribute name="href"><xsl:value-of select="@href" /></xsl:attribute>Download</a>
            <xsl:if test="@template">
                <a><xsl:attribute name="href"><xsl:value-of select="@href" />/metadata</xsl:attribute>Metadata</a>                
            </xsl:if>
        </td>
    </tr>
</xsl:template>

<xsl:template match="/clam/parameters">
    <form method="POST" enctype="multipart/form-data" action="">
    <div id="parameters" class="box parameters">
        <h2>Parameter Selection</h2>

        <xsl:for-each select="parametergroup">
         <h3><xsl:value-of select="@name" /></h3>
         <table>
          <xsl:apply-templates />
         </table>
        </xsl:for-each>

        <input id="usecorpus" name="usecorpus" type="hidden" value="" />


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
        <div id="upload" class="box">
            <a href="../">Return to the project view</a>
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
    <xsl:when test="@validated = 'yes'">
        <li class="ok"><tt><xsl:value-of select="@name" /></tt>: OK</li>    
    </xsl:when>
    <xsl:otherwise>
        <li class="failed"><tt><xsl:value-of select="@name" /></tt>: Failed</li>    
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>


<xsl:template name="clamindex">
        <div id="header"><h1><xsl:value-of select="@name"/></h1><h2><xsl:value-of select="@project"/></h2></div>
        <div id="description" class="box">
              <xsl:value-of select="description" />   
        </div>
        <div id="startproject" class="box">
            <h3>Start a new Project</h3>    
                Project ID: <input id="projectname" type="projectname" value="" />
                <input id="startprojectbutton" type="button" value="Start project" />
        </div>
        <div id="index" class="box">
        <h2>Projects</h2>
        <table id="projects">
          <thead>
            <tr><th>Project ID</th><th>Last changed</th></tr>
          </thead>
          <tbody>
           <xsl:for-each select="projects/project">
            <tr><td><a><xsl:attribute name="href"><xsl:value-of select="." />/</xsl:attribute><xsl:value-of select="." /></a></td><td><xsl:value-of select="@time" /></td></tr>
           </xsl:for-each>
          </tbody>
        </table>
        </div>
</xsl:template>

</xsl:stylesheet>
