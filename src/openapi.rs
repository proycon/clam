use crate::config::{EndPoint, EndPointMode, ParameterType, ServiceConfig};
use crate::error::ApiError;
use crate::project::ProjectStatus;
use utoipa::openapi::{
    Components, ContentBuilder, HttpMethod, Info, ObjectBuilder, OpenApi, OpenApiBuilder, Paths,
    Required, ResponseBuilder, ResponsesBuilder, Schema, Server, content::Content, path::Operation,
    path::Parameter, path::ParameterBuilder, path::ParameterIn, request_body::RequestBodyBuilder,
    schema::Type,
};

//TODO: add projects/ endpoint

impl From<&ServiceConfig> for OpenApi {
    fn from(config: &ServiceConfig) -> Self {
        let error_schema = ApiError::schema();
        let projectstatus_schema = ProjectStatus::schema();
        let mut info = Info::new(config.name(), config.version());
        info.description = config.description().clone();
        info.license = config.license().clone();
        info.contact = config.contact().clone();
        info.terms_of_service = config.termsofservice().clone();

        let mut paths = Paths::new();
        {
            let mut operation = Operation::new();
            operation.summary = Some("OpenAPI specification".to_string());
            operation.description = Some(
                "Full [OpenAPI specification](https://spec.openapis.org) for this webservice"
                    .to_string(),
            );
            operation.responses = ResponsesBuilder::new()
                .response(
                    "200",
                    ResponseBuilder::new()
                        .content("application/json", ContentBuilder::new().into())
                        .description("OpenAPI specification"),
                )
                .into();
            paths.add_path_operation("/openapi.json", vec![HttpMethod::Get], operation);
        }
        {
            let mut operation = Operation::new();
            operation.summary = Some("Swagger interface".to_string());
            operation.description = Some(
                "Presents the interactive Swagger Web-UI for human end-users, allowing them to explore the full webservice API"
                    .to_string(),
            );
            operation.responses = ResponsesBuilder::new()
                .response(
                    "200",
                    ResponseBuilder::new()
                        .content("text/html", ContentBuilder::new().into())
                        .description("Swagger UI"),
                )
                .into();
            paths.add_path_operation("/info", vec![HttpMethod::Get], operation);
        }

        for endpoint in config.endpoints().iter() {
            endpoint.register_paths_in(&mut paths, config, &error_schema, &projectstatus_schema);
        }
        let server = Server::new(config.url().clone().unwrap_or_else(|| "/".to_string()));
        let openapi = OpenApiBuilder::new()
            .servers(Some(vec![server]))
            .info(info)
            .paths(paths)
            .components(Some(Components::new()))
            .build();
        openapi
    }
}

impl EndPoint {
    pub fn register_paths_in(
        &self,
        paths: &mut Paths,
        config: &ServiceConfig,
        error_schema: &Schema,
        projectresponse_schema: &Schema,
    ) {
        match self.mode() {
            &EndPointMode::LandingPage => {
                let mut operation = Operation::new();
                operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Public landing page".to_string()),
                );
                operation.description =
                    Some(self.description().clone().unwrap_or_else(|| "This is the public landing page that is accessible without authentication and gives information and metadata about the webservice. It allows users to continue to the authenticated sections (if available). If JSON content is requested, it returns the full OpenAPI specification of the service.".to_string()));
                operation.responses = ResponsesBuilder::new().response("200",
                    ResponseBuilder::new().content("text/html", ContentBuilder::new().into()).content("application/json", ContentBuilder::new().into()).description("Information and metadata about the webservice, the HTML versio includes a button to proceed to the next (possibly authenticated) stage. The JSON version presents the OpenAPI specification")
                ).
                into();
                paths.add_path_operation(self.path(), vec![HttpMethod::Get], operation);
            }
            &EndPointMode::Action => {
                let filetype = config.filetype(self.filetype().as_deref().unwrap_or("none"));

                let mut get_operation = Operation::new();
                get_operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Submission form for an action".to_string()),
                );
                get_operation.description = Some(format!(
                    "{}{}{}",
                    self.description().as_deref().unwrap_or(""),
                    if self.description().is_some() {
                        ". "
                    } else {
                        ""
                    },
                    format!(
                        "This endpoint is for human end-users and presents the submission form for the action unless the output content-type {} is requested in the accepted header.",
                        if let Some(filetype) = filetype {
                            filetype.contenttype()
                        } else {
                            ""
                        }
                    )
                ));
                self.register_parameters_in(&mut get_operation);

                get_operation.responses = ResponsesBuilder::new()
                    .response(
                        "200",
                        if let Some(filetype) = filetype {
                            let mut rb = ResponseBuilder::new()
                                .content("text/html", ContentBuilder::new().into())
                                .description(
                                    "The submission form for the action"
                                );
                            if filetype.contenttype() != "text/html" {
                                rb = rb
                                    .content(filetype.contenttype(), ContentBuilder::new().into())
                                    .description(
                                        format!("Output of the action in {} format", filetype.name())
                                    );
                            }
                            rb.build()
                        } else {
                            // generic, unknown filetype
                            ResponseBuilder::new()
                                .content("text/html", ContentBuilder::new().into())
                                .description(
                                    "Submission form for the action"
                                ).build()
                        }
                    )
                    .response(
                        "400",
                        apierror_response("Returned when one or more parameters to the action are invalid (ParameterError)", error_schema),
                    )
                    .response(
                        "503",
                        apierror_response("Returned when the action is unavailable due to load or other reasons (ServiceUnavailable)", error_schema),
                    )
                    .into();
                paths.add_path_operation(self.path(), vec![HttpMethod::Get], get_operation);

                let mut post_operation = Operation::new();
                post_operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Action endpoint".to_string()),
                );
                post_operation.description =
                    Some(self.description().clone().unwrap_or_else(|| "An action endpoint takes zero or more parameters, runs a process in the background, and returns within the same round-trip with the result".to_string()));
                self.register_parameters_in(&mut post_operation);

                post_operation.responses = ResponsesBuilder::new()
                    .response(
                        "200",
                        if let Some(filetype) = filetype {
                            ResponseBuilder::new()
                                .content(filetype.contenttype(), ContentBuilder::new().into())
                                .description(
                                    format!("Output of the action upon succesful completion, in {} format", filetype.name())
                                )
                        } else {
                            // generic, unknown filetype
                            ResponseBuilder::new()
                                .content("text/plain", ContentBuilder::new().into())
                                .description(
                                    "Output of the action upon succesful completion in plain text format"
                                )
                        }
                    )
                    .response(
                        "400",
                        apierror_response("Returned when one or more parameters to the action are invalid (ParameterError)", error_schema),
                    )
                    .response(
                        "503",
                        apierror_response("Returned when the action is unavailable due to load or other reasons (ServiceUnavailable)", error_schema),
                    )
                    .into();
                paths.add_path_operation(self.path(), vec![HttpMethod::Post], post_operation);
            }
            &EndPointMode::Project => {
                //GET projects -- project index
                let mut get_index_operation = Operation::new();
                get_index_operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Project index".to_string()),
                );
                get_index_operation.description =
                    Some(self.description().clone().unwrap_or_else(|| {
                        "This endpoint provides a list of all projects (pertaining to this this project path)".to_string()
                    }));
                get_index_operation.responses = ResponsesBuilder::new()
                    .response(
                        "200",
                        ResponseBuilder::new()
                            .content(
                                "application/json",
                                ContentBuilder::new()
                                    .into(),
                            )
                            .content("text/html", ContentBuilder::new().into())
                            .description("Project listing, returns all project names. The html interface also presents a form to create a new project."),
                    )
                    .response(
                        "404",
                        apierror_response("Returned when the underlying endpoint does not exist", error_schema),
                    )
                    .into();
                paths.add_path_operation(
                    format!("{}projects", self.path()),
                    vec![HttpMethod::Get],
                    get_index_operation,
                );

                let form_schema = ObjectBuilder::new()
                    .property("project", ObjectBuilder::new().schema_type(Type::String))
                    .required("project")
                    .build();

                //POST projects -- post to the index project creation (alternative)
                let mut post_index_operation = Operation::new();
                post_index_operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Project creation (alternative endpoint)".to_string()),
                );
                post_index_operation.description = Some(
                    self.description()
                        .clone()
                        .unwrap_or_else(|| "Alternative endpoint for project creation (application/x-www-form-urlencoded); usually invoked from the web interface".to_string()),
                );
                post_index_operation.request_body = Some(
                    RequestBodyBuilder::new()
                        .content(
                            "application/x-www-form-urlencoded",
                            Content::new(Some(form_schema)),
                        )
                        .build(),
                );
                post_index_operation.responses = ResponsesBuilder::new()
                    .response(
                        "303",
                        ResponseBuilder::new().description(
                            "Redirects to the new project's status page upon successful creation",
                        ),
                    )
                    .response(
                        "404",
                        apierror_response(
                            "Returned when the project can not be created",
                            error_schema,
                        ),
                    )
                    .into();
                paths.add_path_operation(
                    format!("{}projects", self.path()),
                    vec![HttpMethod::Post],
                    post_index_operation,
                );

                //GET $project
                let mut get_operation = Operation::new();
                get_operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Project state and information".to_string()),
                );
                get_operation.description =
                    Some(self.description().clone().unwrap_or_else(|| "Retrieves the project state and depending on it presents a 1) a listing of uploaded input files and parameters in a staging area, 2) an in progress notification, or 3) a list of output files when the project is done".to_string()));
                get_operation.responses = ResponsesBuilder::new()
                    .response(
                        "200",
                        ResponseBuilder::new()
                            .content(
                                "application/json",
                                ContentBuilder::new()
                                    .schema(Some(projectresponse_schema.clone()))
                                    .into(),
                            )
                            .content("text/html", ContentBuilder::new().into())
                            .description("Project information"),
                    )
                    .response(
                        "404",
                        apierror_response("Returned when the project does not exist", error_schema),
                    )
                    .into();
                get_operation.parameters = Some(vec![project_path_parameter()]);
                paths.add_path_operation(
                    format!("{}{{project}}", self.path()),
                    vec![HttpMethod::Get],
                    get_operation,
                );

                //PUT $project (create)
                let mut put_operation = Operation::new();
                put_operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Create a new project".to_string()),
                );
                put_operation.description = Some(self.description().clone().unwrap_or_else(|| {
                    "Creates a new (empty) project, you can upload files in subsequent requests"
                        .to_string()
                }));
                put_operation.responses = ResponsesBuilder::new()
                    .response("201", ResponseBuilder::new())
                    .response(
                        "404",
                        apierror_response(
                            "Returned when the project can not be created",
                            error_schema,
                        ),
                    )
                    .build();
                paths.add_path_operation(
                    format!("{}{{project}}", self.path()),
                    vec![HttpMethod::Put],
                    put_operation,
                );

                //DELETE $project
                let mut delete_operation = Operation::new();
                delete_operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Delete a project".to_string()),
                );
                delete_operation.description =
                    Some(self.description().clone().unwrap_or_else(|| {
                        "Deletes this project, including all input and output files. Automatically aborts any associated running processes.".to_string()
                    }));
                delete_operation.responses = ResponsesBuilder::new()
                    .response("204", ResponseBuilder::new().description("Returned upon succesful deletion, it may take a while to return if jobs are runrning, because any associated processes are asked to terminate first"))
                    .response(
                        "404",
                        apierror_response("Returned when the project does not exist", error_schema),
                    )
                    .build();
                paths.add_path_operation(
                    format!("{}{{project}}", self.path()),
                    vec![HttpMethod::Delete],
                    delete_operation,
                );

                //POST $project
                let mut post_operation = Operation::new();
                post_operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Start a project run".to_string()),
                );
                post_operation.description =
                    Some(self.description().clone().unwrap_or_else(|| "This starts a project, with the specified parameters and runs the background job(s).".to_string()));
                post_operation.parameters = Some(vec![project_path_parameter()]);
                self.register_parameters_in(&mut post_operation);
                post_operation.responses = ResponsesBuilder::new()
                    .response(
                        "200",
                        ResponseBuilder::new()
                            .description(
                                "Indicates that the job for the project has been succesfully accepted. Query progress using GET requests.",
                            ),
                    )
                    .response(
                        "404",
                        apierror_response("Returned when the project does not exist (NotFound error)", error_schema),
                    )
                    .response(
                        "400",
                        apierror_response("Returned when one or more parameters are invalid (ParameterError)", error_schema),
                    )
                    .response(
                        "503",
                        apierror_response("Returned when the service is unavailable due to load or other reasons (ServiceUnavailable)", error_schema),
                    )
                    .into();
                paths.add_path_operation(
                    format!("{}{{project}}", self.path()),
                    vec![HttpMethod::Post],
                    post_operation,
                );

                let mut file_parameters = Vec::new();

                // Create endpoints for input file upload/download/deletion
                for parameter in self.parameters().iter() {
                    if let ParameterType::File {
                        filename: _,
                        filetype,
                        conflictresolution: _,
                    } = parameter.r#type()
                    {
                        let filetype = config
                            .filetype(filetype)
                            .expect("A parameter references an undefined filetype");
                        file_parameters.push((parameter.id(), filetype));

                        //GET inputfile
                        let mut get_inputfile_operation = Operation::new();
                        get_inputfile_operation.summary = Some(format!(
                            "Retrieves the specified inputfile for parameter: {}",
                            parameter.name(),
                        ));
                        get_inputfile_operation.responses = ResponsesBuilder::new()
                            .response(
                                "200",
                                ResponseBuilder::new()
                                    .content(filetype.contenttype(), ContentBuilder::new().into())
                                    .description(filetype.name()),
                            )
                            .response(
                                "404",
                                apierror_response(
                                    "Returned when the specified input file does not exist",
                                    error_schema,
                                ),
                            )
                            .into();
                        get_inputfile_operation.parameters = Some(vec![project_path_parameter()]);
                        get_inputfile_operation
                            .parameters
                            .as_mut()
                            .map(|parameters| parameters.push(filename_path_parameter()));
                        paths.add_path_operation(
                            format!("{}{{project}}/{}/{{filename}}", self.path(), parameter.id()),
                            vec![HttpMethod::Get],
                            get_inputfile_operation,
                        );

                        //DELETE inputfile
                        let mut delete_inputfile_operation = Operation::new();
                        delete_inputfile_operation.summary = Some(format!(
                            "Removes the specified inputfile for parameter: {}",
                            parameter.name(),
                        ));
                        delete_inputfile_operation.responses = ResponsesBuilder::new()
                            .response(
                                "204",
                                ResponseBuilder::new()
                                    .description("Returned when the file was succesfully deleted"),
                            )
                            .response(
                                "404",
                                apierror_response(
                                    "Returned when the specified input file does not exist",
                                    error_schema,
                                ),
                            )
                            .into();
                        delete_inputfile_operation.parameters =
                            Some(vec![project_path_parameter()]);
                        delete_inputfile_operation
                            .parameters
                            .as_mut()
                            .map(|parameters| parameters.push(filename_path_parameter()));
                        paths.add_path_operation(
                            format!("{}{{project}}/{}/{{filename}}", self.path(), parameter.id()),
                            vec![HttpMethod::Delete],
                            delete_inputfile_operation,
                        );

                        //Upload inputfile (PUT), file contents is directly in request body and filename encoded in URL
                        let mut upload_inputfile_operation = Operation::new();
                        upload_inputfile_operation.summary = Some(format!(
                            "Upload the specified inputfile for parameter: {}{}",
                            parameter.name(),
                            if parameter.multiple() {
                                ", this may be called multiple times to upload multiple files"
                            } else {
                                ", only one file is accepted, subsequent calls will overwrite/remove earlier uploads!"
                            }
                        ));
                        upload_inputfile_operation.responses = ResponsesBuilder::new()
                            .response(
                                "201",
                                ResponseBuilder::new()
                                    .description("Returned when the file is succesfully uploaded"),
                            )
                            .response(
                                "404",
                                apierror_response(
                                    "Returned when the specified input file does not exist",
                                    error_schema,
                                ),
                            )
                            .into();
                        upload_inputfile_operation.request_body = Some(
                            RequestBodyBuilder::new()
                                .required(Some(Required::True))
                                .description(Some("File contents to upload"))
                                .content(filetype.contenttype(), ContentBuilder::new().build())
                                .build(),
                        );
                        upload_inputfile_operation.parameters =
                            Some(vec![project_path_parameter()]);
                        upload_inputfile_operation
                            .parameters
                            .as_mut()
                            .map(|parameters| parameters.push(filename_path_parameter()));
                        paths.add_path_operation(
                            format!("{}{{project}}/{}/{{filename}}", self.path(), parameter.id()),
                            vec![HttpMethod::Put],
                            upload_inputfile_operation,
                        );
                    }
                }
                if !file_parameters.is_empty() {
                    //Upload inputfile (POST), secondary upload point, file name and contents are form-encoded in request body
                    let mut upload_inputfile_operation = Operation::new();
                    upload_inputfile_operation.summary = Some(format!("Generic upload endpoint"));
                    upload_inputfile_operation.description = Some(format!(
                        "This upload endpoint accepts multipart/form-data, the field names must correspond with the parameter IDs you want to upload for",
                    ));
                    upload_inputfile_operation.responses = ResponsesBuilder::new()
                        .response(
                            "201",
                            ResponseBuilder::new()
                                .description("Returned when the file is succesfully uploaded"),
                        )
                        .response(
                            "404",
                            apierror_response(
                                "Returned when the specified input file does not exist",
                                error_schema,
                            ),
                        )
                        .into();
                    let mut multipart_schema_builder = ObjectBuilder::new();
                    for (parameter, filetype) in file_parameters.iter() {
                        multipart_schema_builder = multipart_schema_builder.property(
                            parameter.as_str(),
                            ObjectBuilder::new().schema_type(Type::String).format(Some(
                                utoipa::openapi::SchemaFormat::Custom(
                                    filetype.contenttype().clone(),
                                ),
                            )),
                        )
                    }
                    upload_inputfile_operation.request_body = Some(
                        RequestBodyBuilder::new()
                            .required(Some(Required::True))
                            .description(Some("File contents to upload"))
                            .content(
                                "multipart/form-data",
                                ContentBuilder::new()
                                    .schema(Some(Schema::Object(multipart_schema_builder.build())))
                                    .build(),
                            )
                            .build(),
                    );
                    upload_inputfile_operation.parameters = Some(vec![project_path_parameter()]);
                    paths.add_path_operation(
                        format!("{}{{project}}/upload", self.path()),
                        vec![HttpMethod::Post],
                        upload_inputfile_operation,
                    );
                }
            }
        }
    }
}

impl EndPoint {
    fn register_parameters_in(&self, operation: &mut Operation) {
        if operation.parameters.is_none() {
            operation.parameters = Some(Vec::new());
        }
        operation.parameters.as_mut().map(|parameters| {
            for parameter in self.parameters() {
                let builder = ParameterBuilder::new()
                    .parameter_in(ParameterIn::Query)
                    .name(parameter.name())
                    .required(if parameter.required() {
                        Required::True
                    } else {
                        Required::False
                    })
                    .schema(Some(parameter.r#type().schema()))
                    .description(parameter.description().clone());
                parameters.push(builder.build());
            }
        });
    }
}

fn project_path_parameter() -> Parameter {
    ParameterBuilder::new()
        .name("project")
        .description(Some("Project identifier"))
        .parameter_in(ParameterIn::Path)
        .build()
}

fn filename_path_parameter() -> Parameter {
    ParameterBuilder::new()
        .name("filename")
        .description(Some("Filename"))
        .parameter_in(ParameterIn::Path)
        .build()
}

fn apierror_response(message: &str, error_schema: &Schema) -> ResponseBuilder {
    ResponseBuilder::new()
        .content(
            "application/json",
            ContentBuilder::new()
                .schema(Some(error_schema.clone()))
                .into(),
        )
        .description(message)
}

impl ApiError {
    pub fn schema() -> Schema {
        Schema::Object(
            ObjectBuilder::new()
                .property(
                    "type",
                    ObjectBuilder::new()
                        .schema_type(Type::String)
                        .description(Some("The type of error (NotFound, NotAcceptable, ParameterError, InternalError, ServiceUnavailable or InvalidName)")),
                )
                .property(
                    "message",
                    ObjectBuilder::new()
                        .schema_type(Type::String)
                        .description(Some(
                            "A more verbose message explaining the nature of the error",
                        )),
                )
                .required("type")
                .description(Some("Structure encapsulating an error type and error message"))
                .build(),
        )
    }
}

impl ProjectStatus {
    pub fn schema() -> Schema {
        Schema::Object(
            ObjectBuilder::new()
                .property(
                    "stage",
                    ObjectBuilder::new()
                        .schema_type(Type::String)
                        .description(Some("Stage of the project: Staging, Running, or Done")),
                )
                .property(
                    "data",
                    Schema::Object(
                        ObjectBuilder::new()
                            .property(
                                "success",
                                ObjectBuilder::new()
                                    .schema_type(Type::Boolean)
                                    .description(Some("Whether the operation succeeded (used in Done stage)")),
                            )
                            .property(
                                "message",
                                ObjectBuilder::new()
                                    .schema_type(Type::String)
                                    .description(Some("Human-readable status or error message (used in Running or Done stages)")),
                            )
                            .property("input_files", ObjectBuilder::new().schema_type(Type::Array)
                                    .description(Some("List of input files provided (Staging stage)")),
                            )
                            .property(
                                "output_files",
                                ObjectBuilder::new().schema_type(Type::Array)
                                    .description(Some("List of output files produced (Done stage)")),
                            )
                            .property("progress", ObjectBuilder::new().schema_type(Type::Integer)
                                .description(Some("Progress percentage (0-100).")),
                            )
                            .build(),
                    ),
                )
                .required("type")
                .description(Some("Structure encapsulating the stage and data of a project"))
                .build(),
        )
    }
}

impl ParameterType {
    pub fn schema(&self) -> Schema {
        match self {
            ParameterType::Int { min, max, default } => Schema::Object(
                ObjectBuilder::new()
                    .schema_type(Type::Integer)
                    .default(default.map(|x| x.into()))
                    .minimum(min.clone())
                    .maximum(max.clone())
                    .description(Some("Integer value"))
                    .build(),
            ),
            ParameterType::Float { min, max, default } => Schema::Object(
                ObjectBuilder::new()
                    .schema_type(Type::Number)
                    .default(default.map(|x| x.into()))
                    .minimum(min.clone())
                    .maximum(max.clone())
                    .description(Some("Integer value"))
                    .build(),
            ),
            ParameterType::Bool { invert, default } => Schema::Object(
                ObjectBuilder::new()
                    .schema_type(Type::Boolean)
                    .default(default.map(|x| x.into()))
                    .description(if invert == &Some(true) {
                        Some("Boolean value (inverted)")
                    } else {
                        Some("Boolean value")
                    })
                    .build(),
            ),
            ParameterType::String {
                maxlength,
                validation_pattern: _,
                default,
            } => Schema::Object(
                ObjectBuilder::new()
                    .schema_type(Type::String)
                    .default(default.clone().map(|x| x.into()))
                    .description(Some("String value"))
                    .max_length(maxlength.clone())
                    .build(),
            ),
            ParameterType::Selection {
                choices,
                multiple,
                default,
            } => Schema::Object(
                ObjectBuilder::new()
                    .schema_type(Type::String)
                    .default(default.clone().map(|x| x.into()))
                    .description(Some(format!(
                        "String value from the following predefined list: {} {}",
                        choices.join(", "),
                        if *multiple {
                            "(multiple comma-separated values are allowed)"
                        } else {
                            ""
                        }
                    )))
                    .build(),
            ),
            ParameterType::File { .. } => Schema::Object(
                //this one isn't really used here, as files are handled separately and not as query parameters in the API
                ObjectBuilder::new()
                    .schema_type(Type::String)
                    .description(Some("File contents"))
                    .build(),
            ),
        }
    }
}
