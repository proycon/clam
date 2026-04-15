use std::ffi::OsString;

use crate::error::ClamError;

pub trait Envsubst {
    /// Substitute variables from the environment, this should only be called once per structure, just after deserialisation
    fn envsubst(&mut self) -> Result<(), ClamError>;
}

#[derive(Copy, Clone, Default)]
pub enum EnvsubstMode {
    #[default]
    ErrorIfMissing,

    /// Leaves the variable unresolved if it is missing, so the variable remains in the string
    UnresolvedIfMissing,

    EmptyIfMissing,
}

/// Resolve environment variables following `${VARNAME}` syntax.
/// Supports assigning defaults via `${VARNAME:-default}` or `${VARNAME:=default}` (functionally identical)
pub fn envsubst<'a>(s: &mut String, mode: EnvsubstMode) -> Result<(), ClamError> {
    let mut beginvarname = 0;
    let mut begindefault = 0;
    let mut substitute = String::new();
    let mut lastend = 0;
    let mut substituted = false;
    for (bytepos, c) in s.char_indices() {
        if bytepos < beginvarname || bytepos < begindefault {
            //skip a few known chars
            continue;
        }

        if beginvarname == 0 && c == '$' && s[bytepos..].starts_with("${") {
            beginvarname = bytepos + 2;
        }
        if beginvarname > 0
            && c == ':'
            && (s[bytepos..].starts_with(":-") || s[bytepos..].starts_with(":="))
        {
            begindefault = bytepos + 2;
        } else if beginvarname > 0 && c == '}' {
            let varname: &str = if begindefault > 0 {
                &s[beginvarname..begindefault - 2]
            } else {
                &s[beginvarname..bytepos]
            };

            let varname_os: OsString = varname.into();

            //add the intermediate part
            if beginvarname - 2 > lastend {
                substitute += &s[lastend..beginvarname - 2];
            }

            if let Ok(value) = std::env::var(varname_os) {
                substituted = true;
                substitute += value.as_str();
            } else if begindefault > 0 {
                let default = &s[begindefault..bytepos];
                substituted = true;
                substitute += default;
            } else {
                substituted = true;
                match mode {
                    EnvsubstMode::ErrorIfMissing => {
                        return Err(ClamError::MissingEnvVariable(varname.to_owned()));
                    }
                    EnvsubstMode::EmptyIfMissing => {}
                    EnvsubstMode::UnresolvedIfMissing => {
                        substitute += &s[beginvarname - 2..bytepos + 1]
                    }
                }
            }

            //reset
            beginvarname = 0;
            begindefault = 0;
            lastend = bytepos + 1;
        }
    }
    if substituted {
        //add the last remaining part
        substitute += &s[lastend..];
        *s = substitute;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_envsubst_none() -> Result<(), ClamError> {
        let mut s: String = "novars".into();
        envsubst(&mut s, EnvsubstMode::ErrorIfMissing)?;
        assert_eq!(s, "novars");
        Ok(())
    }

    #[test]
    fn test_envsubst_simple() -> Result<(), ClamError> {
        let mut s: String = "${HOME}".into();
        envsubst(&mut s, EnvsubstMode::ErrorIfMissing)?;
        assert_eq!(
            s,
            std::env::var("HOME").expect("HOME variable not available in test environment")
        );
        Ok(())
    }

    #[test]
    fn test_envsubst_default() -> Result<(), ClamError> {
        let mut s: String = "${BLAH:=blah}".into();
        envsubst(&mut s, EnvsubstMode::ErrorIfMissing)?;
        assert_eq!(s, "blah");
        Ok(())
    }

    #[test]
    fn test_envsubst_default2() -> Result<(), ClamError> {
        let mut s: String = "${BLAH:-blah}".into();
        envsubst(&mut s, EnvsubstMode::ErrorIfMissing)?;
        assert_eq!(s, "blah");
        Ok(())
    }

    #[test]
    fn test_envsubst_incontext() -> Result<(), ClamError> {
        let mut s: String = "foo${HOME}bar".into();
        let reference: String = format!(
            "foo{}bar",
            std::env::var("HOME").expect("HOME variable not available in test environment")
        );
        envsubst(&mut s, EnvsubstMode::ErrorIfMissing)?;
        assert_eq!(s, reference);
        Ok(())
    }

    #[test]
    fn test_envsubst_incontext_default() -> Result<(), ClamError> {
        let mut s: String = "foo${BLAH:=blah}bar".into();
        envsubst(&mut s, EnvsubstMode::ErrorIfMissing)?;
        assert_eq!(s, "fooblahbar");
        Ok(())
    }

    #[test]
    fn test_envsubst_incontext_default2() -> Result<(), ClamError> {
        let mut s: String = "foo${BLAH:-blah}bar".into();
        envsubst(&mut s, EnvsubstMode::ErrorIfMissing)?;
        assert_eq!(s, "fooblahbar");
        Ok(())
    }

    #[test]
    fn test_envsubst_errorifmissing() -> Result<(), ClamError> {
        let mut s: String = "${BLAH}".into();
        let e = envsubst(&mut s, EnvsubstMode::ErrorIfMissing);
        assert!(e.is_err());
        Ok(())
    }

    #[test]
    fn test_envsubst_emptyifmissing() -> Result<(), ClamError> {
        let mut s: String = "${BLAH}".into();
        let e = envsubst(&mut s, EnvsubstMode::EmptyIfMissing);
        assert_eq!(s, "");
        Ok(())
    }
}
