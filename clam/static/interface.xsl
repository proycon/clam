<?xml version="1.0" encoding="utf-8" ?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xlink="http://www.w3.org/1999/xlink">

<xsl:import href="parameters.xsl" />

<xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes" cdata-section-elements="script"/>

<xsl:template match="/clam">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <xsl:call-template name="head" />
  <body>
    <div id="gradient"></div>
    <div id="header"><h1><xsl:value-of select="@name"/></h1><xsl:if test="@project"><h2><xsl:value-of select="@project"/></h2></xsl:if></div>
    <div id="covershadow"></div>
    <div id="container">

        <xsl:choose>
         <xsl:when test="@project">
    		<div id="tabs">
    			<ol>
                    <xsl:choose>
                    <xsl:when test="/clam/@oauth_access_token = ''">
                      <li><a href="{/clam/@baseurl}/">1. Projects</a></li>
                    </xsl:when>
                    <xsl:otherwise>
                      <li><a href="{/clam/@baseurl}/?oauth_access_token={/clam/@oauth_access_token}">1. Projects</a></li>
                    </xsl:otherwise>
                    </xsl:choose>
				    <xsl:choose>
				        <xsl:when test="status/@code = 0">
				         <li class="active">2. Input &amp; Parameters</li>
				         <li class="disabled">3. Processing</li>
				         <li class="disabled">4. Output &amp; Visualisation</li>
				        </xsl:when>
				        <xsl:when test="status/@code = 1">
				         <li class="disabled">2. Input &amp; Parameters</li>
				         <li class="active">3. Processing</li>
				         <li class="disabled">4. Output &amp; Visualisation</li>
				        </xsl:when>
				        <xsl:when test="status/@code = 2">
				         <li class="disabled">2. Input &amp; Parameters</li>
				         <li class="disabled">3. Processing</li>
				         <li class="active">4. Output &amp; Visualisation</li>
				        </xsl:when>
				    </xsl:choose>

    			</ol>
    		</div>

          <xsl:if test="/clam/@oauth_access_token != ''">
            <xsl:call-template name="logout"/>
          </xsl:if>

            <xsl:choose>
                <xsl:when test="status/@code = 0">
                    <xsl:if test="/clam/customhtml">
                        <div id="customhtml" class="box">
                            <xsl:value-of select="/clam/customhtml" disable-output-escaping="yes"/>
                        </div>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="status/@code = 2">
                    <xsl:if test="/clam/customhtml">
                        <div id="customhtml" class="box">
                            <xsl:value-of select="/clam/customhtml" disable-output-escaping="yes"/>
                        </div>
                    </xsl:if>
                </xsl:when>
            </xsl:choose>

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
                <div id="input" class="box">
                    <button id="toggleinputfiles">Show input files</button>
                    <div style="clear: both"></div>
                    <div id="inputfilesarea" style="display: none">
                        <xsl:apply-templates select="input"/>
                    </div>
                </div>
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
    <xsl:if test="status/@code = 1 and (contains(/clam/@interfaceoptions,'secureonly') or contains(/clam/@interfaceoptions,'simplepolling'))" >
      <meta http-equiv="refresh" content="2" />
    </xsl:if>
    <title><xsl:value-of select="@name"/> :: <xsl:value-of select="@project"/></title>
    <link rel="stylesheet" href="{/clam/@baseurl}/static/base.css" type="text/css" />
    <link rel="stylesheet" href="{/clam/@baseurl}/static/fineuploader.css" type="text/css" />
    <link rel="stylesheet" href="{/clam/@baseurl}/static/table.css" type="text/css" />
    <link rel="stylesheet" href="{/clam/@baseurl}/style.css" type="text/css" />

    <script type="text/javascript" src="{/clam/@baseurl}/static/jquery-1.8.3.min.js" />
    <script type="text/javascript" src="{/clam/@baseurl}/static/jquery-ui-1.9.2.custom.min.js" />
    <script type="text/javascript" src="{/clam/@baseurl}/static/jquery.dataTables.min.js" />

    <script type="text/javascript" src="{/clam/@baseurl}/data.js" />

    <xsl:choose>
     <xsl:when test="contains(/clam/@interfaceoptions,'simplepolling')">
         <script type="text/javascript" src="{/clam/@baseurl}/static/ajaxupload.js" />
     </xsl:when>
     <xsl:otherwise>
         <script type="text/javascript" src="{/clam/@baseurl}/static/jquery.fineuploader-3.1.min.js" />
     </xsl:otherwise>
    </xsl:choose>
    <script type="text/javascript" src="{/clam/@baseurl}/static/clam.js" />

    <script type="text/javascript">
        <xsl:if test="status/@code = 1">
                stage = 1;
                progress = 0;
        </xsl:if>
        <xsl:if test="status/@code = 0">
                stage = 0;
        </xsl:if>
        <xsl:if test="status/@code = 2">
                stage = 2;
        </xsl:if>
        <xsl:if test="/clam/@project">
                project = '<xsl:value-of select="/clam/@project" />';
        </xsl:if>
        <xsl:if test="/clam/@accesstoken">
        		accesstoken = '<xsl:value-of select="/clam/@accesstoken" />';
        </xsl:if>
        <xsl:if test="/clam/@oauth_access_token">
        		oauth_access_token = '<xsl:value-of select="/clam/@oauth_access_token" />';
        </xsl:if>
        <xsl:choose>
        <xsl:when test="/clam/@user">
        		user = '<xsl:value-of select="/clam/@user" />';
        </xsl:when>
        <xsl:otherwise>
        		user = 'anonymous';
        </xsl:otherwise>
        </xsl:choose>

        simplepolling = false;
        simpleupload = false;
        preselectinputtemplate = false;
		<xsl:if test="contains(/clam/@interfaceoptions,'secureonly')">
			simplepolling = true;
			simpleupload = true;
		</xsl:if>
		<xsl:if test="contains(/clam/@interfaceoptions,'simplepolling')">
			simplepolling = true;
		</xsl:if>
		<xsl:if test="contains(/clam/@interfaceoptions,'simpleupload')">
			simpleupload = true;
		</xsl:if>
		<xsl:if test="contains(/clam/@interfaceoptions,'preselectinputtemplate')">
			preselectinputtemplate = true;
		</xsl:if>
        $(document).ready(function() {
            if ( (typeof(initclam) == 'undefined') )  {
                alert("Error loading clam.js . Try refreshing the page?");
            } else {
                initclam();
            }
        });

    </script>


  </head>
</xsl:template>

<xsl:template name="footer">
    <div id="footer" class="box">
        <p>
            <strong><xsl:value-of select="/clam/@name" /></strong>
            <xsl:if test="/clam/version != ''">
                - version <xsl:value-of select="/clam/version" />
            </xsl:if><br/>
            <xsl:if test="/clam/author != ''">
                <xsl:choose>
                    <xsl:when test="/clam/email != ''">
                        by <a href="mailto:{/clam/email}"><strong><em><xsl:value-of select="/clam/author" /></em></strong></a>
                    </xsl:when>
                    <xsl:otherwise>
                        by <strong><em><xsl:value-of select="/clam/author" /></em></strong>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
        </p>


        <p>Powered by <strong>CLAM</strong> v<xsl:value-of select="/clam/@version" /> - Computational Linguistics Application Mediator<br />by Maarten van Gompel -
        <a href="https://proycon.github.io/clam">https://proycon.github.io/clam</a>
        <br /><a href="http://ru.nl/clst">Centre for Language and Speech Technology</a>, <a href="http://www.ru.nl">Radboud University Nijmegen</a></p>

        <span class="extracredits">
            <strong>CLAM</strong> is funded by <a href="http://www.clarin.nl/">CLARIN-NL</a> and its successor <a href="http://www.clariah.nl">CLARIAH</a>.
        </span>
    </div>

</xsl:template>

<xsl:template name="logout">
    <div class="box">
      <p>
        You are currently logged in as <em><xsl:value-of select="/clam/@user" /></em>. Make sure to <strong><a href="{/clam/@baseurl}/logout/?oauth_access_token={/clam/@oauth_access_token}">log out</a></strong> when you are done.
      </p>
    </div>
</xsl:template>

<xsl:template match="/clam/status">
    <div id="status" class="box">
     <h2>Status</h2>
     <xsl:choose>
      <xsl:when test="@code = 0">
        <div id="actions">
        	<input id="deletebutton" type="button" value="Cancel and delete project" />
       	</div>
  		<xsl:if test="@errors = 'yes'">
      		<div id="errorbox" class="error">
            <strong>Error: </strong> <xsl:value-of select="@errormsg"/>
      		</div>
     	</xsl:if>
        <div id="statusmessage" class="ready"><xsl:value-of select="@message"/></div>

      </xsl:when>
      <xsl:when test="@code = 1">
        <div id="actions">
        	<input id="abortbutton" type="button" value="Abort execution" />
        </div>
  		<xsl:if test="@errors = 'yes'">
      		<div id="errorbox" class="error">
            <strong>Error: </strong> <xsl:value-of select="@errormsg"/>
      		</div>
     	</xsl:if>
        <div id="statusmessage" class="running"><xsl:value-of select="@message"/></div>
        <xsl:choose>
         <xsl:when test="@completion > 0">
           <div id="progressbar">
           </div>
         </xsl:when>
         <xsl:otherwise>
           <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
         </xsl:otherwise>
        </xsl:choose>
        <p>You may safely close your browser or shut down your computer during this process, the system will keep running on the server and is available when you return another time.</p>

        <xsl:call-template name="log" />
      </xsl:when>
      <xsl:when test="@code = 2">
        <div id="actions">
            <input id="indexbutton" type="button" value="Done, return to project index" /><input id="deletebutton" type="button" value="Cancel and delete project" /><input id="restartbutton" type="button" value="Discard output and restart" />
        </div>
        <xsl:if test="@errors = 'yes'">
      		<div id="errorbox" class="error">
            <strong>Error: </strong> <xsl:value-of select="@errormsg"/>
      		</div>
     	</xsl:if>
        <div id="statusmessage" class="done"><xsl:value-of select="@message"/></div>
        <xsl:call-template name="log" />
      </xsl:when>
      <xsl:otherwise>
        <div id="statusmessage" class="other"><xsl:value-of select="@message"/></div>
      </xsl:otherwise>
     </xsl:choose>

    </div>
</xsl:template>

<xsl:template name="log">
        <div id="statuslog">
            <table id="statuslogtable">
                <xsl:apply-templates select="log" />
            </table>
        </div>
</xsl:template>

<xsl:template match="/clam/status/log">
    <tr><td class="time"><xsl:value-of select="@time" /></td><td class="message"><xsl:value-of select="." /></td></tr>
</xsl:template>

<xsl:template match="/clam/profiles">
        <div id="uploadarea">

            <xsl:if test="profile/input/InputTemplate/inputsource|/clam/inputsources/inputsource">

            <h3>Add already available resources</h3>

            <div id="inputsourceupload">
                    <strong>Step 1)</strong><xsl:text> </xsl:text><em>Select the resource you want to add:</em><xsl:text> </xsl:text>
                    <select id="uploadinputsource">
                    <xsl:for-each select="/clam/inputsources/inputsource">
                        <option><xsl:attribute name="value"><xsl:value-of select="./@id" /></xsl:attribute><xsl:value-of select="." /></option>
                    </xsl:for-each>
                    <xsl:for-each select="profile">
                    <xsl:for-each select="input/InputTemplate">
                        <xsl:for-each select="inputsource">
                            <option value="{@id}"><xsl:value-of select="../@label" /> - <xsl:value-of select="." /></option>
                        </xsl:for-each>
                    </xsl:for-each>
                    </xsl:for-each>
                    </select><br />
                    <strong>Step 2)</strong><xsl:text> </xsl:text><input id="uploadinputsourcebutton" class="uploadbutton" type="submit" value="Add resource" />
            </div>
            <div id="inputsourceprogress">
                <strong>Gathering files... Please wait...</strong><br />
                <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
            </div>

            </xsl:if>

            <xsl:if test="not(contains(/clam/@interfaceoptions,'disablefileupload'))">

            <div class="uploadform">
                <h3>Upload a file from disk</h3>
                <p>Use this to upload files from your computer to the system.</p>


                <div id="clientupload">
                    <strong>Step 1)</strong><xsl:text> </xsl:text><em>First select what type of file you want to add:</em><xsl:text> </xsl:text><select id="uploadinputtemplate" class="inputtemplates"></select><br />
                    <strong>Step 2)</strong><xsl:text> </xsl:text><em>Set the parameters for the file(s) you are about to upload:</em><xsl:text> </xsl:text><div id="uploadparameters" class="parameters"><em>Select a type first</em></div>
                    <strong>Step 3)</strong><xsl:text> </xsl:text><em>Click the upload button below and then select one or more files (holding control), you can also drag &amp; drop files onto the button from an external file manager</em><xsl:text> </xsl:text>
                    <xsl:choose>
                    <xsl:when test="contains(/clam/@interfaceoptions,'simpleupload') or contains(/clam/@interfaceoptions,'secureonly')">
                    	<input id="uploadbutton" class="uploadbutton" type="submit" value="Select and upload a file" />
                    </xsl:when>
                    <xsl:otherwise>
                    	<div id="fineuploadarea"></div>
                    </xsl:otherwise>
                    </xsl:choose>
                </div>
                <div id="uploadprogress">
                        <strong>Upload in progress... Please wait...</strong><br />
                        <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
                </div>


            </div>

            </xsl:if>

            <xsl:if test="contains(/clam/@interfaceoptions,'inputfromweb')">

            <h3>Grab a file from the web</h3>
            <div id="urlupload">
                <p>Retrieves an input file from another location on the web.</p>
                <strong>Step 1)</strong><xsl:text> </xsl:text><em>First select the desired input type:</em><xsl:text> </xsl:text><select id="urluploadinputtemplate" class="inputtemplates"></select><br />
                <strong>Step 2)</strong><xsl:text> </xsl:text><em>Set the parameters for the file you are adding:</em><xsl:text> </xsl:text><div id="urluploadparameters" class="parameters"><em>Select a type first</em></div>
                <strong>Step 3)</strong><xsl:text> </xsl:text><em>Enter the URL where to retrieve the file</em><xsl:text> </xsl:text><input id="urluploadfile" value="http://" /><br />
                <strong>Step 4)</strong><xsl:text> </xsl:text><input id="urluploadsubmit" class="uploadbutton" type="submit" value="Retrieve and add file" />
            </div>

            </xsl:if>

            <div id="urluploadprogress">
                        <strong>Download in progress... Please wait...</strong><br />
                        <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
            </div>

 			<xsl:if test="not(contains(/clam/@interfaceoptions,'disableliveinput'))">

            <h3>Add input from browser</h3>
            <p>You can create and add new files on the spot from within your browser. Type your text, choose the desired input type, fill the necessary parameters and choose a filename. Press <em>"Add to files"</em> when all done.</p>

			<div id="editor">
                <table>
                 <tr><th><label for="editorcontents">Input text:</label></th><td><textarea id="editorcontents"></textarea></td></tr>
                 <tr><th><label for="editorinputtemplate">Input type:</label></th><td>
                  <select id="editorinputtemplate" class="inputtemplates"></select>
                 </td></tr>
                 <tr><th><label for="editorparameters">Parameters:</label></th><td>
                    <div id="editorparameters" class="parameters"><em>Select a type first</em></div>
                 </td></tr>
                 <tr class="editorfilenamerow"><th><label for="editorfilename">Desired filename:</label></th><td><input id="editorfilename" /></td></tr>
                 <tr><th></th><td><input id="editorsubmit" class="uploadbutton" type="submit" value="Add to input files" /></td></tr>
                </table>
            </div>

            </xsl:if>

        </div>
</xsl:template>


<xsl:template match="/clam/input">
        <h2>Input</h2>


        <!--
        <xsl:if test="/clam/inputsources/inputsource">
            <div id="corpusselection">
            <label>Add files from pre-installed input source: </label>
            <select id="inputsource" onchange="setinputsource(this);">
                <xsl:for-each select="/clam/inputsources/inputsource">
                    <option><xsl:attribute name="value"><xsl:value-of select="./@id" /></xsl:attribute><xsl:value-of select="." /></option>
                </xsl:for-each>
            </select>
            <button id="inputsourceselect">Copy files</button>
            </div>
        </xsl:if>
        -->

        <div id="inputfilesarea">
        <h3>Input files</h3>
        <table id="inputfiles" class="files">
            <thead>
                <tr>
                    <th style="width: 30%">Input File</th>
                    <th style="width: 30%">Template</th>
                    <th style="width: 30%">Format</th>
                    <th style="width: 10%">Actions</th>
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

        <p>(Download all as archive:
          <xsl:choose>
          <xsl:when test="/clam/@oauth_access_token = ''">
            <a href="output/zip/">zip</a> | <a href="output/gz/">tar.gz</a> | <a href="output/bz2/">tar.bz2</a>)
          </xsl:when>
          <xsl:otherwise>
            <a href="output/zip/?oauth_access_token={/clam/@oauth_access_token}">zip</a> | <a href="output/gz/?oauth_access_token={/clam/@oauth_access_token}">tar.gz</a> | <a href="output/bz2/?oauth_access_token={/clam/@oauth_access_token}">tar.bz2</a>)
          </xsl:otherwise>
          </xsl:choose>
        </p>

        <xsl:if test="/clam/forwarders">
            <p>
            Forward all output to:
            <ul>
                <xsl:for-each select="/clam/forwarders/forwarder">
                    <li><a href="{./@url}"><xsl:value-of select="./@name" /></a> - <xsl:value-of select="./@description" /></li>
                </xsl:for-each>
            </ul>
            </p>
        </xsl:if>

        <table id="outputfiles" class="files">
            <thead>
                <tr>
                    <th style="width: 35%">Output File</th>
                    <th style="width: 25%">Template</th>
                    <th style="width: 20%">Format</th>
                    <th style="width: 25%">Viewers</th>
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
      <td class="file"><a><xsl:attribute name="href"><xsl:value-of select="@xlink:href"/><xsl:if test="/clam/@oauth_access_token != ''">?oauth_access_token=<xsl:value-of select="/clam/@oauth_access_token"/></xsl:if></xsl:attribute><xsl:value-of select="./name"/></a></td>
        <xsl:variable name="template" select="@template" />
        <td><xsl:value-of select="/clam/profiles/profile/input/InputTemplate[@id = $template]/@label"/></td>
        <td><xsl:value-of select="/clam/profiles/profile/input/InputTemplate[@id = $template]/@format"/></td>
        <td class="actions"><img src="{/clam/@baseurl}/static/delete.png" title="Delete this file">
            <xsl:attribute name="onclick">deleteinputfile('<xsl:value-of select="./name"/>');</xsl:attribute>
        </img></td>
    </tr>
</xsl:template>


<xsl:template match="/clam/output/file">
    <tr>

        <td class="file">
        <xsl:choose>
        <xsl:when test="./viewers/viewer[1]">
            <a><xsl:attribute name="href"><xsl:value-of select="./viewers/viewer[1]/@xlink:href" /><xsl:if test="/clam/@oauth_access_token != ''">?oauth_access_token=<xsl:value-of select="/clam/@oauth_access_token"/></xsl:if></xsl:attribute><xsl:value-of select="./name"/></a>
        </xsl:when>
        <xsl:otherwise>
            <a><xsl:attribute name="href"><xsl:value-of select="@xlink:href" /><xsl:if test="/clam/@oauth_access_token != ''">?oauth_access_token=<xsl:value-of select="/clam/@oauth_access_token"/></xsl:if></xsl:attribute><xsl:value-of select="./name"/></a>
        </xsl:otherwise>
        </xsl:choose>
        </td>

        <xsl:variable name="template" select="@template" />
        <td><xsl:value-of select="//OutputTemplate[@id = $template]/@label"/></td>
        <td><xsl:value-of select="//OutputTemplate[@id = $template]/@format"/></td>

        <td>
            <xsl:for-each select="./viewers/viewer">
                <a><xsl:attribute name="href"><xsl:value-of select="@xlink:href" /><xsl:if test="/clam/@oauth_access_token != ''">?oauth_access_token=<xsl:value-of select="/clam/@oauth_access_token"/></xsl:if></xsl:attribute><xsl:value-of select="." /></a><xsl:text> | </xsl:text>
            </xsl:for-each>
            <a><xsl:attribute name="href"><xsl:value-of select="@xlink:href" /><xsl:if test="/clam/@oauth_access_token != ''">?oauth_access_token=<xsl:value-of select="/clam/@oauth_access_token"/></xsl:if></xsl:attribute>Download</a>
            <xsl:if test="@template">
                <xsl:text> | </xsl:text>
                <a><xsl:attribute name="href"><xsl:value-of select="@xlink:href" />/metadata<xsl:if test="/clam/@oauth_access_token != ''">?oauth_access_token=<xsl:value-of select="/clam/@oauth_access_token"/></xsl:if></xsl:attribute>Metadata</a>
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
            <xsl:choose>
            <xsl:when test="/clam/@oauth_access_token = ''">
              <a href="../">Return to the project view</a>
            </xsl:when>
            <xsl:otherwise>
              <a href="../?oauth_access_token={/clam/@oauth_access_token}">Return to the project view</a>
            </xsl:otherwise>
            </xsl:choose>
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

   		<div id="tabs">
			<ol>
                <xsl:choose>
                <xsl:when test="/clam/@oauth_access_token = ''">
                  <li class="active"><a href="{/clam/@baseurl}/">1. Projects</a></li>
                </xsl:when>
                <xsl:otherwise>
                  <li class="active"><a href="{/clam/@baseurl}/?oauth_access_token={/clam/@oauth_access_token}">1. Projects</a></li>
                </xsl:otherwise>
                </xsl:choose>
				<li class="disabled">2. Input &amp; Parameters</li>
				<li class="disabled">3. Processing</li>
				<li class="disabled">4. Output &amp; Visualisation</li>
			</ol>
		</div>

        <xsl:if test="/clam/@oauth_access_token != ''">
          <xsl:call-template name="logout"/>
        </xsl:if>

        <div id="description" class="box">
         <xsl:value-of select="description" />
        </div>

        <xsl:if test="/clam/customhtml">
            <div id="customhtml" class="box">
                <xsl:value-of select="/clam/customhtml" disable-output-escaping="yes" />
            </div>
        </xsl:if>

        <xsl:if test="count(/clam/actions/action) > 0">
            <div id="actionindex" class="box parameters">
                <h2>Actions</h2>
                <xsl:for-each select="/clam/actions/action">
                    <h3><xsl:value-of select="./@name" /></h3>
                    <p><xsl:value-of select="./@description" /></p>
                    <form action="{/clam/@baseurl}/actions/{./@id}/">
                        <xsl:choose>
                            <xsl:when test="./@method = 'POST'">
                                <xsl:attribute name="method">POST</xsl:attribute>
                                <xsl:attribute name="enctype">multipart/form-data</xsl:attribute>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:attribute name="method">GET</xsl:attribute>
                                <xsl:attribute name="enctype">application/x-www-form-urlencoded</xsl:attribute>
                            </xsl:otherwise>
                        </xsl:choose>
                        <table>
                            <xsl:apply-templates />
                        </table>
                        <input type="submit" class="submitaction" value="Submit" />
                    </form>
                </xsl:for-each>
            </div>
        </xsl:if>

        <xsl:if test="count(/clam/profiles/profile) > 0">
        <div id="startproject" class="box">
            <h3>Start a new Project</h3>
            	<p>A project is your personal workspace for a specific task; in a project you gather input files, set parameters for the system, monitor the system's progress and download and visualise your output files. Users can have and run multiple projects simultaneously. You can always come back to a project, regardless of the state it's in, until you explicitly delete it. To create a new project, enter a short unique identifier below <em>(no spaces or special characters allowed)</em>:</p>
                Project ID: <input id="projectname" type="projectname" value="" />
                <input id="startprojectbutton" type="button" value="Create project" />
        </div>
        <div id="index" class="box">
        <h2>Projects</h2>
        <table id="projects">
          <thead>
              <tr><th style="width: 50%;">Project ID</th><th>Status</th><th>Size</th><th>Last changed</th></tr>
          </thead>
          <tbody>
           <xsl:for-each select="projects/project">
               <tr>
                   <xsl:attribute name="id">projectrow_<xsl:value-of select='.' /></xsl:attribute>
                   <td><a><xsl:attribute name="href"><xsl:value-of select="@xlink:href" />/<xsl:if test="/clam/@oauth_access_token != ''">?oauth_access_token=<xsl:value-of select="/clam/@oauth_access_token"/></xsl:if></xsl:attribute><xsl:value-of select="." /></a>
                       <button class="quickdelete">
                           <xsl:attribute name="onclick">quickdelete('<xsl:value-of select='.' />');</xsl:attribute>
                           Delete</button>
                   </td>
                   <td>
                       <xsl:choose>
                           <xsl:when test="@status = 0">
                               <span class="staging">staging</span>
                           </xsl:when>
                       </xsl:choose>
                       <xsl:choose>
                           <xsl:when test="@status = 1">
                               <span class="running">running</span>
                           </xsl:when>
                       </xsl:choose>
                       <xsl:choose>
                           <xsl:when test="@status = 2">
                               <span class="done">done</span>
                           </xsl:when>
                       </xsl:choose>
                    </td>
                   <td><xsl:value-of select="@size" /> MB</td>
                   <td><xsl:value-of select="@time" /></td>
               </tr>
           </xsl:for-each>
          </tbody>
        </table>
        <div class="diskusage">
            <span>Disk size used: <xsl:value-of select="/clam/projects/@totalsize" /> MB</span><br />
            <button onclick="showquickdelete()">Show delete buttons</button>
        </div>
        </div>
        </xsl:if>



</xsl:template>

</xsl:stylesheet>
