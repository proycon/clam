<?xml version="1.0" encoding="utf-8" ?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xlink="http://www.w3.org/1999/xlink">


<xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes" cdata-section-elements="script"/>

<xsl:include href="parameters.xsl" />

<xsl:template match="/clam">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <xsl:call-template name="head" />
  <body>
    <div id="gradient"></div>
    <div id="container">

        <div id="cover">
        <xsl:if test="/clam/coverurl != ''">
            <img src="{/clam/coverurl}" alt="Cover Image">
                <xsl:attribute name="style">
                <xsl:if test="contains(/clam/@interfaceoptions,'centercover')">display: block; margin-left: auto; margin-right: auto;</xsl:if>
                <xsl:if test="contains(/clam/@interfaceoptions,'coverheight64')">height: 64px;</xsl:if>
                <xsl:if test="contains(/clam/@interfaceoptions,'coverheight100')">height: 100px;</xsl:if>
                <xsl:if test="contains(/clam/@interfaceoptions,'coverheight128')">height: 128px;</xsl:if>
                <xsl:if test="contains(/clam/@interfaceoptions,'coverheight192')">height: 192px;</xsl:if>
                </xsl:attribute>
            </img>
        </xsl:if>
        </div>

        <xsl:call-template name="nav" />

        <xsl:choose>
         <xsl:when test="@project">

            <xsl:if test="/clam/@authentication != 'none' and /clam/@user != 'anonymous'">
             <xsl:call-template name="logout"/>
            </xsl:if>

            <xsl:choose>
                <xsl:when test="status/@code = 0">
                    <xsl:if test="/clam/customhtml">
                        <div id="customhtml" class="card">
                            <div class="card-body">
                            <xsl:value-of select="/clam/customhtml" disable-output-escaping="yes"/>
                            </div>
                        </div>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="status/@code = 2">
                    <xsl:if test="/clam/customhtml">
                        <div id="customhtml" class="card">
                            <div class="card-body">
                            <xsl:value-of select="/clam/customhtml" disable-output-escaping="yes"/>
                            </div>
                        </div>
                    </xsl:if>
                </xsl:when>
            </xsl:choose>

            <xsl:apply-templates select="status"/>
            <xsl:choose>
              <xsl:when test="status/@code = 0">
                <div id="input" class="card">
                 <div class="card-body">
                  <xsl:apply-templates select="input"/><!-- upload form transformed from input formats -->
                 </div>
                </div>
                <div id="profiles" class="card">
                 <div class="card-body">
                  <xsl:apply-templates select="profiles"/>
                 </div>
                </div>
                <xsl:apply-templates select="parameters"/>
              </xsl:when>
              <xsl:when test="status/@code = 2">
                <div id="input" class="card">
                    <div class="card-body">
                        <button id="toggleinputfiles" class="btn btn-outline-primary">Show input files</button>
                        <div style="clear: both"></div>
                        <div id="inputfilesarea" style="display: none">
                            <xsl:apply-templates select="input"/>
                        </div>
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
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title><xsl:value-of select="@name"/><xsl:if test="@project"> :: <xsl:value-of select="@project"/></xsl:if></title>


    <link rel="stylesheet" href="{/clam/@baseurl}/static/bootstrap.min.css" type="text/css" />
    <link rel="stylesheet" href="{/clam/@baseurl}/static/jquery.dataTables.min.css" type="text/css" />
    <link rel="stylesheet" href="{/clam/@baseurl}/static/open-iconic-bootstrap.min.css" type="text/css" />

    <link rel="stylesheet" href="{/clam/@baseurl}/static/base.css" type="text/css" />
    <link rel="stylesheet" href="{/clam/@baseurl}/static/fineuploader.css" type="text/css" />
    <link rel="stylesheet" href="{/clam/@baseurl}/style.css" type="text/css" />


    <script src="{/clam/@baseurl}/static/jquery-3.4.1.min.js"></script>
    <script src="{/clam/@baseurl}/static/popper.min.js"></script>
    <script src="{/clam/@baseurl}/static/jquery.dataTables.min.js"></script>
    <script src="{/clam/@baseurl}/static/bootstrap.min.js"></script>

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

    <xsl:if test="/clam/customcss">
    <style>
    <xsl:value-of select="/clam/customcss" />
    </style>
    </xsl:if>

  </head>
</xsl:template>

<xsl:template name="footer">
    <div id="footer" class="card">
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
            <xsl:if test="/clam/affiliation != ''">
                <br /><xsl:value-of select="/clam/affiliation" />
            </xsl:if>
        </p>


        <p>Powered by <strong>CLAM</strong> v<xsl:value-of select="/clam/@version" /> - Computational Linguistics Application Mediator<br />by Maarten van Gompel -
        <a href="https://proycon.github.io/clam">https://proycon.github.io/clam</a>
        <br /><a href="http://ru.nl/clst">Centre for Language and Speech Technology</a>, <a href="http://www.ru.nl">Radboud University Nijmegen</a><br />
        &amp; <a href="https://huc.knaw.nl">KNAW Humanities Cluster</a>
        </p>

        <span class="extracredits">
            <strong>CLAM</strong> is funded by <a href="http://www.clarin.nl/">CLARIN-NL</a> and its successor <a href="http://www.clariah.nl">CLARIAH</a>.
        </span>
    </div>

</xsl:template>

<xsl:template name="logout">
    <div class="card">
      <p>
        You are currently logged in as <em><xsl:value-of select="/clam/@user" /></em>. Make sure to <strong><a href="{/clam/@baseurl}/logout/">log out</a></strong> when you are done.
      </p>
    </div>
</xsl:template>

<xsl:template match="/clam/status">
    <div id="status" class="card">
     <div class="card-body">
     <h2 class="card-title">Status</h2>
     <xsl:choose>
      <xsl:when test="@code = 0">
  		<xsl:if test="@errors = 'yes'">
      		<div class="alert alert-danger">
            <strong>Error: </strong> <xsl:value-of select="@errormsg"/>
      		</div>
     	</xsl:if>
        <div id="actions">
        	<input id="deletebutton" class="btn btn-danger" type="button" value="Cancel and delete project" />
       	</div>
        <div id="statusmessage" class="alert alert-success"><xsl:value-of select="@message"/></div>

      </xsl:when>
      <xsl:when test="@code = 1">
        <div id="actions">
        	<input id="abortbutton" class="btn btn-danger" type="button" value="Abort execution" />
        </div>
  		<xsl:if test="@errors = 'yes'">
      		<div class="alert alert-danger">
            <strong>Error: </strong> <xsl:value-of select="@errormsg"/>
      		</div>
     	</xsl:if>
        <div id="statusmessage" class="running"><xsl:value-of select="@message"/></div>
        <xsl:choose>
         <xsl:when test="@completion > 0">
           <div class="progress">
               <div class="progress-bar" role="progressbar" aria-valuenow="{@completion}" aria-valuemin="0" aria-valuemax="100">
                   <xsl:attribute name="style">width: <xsl:value-of select="@completion" />%</xsl:attribute>
               </div>
            </div>
         </xsl:when>
         <xsl:otherwise>
           <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
         </xsl:otherwise>
        </xsl:choose>
        <p class="alert alert-info">You may safely close your browser or shut down your computer during this process, the system will keep running on the server and is available when you return another time.</p>

        <xsl:call-template name="log" />
      </xsl:when>
      <xsl:when test="@code = 2">
        <div id="actions">
            <input id="indexbutton" type="button" class="btn btn-primary" value="Return to project index" /><input id="deletebutton" class="btn btn-danger" type="button" value="Cancel and delete project" /><input id="restartbutton" type="button" class="btn btn-danger" value="Discard output and restart" />
        </div>
        <xsl:choose>
        <xsl:when test="@errors = 'yes'">
      		<div class="alert alert-danger">
                <strong>Error: </strong> <xsl:value-of select="@errormsg"/>
      		</div>
     	</xsl:when>
        <xsl:otherwise>
            <div id="statusmessage" class="alert alert-success"><xsl:value-of select="@message"/></div>
        </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="log" />
      </xsl:when>
      <xsl:otherwise>
        <div id="statusmessage" class="alert alert-info"><xsl:value-of select="@message"/></div>
      </xsl:otherwise>
     </xsl:choose>
     </div>
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

        <div class="card tab-card uploadform">

            <div class="card-header tab-card-header">
                <ul class="nav nav-tabs card-header-tabs">
                  <xsl:if test="profile/input/InputTemplate/inputsource|/clam/inputsources/inputsource">
                  <li class="nav-item">
                      <a class="nav-link text-primary" id="inputsources-tab" data-toggle="tab" href="#inputsources">
                          <span class="oi oi-cloud"></span> Add existing resources</a>
                  </li>
                  </xsl:if>
                  <xsl:if test="not(contains(/clam/@interfaceoptions,'disablefileupload'))">
                  <li class="nav-item">
                      <a class="nav-link text-primary" id="fileupload-tab" data-toggle="tab" href="#fileupload">
                          <span class="oi oi-data-transfer-upload"></span> Upload a file from disk</a>
                  </li>
                  </xsl:if>
                  <xsl:if test="contains(/clam/@interfaceoptions,'inputfromweb')">
                  <li class="nav-item">
                      <a class="nav-link text-primary" id="inputfromweb-tab" data-toggle="tab" href="#inputfromweb">
                          <span class="oi oi-cloud-download"></span> Grab a file from the web</a>
                  </li>
                  </xsl:if>
                  <xsl:if test="not(contains(/clam/@interfaceoptions,'disableliveinput'))">
                  <li class="nav-item">
                      <a class="nav-link text-primary" id="liveinput-tab" data-toggle="tab" href="#liveinput">
                          <span class="oi oi-pencil"></span> Add input directly</a>
                  </li>
                  </xsl:if>
                </ul>
            </div>

        <div class="tab-content" id="uploadtabs">

        <xsl:if test="profile/input/InputTemplate/inputsource|/clam/inputsources/inputsource">

            <div id="inputsources" class="tab-pane">
                <div class="card-body">

                    <h3 class="card-title">Add already available resources</h3>

                    <div id="inputsourceupload">
                            <strong>Step 1)</strong><xsl:text> </xsl:text><em>Select the resource you want to add:</em><xsl:text> </xsl:text>
                        <select id="uploadinputsource" class="form-control">
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
                        <strong>Step 2)</strong><xsl:text> </xsl:text><input id="uploadinputsourcebutton" class="btn btn-primary" type="submit" value="Add resource" />
                    </div>

                    <div id="inputsourceprogress">
                        <strong>Gathering files... Please wait...</strong><br />
                        <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
                    </div>
                </div>
            </div>

        </xsl:if>

        <xsl:if test="not(contains(/clam/@interfaceoptions,'disablefileupload'))">

            <div id="fileupload" class="tab-pane">
                <div class="card-body">
                    <h3 class="card-title"><span class="oi oi-data-transfer-upload"></span> Upload a file from disk</h3>

                    <p class="card-text">Use this to upload files from your computer to the system.</p>


                    <div id="clientupload">
                        <strong>Step 1)</strong><xsl:text> </xsl:text><em>First select what type of file you want to add:</em><xsl:text> </xsl:text><select id="uploadinputtemplate" class="inputtemplates form-control"></select><br />
                        <div id="uploadparameterswrapper">
                        <strong>Step 2)</strong><xsl:text> </xsl:text><em>Set the parameters (if any) for the file(s) you are about to upload:</em><xsl:text> </xsl:text><div id="uploadparameters" class="parameters"><span class="alert alert-info typefirst">Select a type first</span></div>
                        </div>
                        <strong>Step <span id="uploadparametersstep">3</span>)</strong><xsl:text> </xsl:text><em>Click the upload button below and then select one or more files (holding control), you can also drag &amp; drop files onto the button from an external file manager</em><xsl:text> </xsl:text>
                        <xsl:choose>
                        <xsl:when test="contains(/clam/@interfaceoptions,'simpleupload') or contains(/clam/@interfaceoptions,'secureonly')">
                            <input id="uploadbutton" class="btn btn-primary" type="submit" value="Select and upload a file" />
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


            </div>

        </xsl:if>

        <xsl:if test="contains(/clam/@interfaceoptions,'inputfromweb')">

            <div id="inputfromweb" class="tab-pane">
                <div class="card-body">

                    <h3 class="card-title"><span class="oi oi-cloud-download"></span> Grab a file from the web</h3>

                    <div id="urlupload">
                        <p>Retrieves an input file from another location on the web.</p>
                        <strong>Step 1)</strong><xsl:text> </xsl:text><em>First select the desired input type:</em><xsl:text> </xsl:text><select id="urluploadinputtemplate" class="inputtemplates form-control"></select><br />
                        <div id="urluploadparameterswrapper">
                        <strong>Step 2)</strong><xsl:text> </xsl:text><em>Set the parameters (if any) for the file you are adding:</em><xsl:text> </xsl:text><div id="urluploadparameters" class="parameters"><span class="alert alert-info typefirst">Select a type first</span></div>
                        </div>
                        <strong>Step <span id="urluploadparamtersstep">3</span>)</strong><xsl:text> </xsl:text><em>Enter the URL where to retrieve the file</em><xsl:text> </xsl:text><input id="urluploadfile" class="form-control" value="http://" /><br />
                        <strong>Step <span id="urluploadparamtersstep2">4</span>)</strong><xsl:text> </xsl:text><input id="urluploadsubmit" class="btn btn-primary" type="submit" value="Retrieve and add file" />
                    </div>

                    <div id="urluploadprogress">
                            <strong>Download in progress... Please wait...</strong><br />
                            <img class="progress" src="{/clam/@baseurl}/static/progress.gif" />
                    </div>

                </div>
            </div>

        </xsl:if>


        <xsl:if test="not(contains(/clam/@interfaceoptions,'disableliveinput'))">
            <div id="liveinput" class="tab-pane">

                <div class="card-body">


                    <h3 class="cardtitle"><span class="oi oi-pencil"></span> Add input directly</h3>

                    <p class="card-text">You can create and add new files on the spot from within your browser. Type your text, choose the desired input type, fill the necessary parameters and choose a filename. Press <em>"Add to files"</em> when all done.</p>

                    <div id="editor">
                        <table>
                         <tr><th><label for="editorcontents">Input text:</label></th><td><textarea id="editorcontents" class="form-control"></textarea></td></tr>
                         <tr><th><label for="editorinputtemplate">Input type:</label></th><td>
                          <select id="editorinputtemplate" class="inputtemplates form-control"></select>
                         </td></tr>
                         <tr id="editorparameterswrapper"><th><label for="editorparameters">Parameters:</label></th><td>
                            <div id="editorparameters" class="parameters"><span class="alert alert-info typefirst">Select a type first</span></div>
                         </td></tr>
                         <tr class="editorfilenamerow"><th><label for="editorfilename">Desired filename:</label></th><td><input id="editorfilename" class="form-control" /></td></tr>
                         <tr><th></th><td><input id="editorsubmit" class="btn btn-primary" type="submit" value="Add to input files" /></td></tr>
                        </table>
                    </div>
                </div>
            </div>
        </xsl:if>

        </div>

    </div>
    </div>
</xsl:template>


<xsl:template match="/clam/input">
    <h2 class="card-title">Input</h2>


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
        <h4>Input files</h4>
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
    <div id="output" class="card">
        <div class="card-body">
        <h2 class="card-title">Output files</h2>

        <p class="card-text">(Download all as archive:
        <a href="output/zip/">zip</a> | <a href="output/gz/">tar.gz</a> | <a href="output/bz2/">tar.bz2</a>)
        </p>

        <xsl:if test="/clam/forwarders">
            <p class="card-text">
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
    </div>
</xsl:template>

<xsl:template match="/clam/input/file">
    <tr>
      <td class="file"><a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="@xlink:href"/></xsl:attribute><xsl:value-of select="./name"/></a></td>
        <xsl:variable name="template" select="@template" />
        <xsl:variable name="format" select="/clam/profiles/profile/input/InputTemplate[@id = $template]/@format" />
        <td><xsl:value-of select="/clam/profiles/profile/input/InputTemplate[@id = $template]/@label"/></td>
        <td><xsl:value-of select="/clam/formats/format[@id = $format]/@name"/></td>
        <td class="actions"><xsl:attribute name="onclick">deleteinputfile('<xsl:value-of select="./name"/>');</xsl:attribute>
            <span class="oi oi-circle-x deletefile" title="Delete this file"></span>
        </td>
    </tr>
</xsl:template>


<xsl:template match="/clam/output/file">
    <tr>

        <td class="file">
        <xsl:choose>
            <xsl:when test="./viewers/viewer[1] and not(./viewers/viewer[1]/@allowdefault = 'false')">
            <a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="./viewers/viewer[1]/@xlink:href" /></xsl:attribute><xsl:value-of select="./name"/></a>
        </xsl:when>
        <xsl:otherwise>
            <a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="@xlink:href" /></xsl:attribute><xsl:value-of select="./name"/></a>
        </xsl:otherwise>
        </xsl:choose>
        </td>

        <xsl:variable name="template" select="@template" />
        <xsl:variable name="format" select="//OutputTemplate[@id = $template]/@format" />
        <td><xsl:value-of select="//OutputTemplate[@id = $template]/@label"/></td>
        <td><xsl:value-of select="/clam/formats/format[@id = $format]/@name"/></td>

        <td>
            <xsl:for-each select="./viewers/viewer">
                <xsl:if test="not(@more = '1' or @more = 'true' or @more = 'yes')">
                    <a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="@xlink:href" /></xsl:attribute><xsl:value-of select="." /></a><xsl:text> | </xsl:text>
                </xsl:if>
            </xsl:for-each>
            <a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="@xlink:href" /></xsl:attribute>Download</a>
            <xsl:if test="@template">
                <span class="moremenu"> | More...
                <ul class="bg-dark">
                <xsl:for-each select="./viewers/viewer">
                    <xsl:if test="@more = '1' or @more = 'true' or @more = 'yes'">
                        <li><a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="@xlink:href" /></xsl:attribute><xsl:value-of select="." /></a></li>
                    </xsl:if>
                </xsl:for-each>
                <li><a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="@xlink:href" />/share</xsl:attribute>Share</a></li>
                <li><a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="@xlink:href" />/shareonce</xsl:attribute>Share once</a></li>
                <li><a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="@xlink:href" />/metadata</xsl:attribute>Metadata</a></li>
                </ul>
                </span>
            </xsl:if>
        </td>
    </tr>
</xsl:template>

<xsl:template match="/clam/parameters">
    <form method="POST" enctype="multipart/form-data" action="">
    <div id="parameters" class="card parameters">
        <div class="card-body">
            <h2 class="card-title"><span class="oi oi-list"></span> Parameters</h2>

            <xsl:for-each select="parametergroup">
             <h4><xsl:value-of select="@name" /></h4>
             <table>
              <xsl:apply-templates />
             </table>
            </xsl:for-each>

            <input id="usecorpus" name="usecorpus" type="hidden" value="" />


            <div id="startbutton">
                <input type="submit" class="btn btn-primary btn-lg btn-block" value="Start" />
            </div>
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
        <div id="upload" class="card">
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

<xsl:template name="nav">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <a class="navbar-brand" href="#"><xsl:value-of select="/clam/@name" /> <xsl:if test="/clam/@project">:: <em><xsl:value-of select="/clam/@project" /></em></xsl:if></a>
        <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarcontent" aria-controls="navbarcontent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
      </button>

      <xsl:variable name="indexlabel">
          <xsl:choose>
              <xsl:when test="count(/clam/actions/action) > 0 and count(/clam/profiles/profile) > 0">
                  Actions&#160;&amp;&#160;Projects
              </xsl:when>
              <xsl:when test="count(/clam/profiles/profile) > 0">
                  Projects
              </xsl:when>
              <xsl:when test="count(/clam/actions/action) > 0">
                  Actions
              </xsl:when>
            </xsl:choose>
      </xsl:variable>


      <div class="collapse navbar-collapse" id="navbarcontent">
            <ul class="navbar-nav mr-auto">
                <xsl:if test="/clam/parenturl != ''">
                    <li class="nav-item"><a class="nav-link" href="{/clam/parenturl}"><span class="oi oi-home" /></a></li>
                </xsl:if>
                    <li class="nav-item active">
                        <xsl:attribute name="class">nav-item<xsl:if test="not(/clam/@project)"> active</xsl:if></xsl:attribute>
                        <a class="nav-link" href="{/clam/@baseurl}/"><xsl:if test="count(/clam/profiles/profile) > 0">1.&#160;</xsl:if><span class="oi oi-spreadsheet"></span>&#160;<xsl:value-of select="$indexlabel" /></a>
                    </li>
                <xsl:if test="count(/clam/profiles/profile) > 0">
                <xsl:choose>
                    <xsl:when test="@project and status/@code = 0">
                        <li class="nav-item active"><a class="nav-link" href="#" tabindex="-1" aria-disabled="false">2.&#160;<span class="oi oi-cloud-upload"></span>&#160;Staging</a></li>
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="true">3.&#160;<span class="oi oi-timer"></span>&#160;Runtime</a></li>
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="true">4.&#160;<span class="oi oi-cloud-download"></span>&#160;Results</a></li>
                    </xsl:when>
                    <xsl:when test="@project and status/@code = 1">
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="true">2.&#160;<span class="oi oi-cloud-upload"></span>&#160;Staging</a></li>
                        <li class="nav-item active"><a class="nav-link" href="#" tabindex="-1" aria-disabled="false">3.&#160;<span class="oi oi-timer"></span>&#160;Runtime</a></li>
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="true">4.&#160;<span class="oi oi-cloud-download"></span>&#160;Results</a></li>
                    </xsl:when>
                    <xsl:when test="@project and status/@code = 2">
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="false">2.&#160;<span class="oi oi-cloud-upload"></span>&#160;Staging</a></li>
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="true">3.&#160;<span class="oi oi-timer"></span>&#160;Runtime</a></li>
                        <li class="nav-item active"><a class="nav-link" href="#" tabindex="-1" aria-disabled="true">4.&#160;<span class="oi oi-cloud-download"></span>&#160;Results</a></li>
                    </xsl:when>
                    <xsl:otherwise>
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="false">2.&#160;<span class="oi oi-cloud-upload"></span>&#160;Staging</a></li>
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="true">3.&#160;<span class="oi oi-timer"></span>&#160;Runtime</a></li>
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="true">4.&#160;<span class="oi oi-cloud-download"></span>&#160;Results</a></li>
                    </xsl:otherwise>
                </xsl:choose>
                </xsl:if>
            </ul>
            <ul class="navbar-nav pull-right">
                <li class="nav-item"><a class="nav-link" href="{/clam/@baseurl}/info"><span class="oi oi-info"></span>&#160;REST&#160;API&#160;Specification</a></li>
                <li class="nav-item"><a class="nav-link" role="button"
                    tabindex="0" data-trigger="focus" data-toggle="popover"
                    data-content="{/clam/@user}" title="Current user"
                    data-placement="bottom"><span class="oi
                        oi-person"></span></a></li>
            </ul>
        </div>
    </nav>
</xsl:template>

<xsl:template name="clamindex">

        <xsl:if test="/clam/@authentication != 'none' and /clam/@user != 'anonymous'">
          <xsl:call-template name="logout"/>
        </xsl:if>

        <div id="description" class="card">
            <div class="card-body">
                <xsl:if test="/clam/version != '' or /clam/author != '' or /clam/url != '' or /clam/license != '' or /clam/email != '' or /clam/contact != ''">
                 <div id="systeminfo" class="card">
                     <div class="card-body">
                         <h5 class="card-title"><span class="oi oi-info" style="float: right"></span> System Information</h5>
                         <table>
                         <xsl:if test="/clam/version != ''">
                             <tr>
                                 <th>Version:</th>
                                 <td><xsl:value-of select="/clam/version" /></td>
                             </tr>
                         </xsl:if>
                         <xsl:if test="/clam/author != ''">
                             <tr>
                                 <th>Author(s):</th>
                                 <td><xsl:value-of select="/clam/author" /></td>
                             </tr>
                         </xsl:if>
                         <xsl:if test="/clam/affiliation != ''">
                             <tr>
                                 <th>Affiliation:</th>
                                 <td><xsl:value-of select="/clam/affiliation" /></td>
                             </tr>
                         </xsl:if>
                         <xsl:if test="/clam/url != ''">
                             <tr>
                                 <th>Website:</th>
                                 <td><a href="{/clam/url}"><xsl:value-of select="/clam/url" /></a></td>
                             </tr>
                         </xsl:if>
                         <xsl:if test="/clam/license != ''">
                             <tr>
                                 <th>License:</th>
                                 <td><xsl:value-of select="/clam/license" /></td>
                             </tr>
                         </xsl:if>
                         <xsl:if test="/clam/email != ''">
                             <tr>
                                 <th>Contact:</th>
                                 <td><a href="mailto:{/clam/email}"><xsl:value-of select="/clam/email" /></a></td>
                             </tr>
                         </xsl:if>
                         </table>
                    </div>
                 </div>
                 </xsl:if>
                 <p class="p-text"><xsl:value-of select="description" /></p>
                 <xsl:if test="/clam/customhtml">
                    <div id="customhtml">
                    <xsl:value-of select="/clam/customhtml" disable-output-escaping="yes" />
                    </div>
                 </xsl:if>
            </div>
        </div>


        <xsl:call-template name="actions" />

        <xsl:choose>
        <xsl:when test="/clam/@user = 'anonymous' and /clam/@authentication != 'none' and (/clam/profiles or /clam/actions[not(@allowanonymous='yes')])">
        <div id="porch" class="card">
            <div class="card-body">
                <p class="alert alert-info">
                You will be asked to authenticate when you continue to use the rest of this service, by clicking the button below.
                <xsl:if test="/clam/registerurl">
                If you do not have an account yet, you can <a href="{/clam/registerurl}">register here</a>.
                </xsl:if>
                </p>

                <a href="{/clam/@baseurl}/index/" class="btn btn-primary btn-lg btn-block" type="button">Continue</a>

                <xsl:if test="contains(/clam/@authentication,',basic')">
                    Or alternatively <a href="{/clam/@baseurl}/index/?requestauth=Basic">continue using fallback authentication</a> <em>(HTTP Basic Authentication)</em>
                </xsl:if>
            </div>
        </div>
        </xsl:when>
        <xsl:when test="count(/clam/profiles/profile) > 0">
        <div id="startproject" class="card">
            <div class="card-body">
                <h3 class="card-title">Start a new Project</h3>
            	<p class="card-text">A project is your personal workspace for a specific task; in a project you gather input files, set parameters for the system, monitor the system's progress and download and visualise your output files. Users can have and run multiple projects simultaneously. You can always come back to a project, regardless of the state it's in, until you explicitly delete it. To create a new project, enter a short unique identifier below <em>(no spaces or special characters allowed)</em> and press the button:</p>
                Project ID: <input id="projectname" class="form-control" type="projectname" value="" />
                <input id="startprojectbutton" class="btn btn-primary btn-lg btn-block" type="button" value="Create project" />
            </div>
        </div>

        <div id="index" class="card">
            <div class="card-body">
                <h2 class="card-title">Projects</h2>
                <table id="projects">
                  <thead>
                      <tr><th style="width: 50%;">Project ID</th><th>Status</th><th>Size</th><th>Last changed</th></tr>
                  </thead>
                  <tbody>
                   <xsl:for-each select="projects/project">
                       <tr>
                           <xsl:attribute name="id">projectrow_<xsl:value-of select='.' /></xsl:attribute>
                           <td><a class="text-primary"><xsl:attribute name="href"><xsl:value-of select="@xlink:href" />/</xsl:attribute><xsl:value-of select="." /></a>
                               <button class="btn btn-danger btn-sm quickdelete">
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
                    <button class="btn btn-outline-secondary" onclick="showquickdelete()">Show delete buttons</button>
                </div>
            </div>
        </div>
        </xsl:when>
        </xsl:choose>




</xsl:template>

<xsl:template name="actions">
    <xsl:variable name="anonymousonly" select="//clam/@user = 'anonymous' and //clam/@authentication != 'none'" />
    <xsl:if test="count(/clam/actions/action) > 0">
        <div id="actionindex" class="card parameters">
            <div class="card-body">
            <xsl:for-each select="/clam/actions/action">
                <xsl:if test="not($anonymousonly) or ($anonymousonly and ./@allowanonymous = 'yes')">
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
                        <input class="btn btn-primary btn-block" type="submit" style="margin-top: 10px;" value="Run" />
                    </form>
                </xsl:if>
            </xsl:for-each>
            </div>
        </div>
    </xsl:if>
</xsl:template>


</xsl:stylesheet>
