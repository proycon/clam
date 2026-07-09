use crate::config::{EndPoint, EndPointMode, ParameterType, ServiceConfig};
use crate::error::ApiError;
use crate::project::ProjectStatus;
use utoipa::openapi::{
    Components, Content, ContentBuilder, HttpMethod, Info, ObjectBuilder, OpenApi, OpenApiBuilder,
    PathItem, Paths, Required, Response, ResponseBuilder, Responses, ResponsesBuilder, Schema,
    Server, path::Operation, path::Parameter, path::ParameterBuilder, path::ParameterIn,
    schema::Type,
};

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
            operation.summary = Some("OpenAPI specification".to_string());
            operation.description = Some(
                "Presents the full [OpenAPI specification](https://spec.openapis.org) for this webservice if JSON content is requested, presents the interactive Swagger Web-UI for human end-users."
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
            &EndPointMode::Porch => {
                let mut operation = Operation::new();
                operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Public landing page".to_string()),
                );
                operation.description =
                    Some(self.description().clone().unwrap_or_else(|| "This is the public landing page that is accessible without authentication and gives information and metadata about the webservice. It allows users to continue to the authenticated sections (if available). If JSON content is requested, it returns the full OpenAPI specification of the service.".to_string()));
                operation.responses = ResponsesBuilder::new().response("200",
                    ResponseBuilder::new().content("text/html", ContentBuilder::new().into()).description("Information and metadata about the webservice, includes a button to proceed to the next (possibly authenticated) stage")
                ).response("200",
                    ResponseBuilder::new().content("application/json", ContentBuilder::new().into()).description("OpenAPI specification")
                ).into();
                paths.add_path_operation(self.path(), vec![HttpMethod::Get], operation);
            }
            &EndPointMode::Action => {
                let mut operation = Operation::new();
                operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Action endpoint".to_string()),
                );
                operation.description =
                    Some(self.description().clone().unwrap_or_else(|| "An action endpoint takes zero or more parameters, runs a process in the background, and returns within the same round-trip with the result".to_string()));
                self.register_parameters_in(&mut operation);
                let filetype = config.get_filetype(self.filetype().as_deref().unwrap_or("none"));

                operation.responses = ResponsesBuilder::new()
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
                paths.add_path_operation(
                    self.path(),
                    vec![HttpMethod::Get, HttpMethod::Post],
                    operation,
                );
            }
            &EndPointMode::Project => {
                //GET
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
                            .content("text/html", ContentBuilder::new().into())
                            .description("Project page for human end-users"),
                    )
                    .response(
                        "200",
                        ResponseBuilder::new()
                            .content(
                                "application/json",
                                ContentBuilder::new()
                                    .schema(Some(projectresponse_schema.clone()))
                                    .into(),
                            )
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

                //PUT (create)
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

                //DELETE
                let mut delete_operation = Operation::new();
                delete_operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Delete a project".to_string()),
                );
                delete_operation.description =
                    Some(self.description().clone().unwrap_or_else(|| {
                        "Deletes this project, including all input and output files".to_string()
                    }));
                delete_operation.responses = ResponsesBuilder::new()
                    .response("204", ResponseBuilder::new())
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

                //POST
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
            }
            &EndPointMode::Index => {
                let mut operation = Operation::new();
                operation.summary = Some(
                    self.summary()
                        .clone()
                        .unwrap_or_else(|| "Index page, provides a list of endpoints and project to human end-users. Authentication may be required.".to_string()),
                );
                operation.description = self.description().clone();
                operation.responses = ResponsesBuilder::new()
                    .response(
                        "200",
                        ResponseBuilder::new()
                            .content("text/html", ContentBuilder::new().into())
                            .description("List of endpoints (actions & projects). Provides an interface to start new projects or delete existing ones (if applicable)."),
                    )
                    .into();
                paths.add_path_operation(self.path(), vec![HttpMethod::Get], operation);
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
