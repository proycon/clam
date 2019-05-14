<?xml version="1.0" encoding="utf-8" ?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xlink="http://www.w3.org/1999/xlink">

<xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes" cdata-section-elements="script"/>

<xsl:template match="/clam">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <xsl:call-template name="head" />
  <body>
    <div id="container">
    	<div id="header"><h1><xsl:value-of select="@name"/></h1></div>

    	<div class="box">
    	 <h3>Introduction</h3>
    	 <p>
           This is the info page for the <em><xsl:value-of select="@name"/></em> webservice, a <a href="https://proycon.github.io/clam/">CLAM</a>-based webservice. This page contains some technical information useful for users wanting to interface with this webservice. The  <em><xsl:value-of select="@name"/></em> webservice is a <a href="http://en.wikipedia.org/wiki/REST">RESTful</a> webservice, which implies that usage of the four HTTP verbs (<tt>GET, POST, PUT, DELETE</tt>) on pre-defined URLs is how you can communicate with it. In turn, the response will be a standard HTTP response code along with content in CLAM XML, CLAM Upload XML, or CLAM Metadata XML format where applicable. It is recommended to read the <a href="https://proycon.github.io/clam/">CLAM manual</a> to get deeper insight into the operation of CLAM webservices.
    	 </p>
		</div>

		<div id="description" class="box">
		 <h3>Description of <xsl:value-of select="@name"/></h3>
         <xsl:value-of select="description" />
        </div>

        <div id="restspec" class="box">
    	 <h3>RESTful Specification</h3>

         <p>A full generic RESTful specification for CLAM can be found in Appendix A of the <a href="https://proycon.github.io/clam">CLAM manual</a>. The procedure specific to <em><xsl:value-of select="@name"/></em> is described below. Clients interfacing with this webservice should follow this procedure:
    	 </p>

         <xsl:if test="count(/clam/profiles/profile) > 0">

         <h4>Project Paradigm</h4>

    	 <ol>
    		<li><strong>Create a <em>project</em></strong> - Issue a <tt>HTTP PUT</tt> on <tt><xsl:value-of select="@baseurl"/>/<em>{yourprojectname}</em></tt>
				<ul>
					<li>Will respond with <tt>HTTP 201 Created</tt> if successful.</li>
                    <li>Will respond with <tt>HTTP 401 Unauthorized</tt> if incorrect or no user credentials were passed. User credentials have to be passed using <xsl:call-template name="authtype" /></li>
					<li>Will respond with <tt>HTTP 403 Permission Denied</tt> if you specified if an error arises, most often due to an invalid Project ID; certain characters including spaces, slashes and ampersands, are not allowed.</li>
				</ul>
                Curl example: <tt>curl <xsl:call-template name="curlauth" /> -v -X PUT <xsl:value-of select="@baseurl"/>/<em>$yourprojectname</em></tt>
    		</li>
    		<li><strong>Upload one or more files</strong> - Issue a <tt>HTTP POST</tt> on <tt><xsl:value-of select="@baseurl"/>/<em>{yourprojectname}</em>/input/<em>{filename}</em></tt>. The POST request takes the following parameters:
    			<ul>
    				<li><tt>inputtemplate</tt> - The input template for this upload, determines the type of file that is expected. The <em><xsl:value-of select="@name"/></em> webservice defines the following Input Templates (grouped per profile):
                    <ol>
                        <xsl:for-each select="//profile">
                          <li>Profile #<xsl:value-of select="position()" /><ul>
                          <xsl:for-each select=".//InputTemplate">
                              <li><tt>inputtemplate=<span style="color: blue"><xsl:value-of select="@id" /></span></tt> - <strong><xsl:value-of select="@label" /> (<em><xsl:value-of select="@format" /></em>)</strong>. <xsl:if test=".//*/@id">If you use this input template you can specify the following extra parameters:
                                    <ul>
                                     <xsl:apply-templates />
                                    </ul>
                                </xsl:if></li>
                          </xsl:for-each>
                          </ul></li>
                        </xsl:for-each>
                    </ol>
    				</li>
    				<li><tt>file</tt> - HTTP file data.</li>
    				<li><tt>contents</tt> - full string contents of the file (can be used as an alternative to of file)</li>
    				<li><tt>url</tt> - URL to the input file, will be grabbed from the web (alternative to file)</li>
    				<li><tt>metafile</tt> - HTTP file data of a file in CLAM Metadata XML format, specifying metadata for this file (for advanced use)</li>
    				<li><tt>metadata</tt> - As above, but string contents instead of HTTP file (for advanced use)</li>
                </ul>
    			<br /><em>Responses</em>:
    			<ul>
					<li>Will respond with <tt>HTTP 200 OK</tt> if successful, and returns CLAM Upload XML with details on the uploaded files (they may have been renamed automatically)</li>
					<li>Will respond with <tt>HTTP 401 Unauthorized</tt> if incorrect or no user credentials were passed. User credentials have to be passed using <xsl:call-template name="authtype" /></li>
					<li>Will respond with <tt>HTTP 403 Permission Denied</tt> if the upload is not valid, the file may not be of the correct type, have an invalid name, or there may be problems with specified parameters for the file. Returns CLAM Upload XML with the specific details</li>
					<li>Will respond with <tt>HTTP 404 Not Found</tt> if the project does not exist</li>
                </ul><br/>
                Curl example: <tt>curl <xsl:call-template name="curlauth" /> -v -F "inputtemplate=<em>$inputtemplate</em>" -F "file=@<em>/path/to/file</em>" <xsl:value-of select="@baseurl"/>/<em>$yourprojectname</em>/input/<em>$filename</em></tt>  (further parameters are passed similarly with -F)
    		</li>

            <li><strong>Start project execution with specified parameters</strong> - Issue a <tt>HTTP POST</tt> on <tt><xsl:value-of select="@baseurl"/>/<em>{yourprojectname}</em>/</tt>. <xsl:if test=".//parametergroup/*/@id">The POST request takes the following parameters:
    			<ul>
                    <xsl:for-each select="//parametergroup">
                        <xsl:apply-templates />
                    </xsl:for-each>
				</ul>
            </xsl:if>
				<br /><em>Responses:</em>
				<ul>
					<li>Will respond with <tt>HTTP 202 Accepted</tt> if successful, and returns the CLAM XML for the project's current state.</li>
					<li>Will respond with <tt>HTTP 401 Unauthorized</tt> if incorrect or no user credentials were passed. User credentials have to be passed using <xsl:call-template name="authtype" /></li>
					<li>Will respond with <tt>HTTP 403 Permission Denied</tt> if the system does not have sufficient files uploaded to run, or if there are parameter errors. Will return CLAM XML with the project's current state, including parameter errors. In the CLAM XML response, <tt>/CLAM/status/@errors</tt> (XPath) will be <em>yes</em> if errors occurred, <em>no</em> otherwise.</li>
					<li>Will respond with <tt>HTTP 404 Not Found</tt> if the project does not exist</li>
                </ul><br/>
                Curl example: <tt>curl <xsl:call-template name="curlauth" /> -v -X POST <xsl:value-of select="@baseurl"/>/<em>$yourprojectname</em>/</tt>  (further parameters are passed similarly with <tt>-d "<em>$parameter</em>=<em>$value</em>"</tt>, can be issued multiple times)
			</li>
			<li><strong>Poll the project status with a regular interval and check its status until it is flagged as finished</strong> - Issue (with a regular interval) a <tt>HTTP GET</tt> on <tt><xsl:value-of select="@baseurl"/>/<em>{yourprojectname}</em>/</tt> .
			<ul>
			<li>Will respond with <tt>HTTP 200 OK</tt> if successful, and returns the CLAM XML for the project's current state. The state of the project is stored in the CLAM XML response, in <tt>/CLAM/status/@code/</tt> (XPath), this code takes on one of three values:
			<ul>
				<li>0 - The project is in an accepting state, accepting file uploads and waiting to be started</li>
				<li>1 - The project is in execution</li>
				<li>2 - The project has finished</li>
			</ul>
			</li>
			<li>Will respond with <tt>HTTP 401 Unauthorized</tt> if incorrect or no user credentials were passed. User credentials have to be passed using <xsl:call-template name="authtype" /></li>
			<li>Will respond with <tt>HTTP 404 Not Found</tt> if the project does not exist</li>
            </ul><br/>
            Curl example (getting project state only, no interpretation): <tt>curl <xsl:call-template name="curlauth" /> -v -X GET <xsl:value-of select="@baseurl"/>/<em>$yourprojectname</em></tt>
			</li>
			<li><strong>Retrieve the desired output file(s)</strong> - Issue a <tt>HTTP GET</tt> on <tt><xsl:value-of select="@baseurl"/>/<em>{yourprojectname}</em>/output/<em>{outputfilename}</em></tt>.  A list of available output files can be obtained by querying the project's state (HTTP GET on <tt><xsl:value-of select="@baseurl"/>/<em>{yourprojectname}</em>/</tt>) and iterating over <tt>/CLAM/output/file/name</tt> (XPath). A <tt>template</tt> attribute will be available on these nodes indicating what output template was responsible for generating this file. The following output templates are defined for this webservice (grouped per profile):
				<ol>
					<xsl:for-each select="//profile">
                      <li>Profile #<xsl:value-of select="position()" /><ul>
					  <xsl:for-each select=".//OutputTemplate">
                          <li><tt><xsl:value-of select="@id" /></tt>  - <strong><xsl:value-of select="@label" /> (<em><xsl:value-of select="@format" /></em>)</strong> <xsl:if test="@extension"> - Extension: <tt>*.<xsl:value-of select="@extension" /></tt></xsl:if> <xsl:if test="@filename"> - File name: <tt><xsl:value-of select="@filename" /></tt></xsl:if> <xsl:if test="@mimetype"> - MIME Type: <tt><xsl:value-of select="@mimetype" /></tt></xsl:if> <xsl:if test="@parent"> - Input template (parent): <tt><xsl:value-of select="@parent" /></tt></xsl:if></li>
					  </xsl:for-each>
                      </ul></li>
                    </xsl:for-each>
				</ol>
				<br /><em>Responses:</em>
				<ul>
					<li>Will respond with <tt>HTTP 200 OK</tt> if successful, and returns the content of the file (along with the correct mime-type for it)</li>
					<li>Will respond with <tt>HTTP 401 Unauthorized</tt> if incorrect or no user credentials were passed. User credentials have to be passed using <xsl:call-template name="authtype" /></li>
					<li>Will respond with <tt>HTTP 404 Not Found</tt> if the file or project does not exist</li>
                </ul><br/>
                Curl example: <tt>curl <xsl:call-template name="curlauth" /> -v <xsl:value-of select="@baseurl"/>/<em>$yourprojectname</em>/output/<em>$outputfilename</em></tt>
			</li>
			<li><strong>Delete the project</strong> (otherwise it will remain on the server and take up space) - Issue a <tt>HTTP DELETE</tt> on <tt><xsl:value-of select="@baseurl"/>/<em>{yourprojectname}</em>/</tt>.
<br /><em>Responses:</em>
<ul>
    			<li>Will respond with <tt>HTTP 200 OK</tt> if successful, and returns CLAM Upload XML with details on the uploaded files (they may have been renamed automatically)</li>
    			<li>Will respond with <tt>HTTP 401 Unauthorized</tt> if incorrect or no user credentials were passed. User credentials have to be passed using <xsl:call-template name="authtype" /></li>
    			<li>Will respond with <tt>HTTP 403 Permission Denied</tt> if the upload is not valid, the file may not be of the correct type, have an invalid name, or there may be problems with specified parameters for the file. Returns CLAM Upload XML with the specific details</li>
    			<li>Will respond with <tt>HTTP 404 Not Found</tt> if the project does not exist</li>
                </ul><br/>
                Curl example: <tt>curl <xsl:call-template name="curlauth" /> -v -X DELETE <xsl:value-of select="@baseurl"/>/<em>$yourprojectname</em></tt>
			</li>
    	 </ol>


         <h4>Project entry shortcut</h4>

         <p>Steps one to three can be combined in a single HTTP GET or POST query
         that is, however, less RESTful and offers less flexibily. It does, however, facilitate use from simpler
         callers. Issue a <tt>HTTP GET</tt> or <tt>HTTP POST</tt> on <tt><xsl:value-of select="@baseurl"/>/</tt>. The following parameter is
         mandatory, you will be directed to the project page after the request.</p>

         <ul>
             <li><tt>project</tt> -- The name of the project, it will be created if it does not exist yet. Set the value to <em>new</em> if you want CLAM to create a random project name for you.</li>
         </ul>

         <p>The shortcut allows for the adding of files, use the following parameters (grouped per profile):</p>

        <ol>
            <xsl:for-each select="//profile">
              <li>Profile #<xsl:value-of select="position()" />
                 <ul>
                    <xsl:for-each select=".//InputTemplate">
                        <li><strong><xsl:value-of select="@label" /></strong><xsl:text> </xsl:text><em>(<xsl:value-of select="@format" />)</em>:
                        <ul>
                            <li><tt><xsl:value-of select="@id" /></tt> -- The contents of a file for this input template (corresponds to <tt>contents</tt> in the non-shortcut method).</li>
                            <li><tt><xsl:value-of select="@id" />_url</tt> -- A URL from which to download the file for this input template (corresponds to <tt>url</tt> in the non-shortcut method).</li>
                            <li><tt><xsl:value-of select="@id" />_filename</tt> -- The desired filename for the added file (corresponds to (<tt>filename</tt> in the non-shortcut method). Will be automatically generated when not provided and if possible.</li>
                            <li>You can use any of the following parameters, but <strong>prepended with </strong> <tt><xsl:value-of select="@id" />_</tt>
                            <ul>
                            <xsl:apply-templates />
                            </ul>
                            </li>
                        </ul></li>
                    </xsl:for-each>
                 </ul>
                </li>
            </xsl:for-each>
        </ol>

         <p>To automatically start the system, pass the parameter <tt>start</tt> with value 1. By default, the system will not be started yet. You can pass any global parameters by ID.</p>

         <p>Note that the shortcut method is limited to add only one file per input template, and it does not support actual file uploads, only downloads and explicit passing of content.</p>


        </xsl:if>
        <xsl:if test="count(/clam/actions/action) > 0">



        <h4>Actions</h4>

        <p>Actions are simple remote procedure calls that can be executed in real-time, they will return HTTP 200 on success with a response fitting the specified MIME type. On fatal server-side errors, they may return <tt>HTTP 500 Server Error</tt> with an error message. Other HTTP errors may be returned, but this is customly defined by underlying function, rather than CLAM itself.</p>

        <ul>
        <xsl:for-each select="/clam/actions/action">
          <li><strong><xsl:value-of select="@name" /></strong> -- <tt><xsl:value-of select="/clam/@baseurl" />/actions/<xsl:value-of select="@id" />/</tt><br />
              <em><xsl:value-of select="@description" /></em><br />
              <xsl:choose>
              <xsl:when test="@method">
                Method: <tt><xsl:value-of select="@method" /></tt><br />
              </xsl:when>
              <xsl:otherwise>
                Methods: <tt>GET</tt>, <tt>POST</tt><br />
              </xsl:otherwise>
              </xsl:choose>
              <xsl:if test="@allowanonymous = 'yes'">
                (<em>Anonymous access allowed</em>)<br />
              </xsl:if>
              Returns: <tt><xsl:value-of select="@mimetype" /></tt><br />Parameters:<br />
              <ol>
              <xsl:apply-templates />
              </ol>
          </li>
        </xsl:for-each>
        </ul>


        </xsl:if>

    	</div>


    	<div class="box">
    	 <h3>CLAM Client API for Python</h3>
    	 <p>
    	 Using the CLAM Client API for Python greatly facilitates the writing of clients for this webservice, as the API will allow for more higher-level programming, taking care of all the necessary basics of RESTful communication. The following is a <em>skeleton</em> Python 3 script you can use as a <em>template</em> for your client to communicate with this webservice.
    	 </p>

<pre class="pythoncode">
<em>#!/usr/bin/env python3</em>
<strong>import</strong> clam.common.client
<strong>import</strong> clam.common.data
<strong>import</strong> clam.common.status
<strong>import</strong> random
<strong>import</strong> sys
<strong>import</strong> os
<strong>import</strong> time

<em>#create client, connect to server.</em>
<em>#the latter two arguments are required for authenticated webservices, they can be omitted otherwise</em>
<em>#if you use SSL (https) and SSL verification fails, you can pass a verify= parameter with the path to your certificate of certificate authority bundle</em>
<em>#if the server only accepts HTTP Basic Authentication, add a basicauth=True parameter</em>
clamclient = clam.common.client.CLAMClient("<xsl:value-of select="@baseurl"/>", username, password)


<xsl:if test="count(/clam/profiles/profile) > 0">

<em>#If your webservice uses custom formats, you want import or redefine them here (each format is a Python class), and register them with the client:</em>
<em>#class SomeCustomFormat(clam.common.data.CLAMMetaData):</em>
<em>#    mimetype = 'text/plain'</em>
<em>#clamclient.register_custom_formats([ SomeCustomFormat ])</em>

<br /><br />

<em>#Set a project name (it is recommended to include a sufficiently random naming component here, to allow for concurrent uses of the same client)</em>
project = "projectname" + str(random.getrandbits(64))

<em>#Now we call the webservice and create the project (in this and subsequent methods of clamclient, exceptions will be raised on errors).</em>
clamclient.create(project)

<em>#Get project status and specification</em>
data = clamclient.get(project)


<em>#Add one or more input files according to a specific input template. The following input templates are defined,</em>
<em>each may allow for extra parameters to be specified, this is done in the form of Python keyword arguments to the <tt>addinputfile()</tt> method, (parameterid=value)</em>
<xsl:for-each select="//InputTemplate">
<em>#inputtemplate="<xsl:value-of select="@id" />" #<xsl:value-of select="@label" /> (<xsl:value-of select="@format" />)</em>
<em>#	The following parameters may be specified for this input template:</em>
<xsl:for-each select="./*">
<em>#		<xsl:value-of select="@id" />=...  #(<xsl:value-of select="name()" />) -   <xsl:value-of select="@name" /> -  <xsl:value-of select="@description" /></em>
<xsl:if test="@required = 'true'">
	<em>#		this parameter is REQUIRED! </em>
</xsl:if>
<xsl:if test="name() = 'ChoiceParameter'">
	<em>#		valid choices for this parameter: </em>
	<xsl:for-each select="choice">
		<em>#			<xsl:value-of select="@id" /> - <xsl:value-of select="." /></em>
	</xsl:for-each>
</xsl:if>
<xsl:if test="@multi = 'true'">
	<em>#		Multiple choices may be combined for this parameter as a comma separated list </em>
</xsl:if>
</xsl:for-each>
</xsl:for-each>
clamclient.addinputfile(project, data.inputtemplate(inputtemplate), localfilename)


<em>#Start project execution with custom parameters. Parameters are specified as Python keyword arguments to the <tt>start()</tt> method <tt>(parameterid=value)</tt></em>
<xsl:for-each select="//parameters/parametergroup/*">
<em>#<xsl:value-of select="@id" />=...  #(<xsl:value-of select="name()" />) -   <xsl:value-of select="@name" /> -  <xsl:value-of select="@description" /></em>
<xsl:if test="@required = 'true'">
	<em>#	this parameter is REQUIRED! </em>
</xsl:if>
<xsl:if test="name() = 'ChoiceParameter'">
	<em>#	valid choices for this parameter: </em>
	<xsl:for-each select="choice">
		<em>#	<xsl:value-of select="@id" /> - <xsl:value-of select="." /></em>
	</xsl:for-each>
</xsl:if>
<xsl:if test="@multi = 'true'">
	<em>#	Multiple choices may be combined for this parameter as a comma separated list </em>
</xsl:if>
</xsl:for-each>
data = clamclient.start(project)


<em>#Always check for parameter errors! Don't just assume everything went well! Use startsafe() instead of start</em>
<em>#to simply raise exceptions on parameter errors.</em>
<strong>if</strong> data.errors:
    <strong>print</strong>("An error occured: " + data.errormsg, file=sys.stderr)
    <strong>for</strong> parametergroup, paramlist in data.parameters:
        <strong>for</strong> parameter in paramlist:
            <strong>if</strong> parameter.error:
                <strong>print</strong>("Error in parameter " + parameter.id + ": " + parameter.error, file=sys.stderr)
    clamclient.delete(project) #delete our project (remember, it was temporary, otherwise clients would leave a mess)
    sys.exit(1)

<em>#If everything went well, the system is now running, we simply wait until it is done and retrieve the status in the meantime</em>
<strong>while</strong> data.status != clam.common.status.DONE:
    time.sleep(5) #wait 5 seconds before polling status
    data = clamclient.get(project) #get status again
    <strong>print</strong>("\tRunning: " + str(data.completion) + '% -- ' + data.statusmessage, file=sys.stderr)

<em>#Iterate over output files</em>
<strong>for</strong> outputfile <strong>in</strong> data.output:
    <strong>try</strong>:
        outputfile.loadmetadata() #metadata contains information on output template
    <strong>except</strong>:
        <strong>continue</strong>

    outputtemplate = outputfile.metadata.provenance.outputtemplate_id
    <em>	#You can check this value against the following predefined output templates, and determine desired behaviour based on the output template:</em>
    <xsl:for-each select="//OutputTemplate">
	<em>	#if outputtemplate == "<xsl:value-of select="@id" />": #<xsl:value-of select="@label" /> (<xsl:value-of select="@format" />)</em>
	</xsl:for-each>

    <em>	#Download the remote file</em>
    localfilename = os.path.basename(str(outputfile))
    outputfile.copy(localfilename)

    <em>	#..or iterate over its (textual) contents one line at a time:</em>
	<strong>	for</strong> line <strong>in</strong> outputfile.readlines():
		<strong>print</strong>(line)

<em>#delete the project (otherwise it would remain on server and clients would leave a mess)</em>
clamclient.delete(project)

</xsl:if>


<xsl:if test="count(/clam/actions/action) > 0">
<em>#A fictitious sample showing how to use the actions:</em>
result = clamclient.action('someaction', someparameter='blah',otherparameter=42, method='GET')
</xsl:if>

</pre>
    	</div>


    <div class="box">
    	<h3>CLAM XML</h3>
    	<p>To inspect the CLAM XML format, simply view the source of this current page, or any CLAM page. A formal schema definition in RelaxNG format will be available <a href="https://github.com/proycon/clam/blob/master/docs/clam.rng">here</a>. This documentation was automatically generated from the service description in CLAM XML format.</p>
</div>

        <xsl:call-template name="footer" />



    </div>
  </body>
  </html>
</xsl:template>

<xsl:template name="curlauth">
    <xsl:choose>
        <xsl:when test="/clam/@authentication = 'basic'">
            --basic -u <em>$username</em> -p
        </xsl:when>
        <xsl:when test="/clam/@authentication = 'digest'">
            --digest -u <em>$username</em> -p
        </xsl:when>
    </xsl:choose>
</xsl:template>

<xsl:template name="authtype">
    <xsl:choose>
        <xsl:when test="/clam/@authentication = 'basic'">
            HTTP Basic Authentication or HTTP Digest Authentication
        </xsl:when>
        <xsl:when test="/clam/@authentication = 'digest'">
            HTTP Digest Authentication
        </xsl:when>
        <xsl:when test="/clam/@authentication = 'preauth'">
            a custom application-specific scheme based on a pre-authenticated header
        </xsl:when>
        <xsl:when test="/clam/@authentication = 'oauth'">
            OAuth2
        </xsl:when>
        <xsl:when test="/clam/@authentication = 'none'">
            HTTP Basic/Digest Authentication usually, but authentication on this webservice is currently disabled
        </xsl:when>
    </xsl:choose>
</xsl:template>


<xsl:template name="head">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title><xsl:value-of select="@name"/> :: <xsl:value-of select="@project"/></title>
    <link rel="stylesheet" href="{/clam/@baseurl}/static/base.css" type="text/css"></link>
    <link rel="stylesheet" href="{/clam/@baseurl}/style.css" type="text/css"></link>
  </head>
</xsl:template>

<xsl:template name="footer">
<div id="footer" class="box">Powered by <strong>CLAM</strong> v<xsl:value-of select="/clam/@version" /> - Computational Linguistics Application Mediator<br />by Maarten van Gompel -
    <a href="https://proycon.github.io/clam">https://proycon.github.io/clam</a>
    <br /><a href="http://ru.nl/clst">Centre for Language and Speech Technology</a>, <a href="http://www.ru.nl">Radboud University Nijmegen</a>

    <span class="extracredits">
        <strong>CLAM</strong> is funded by <a href="http://www.clarin.nl/">CLARIN-NL</a> and its successor <a href="http://www.clariah.nl">CLARIAH</a>.
    </span>
</div>

</xsl:template>




<xsl:template match="StaticParameter|staticparameter">  <!-- lowercase variant is required because of some XSLT issues in Mozilla -->
	<li><tt><xsl:value-of select="@id" /></tt> - <strong><xsl:value-of select="@name" /></strong> (static parameter, fixed immutable value: <tt><xsl:value-of select="@value" /></tt>) - <xsl:value-of select="@description" />
	<xsl:if test="@required = 'yes'">
		<strong>Note: This is a required parameter!</strong>
	</xsl:if>
	</li>
</xsl:template>


<xsl:template match="BooleanParameter|booleanparameter">  <!-- lowercase variant is required because of some XSLT issues in Mozilla -->
	<li><tt><xsl:value-of select="@id" /></tt> - <strong><xsl:value-of select="@name" /></strong> (boolean parameter) -  <xsl:value-of select="@description" />
	<xsl:if test="@required = 'yes'">
		<strong>Note: This is a required parameter!</strong>
	</xsl:if>
	</li>
</xsl:template>


<xsl:template match="StringParameter|stringparameter">  <!-- lowercase variant is required because of some XSLT issues in Mozilla -->
	<li><tt><xsl:value-of select="@id" /></tt> - <strong><xsl:value-of select="@name" /></strong> (string parameter) -  <xsl:value-of select="@description" />
	<xsl:if test="@required = 'yes'">
		<strong>Note: This is a required parameter!</strong>
	</xsl:if>
	</li>
</xsl:template>




<xsl:template match="TextParameter|textparameter">  <!-- lowercase variant is required because of some XSLT issues in Mozilla -->
	<li><tt><xsl:value-of select="@id" /></tt> - <strong><xsl:value-of select="@name" /></strong> (text parameter) -  <xsl:value-of select="@description" />
	<xsl:if test="@required = 'yes'">
		<strong>Note: This is a required parameter!</strong>
	</xsl:if>
	</li>
</xsl:template>


<xsl:template match="IntegerParameter|integerparameter">  <!-- lowercase variant is required because of some XSLT issues in Mozilla -->
	<li><tt><xsl:value-of select="@id" /></tt> - <strong><xsl:value-of select="@name" /></strong> (integer parameter) -  <xsl:value-of select="@description" />
	<xsl:if test="@required = 'yes'">
		<strong>Note: This is a required parameter!</strong>
	</xsl:if>
	</li>
</xsl:template>

<xsl:template match="FloatParameter|floatparameter">  <!-- lowercase variant is required because of some XSLT issues in Mozilla -->
	<li><tt><xsl:value-of select="@id" /></tt> - <strong><xsl:value-of select="@name" /></strong> (float parameter) -  <xsl:value-of select="@description" />
	<xsl:if test="@required = 'yes'">
		<strong>Note: This is a required parameter!</strong>
	</xsl:if>
	</li>
</xsl:template>


<xsl:template match="ChoiceParameter|choiceparameter">  <!-- lowercase variant is required because of some XSLT issues in Mozilla -->
	<li><tt><xsl:value-of select="@id" /></tt> - <strong><xsl:value-of select="@name" /></strong> (multiple-choice parameter) -  <xsl:value-of select="@description" />
	<xsl:if test="@required = 'true'">
		<strong>Note: This is a required parameter!</strong>
	</xsl:if>
	<xsl:if test="@multi = 'true'">
		<strong>Note: Multiple values may be combined for this parameter as a comma separated list</strong>
	</xsl:if>
	<br />Available value choices:
	<ul>
		<xsl:for-each select="choice">
			<li><em><xsl:value-of select="@id" /></em> - <xsl:value-of select="." /></li>
		</xsl:for-each>
	</ul>
	</li>
</xsl:template>

<xsl:template match="converter|viewer|project|meta|inputsource">
</xsl:template>

</xsl:stylesheet>
