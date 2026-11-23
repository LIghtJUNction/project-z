// Real retained adapters and distinct parser/Windows contracts.
// Excerpts are lexical reference fixtures, not a compiled crate.

// zcalld@6a9e889df48e0b6558a0cfc44d6f3e4ccb464dbf:crates/zcalld-compat-client/src/lib.rs:290
fn quote(s: &str) -> String {
    use zconv::json::{ControlEscapes, Writer};
    let mut sizing = Writer::new(&mut []);
    sizing.string_with_control_escapes(s.as_bytes(), ControlEscapes::Unicode);
    let needed = match sizing.finish() {
        Err(zconv::Error::OutputTooSmall { needed }) => needed,
        result => panic!("valid JSON string sizing failed: {result:?}"),
    };
    let mut output = vec![0; needed];
    let mut writer = Writer::new(&mut output);
    writer.string_with_control_escapes(s.as_bytes(), ControlEscapes::Unicode);
    writer.finish().expect("sized JSON string output");
    String::from_utf8(output).expect("validated UTF-8 JSON string")
}

// zcall-gui@795a85044504e844d04575c44dd8b10da7384aa8:src/json.rs:65
fn quote(value: &str) -> String {
    use zconv::json::{ControlEscapes, Writer};
    let mut sizing = Writer::new(&mut []);
    sizing.string_with_control_escapes(value.as_bytes(), ControlEscapes::Unicode);
    let needed = match sizing.finish() {
        Err(zconv::Error::OutputTooSmall { needed }) => needed,
        result => panic!("valid JSON string sizing failed: {result:?}"),
    };
    let mut output = vec![0; needed];
    let mut writer = Writer::new(&mut output);
    writer.string_with_control_escapes(value.as_bytes(), ControlEscapes::Unicode);
    writer.finish().expect("sized JSON string output");
    String::from_utf8(output).expect("validated UTF-8 JSON string")
}

// ztty@a9d5dede2b2b6b726ca0fd87786ed0f81e6125b8:src/json.rs:398
fn quote_into(value: &str, output: &mut Vec<u8>) {
    use zconv::json::{ControlEscapes, Writer};
    let mut sizing = Writer::new(&mut []);
    sizing.string_with_control_escapes(value.as_bytes(), ControlEscapes::Unicode);
    let needed = match sizing.finish() {
        Err(zconv::Error::OutputTooSmall { needed }) => needed,
        result => panic!("valid JSON string sizing failed: {result:?}"),
    };
    let start = output.len();
    output.resize(
        start
            .checked_add(needed)
            .expect("JSON output length overflow"),
        0,
    );
    let mut writer = Writer::new(&mut output[start..]);
    writer.string_with_control_escapes(value.as_bytes(), ControlEscapes::Unicode);
    writer.finish().expect("sized JSON string output");
}

// zmem@4f3ffc9465f25ee35fac2002cb127a305b20574d:src/json.rs:3
fn quote(s: &str) -> String {
    use zconv::json::{ControlEscapes, Writer};
    let mut sizing = Writer::new(&mut []);
    sizing.string_with_control_escapes(s.as_bytes(), ControlEscapes::Unicode);
    let needed = match sizing.finish() {
        Err(zconv::Error::OutputTooSmall { needed }) => needed,
        result => panic!("valid JSON string sizing failed: {result:?}"),
    };
    let mut output = vec![0; needed];
    let mut writer = Writer::new(&mut output);
    writer.string_with_control_escapes(s.as_bytes(), ControlEscapes::Unicode);
    writer.finish().expect("sized JSON string output");
    String::from_utf8(output).expect("validated UTF-8 JSON string")
}

// zuse@617e9160a119a0b3ea13e8f51940119dd90b9f3b:src/json.rs:6
fn quote(text: &str) -> String {
    use zconv::json::{ControlEscapes, Writer};
    let mut sizing = Writer::new(&mut []);
    sizing.string_with_control_escapes(text.as_bytes(), ControlEscapes::Unicode);
    let needed = match sizing.finish() {
        Err(zconv::Error::OutputTooSmall { needed }) => needed,
        result => panic!("valid JSON string sizing failed: {result:?}"),
    };
    let mut output = vec![0; needed];
    let mut writer = Writer::new(&mut output);
    writer.string_with_control_escapes(text.as_bytes(), ControlEscapes::Unicode);
    writer.finish().expect("sized JSON string output");
    String::from_utf8(output).expect("validated UTF-8 JSON string")
}

// zuse@617e9160a119a0b3ea13e8f51940119dd90b9f3b:src/platform/mod.rs:66
fn quote(s: &str) -> String {
    crate::json::quote(s)
}

// ztty@a9d5dede2b2b6b726ca0fd87786ed0f81e6125b8:src/json.rs:418
fn encode(value: &Value, output: &mut Vec<u8>) {
    match value {
        Value::Null => output.extend_from_slice(b"null"),
        Value::Bool(true) => output.extend_from_slice(b"true"),
        Value::Bool(false) => output.extend_from_slice(b"false"),
        Value::Number(value) => output.extend_from_slice(value.as_bytes()),
        Value::String(value) => quote_into(value, output),
        Value::Array(items) => {
            output.push(b'[');
            for (index, item) in items.iter().enumerate() {
                if index != 0 {
                    output.push(b',');
                }
                encode(item, output);
            }
            output.push(b']');
        }
        Value::Object(fields) => {
            output.push(b'{');
            for (index, (key, value)) in fields.iter().enumerate() {
                if index != 0 {
                    output.push(b',');
                }
                quote_into(key, output);
                output.push(b':');
                encode(value, output);
            }
            output.push(b'}');
        }
    }
}

// zcalld@6a9e889df48e0b6558a0cfc44d6f3e4ccb464dbf:src/privacy_windows.rs:17
fn protect(file: &std::fs::File) -> Result<(), String> {
    zsys::windows::privacy::protect(
        file,
        zsys::windows::privacy::DirectoryInheritance::FilesAndDirectories,
    )
    .map_err(|error| error.to_string())
}

// zcalld@6a9e889df48e0b6558a0cfc44d6f3e4ccb464dbf:src/privacy_windows.rs:27
fn check_private(file: &std::fs::File) -> Result<(), String> {
    zsys::windows::privacy::check_private(file).map_err(|error| error.to_string())
}

// zcalld@6a9e889df48e0b6558a0cfc44d6f3e4ccb464dbf:src/privacy_windows.rs:33
fn protect_created(file: &std::fs::File) -> Result<(), String> {
    zsys::windows::privacy::protect_created(
        file,
        zsys::windows::privacy::DirectoryInheritance::FilesAndDirectories,
    )
    .map_err(|error| error.to_string())
}

// zcall-gui@795a85044504e844d04575c44dd8b10da7384aa8:src/core_install_windows.rs:3
fn check_private(file: &std::fs::File) -> Result<(), String> {
    zsys::windows::privacy::check_private(file).map_err(|error| error.to_string())
}

// zcall-gui@795a85044504e844d04575c44dd8b10da7384aa8:src/core_install_windows.rs:8
fn protect_created(file: &std::fs::File) -> Result<(), String> {
    zsys::windows::privacy::protect_created(
        file,
        zsys::windows::privacy::DirectoryInheritance::ObjectOnly,
    )
    .map_err(|error| error.to_string())
}

// ztty@963afbd7f9463f6de61a96e1968fdf26d3bc8990:src/json.rs:290
fn hex4(&mut self) -> Result<u32, &'static str> {
        let mut code = 0;
        for _ in 0..4 {
            let byte = *self
                .bytes
                .get(self.position)
                .ok_or("incomplete Unicode escape")?;
            self.position += 1;
            code = code * 16
                + match byte {
                    b'0'..=b'9' => u32::from(byte - b'0'),
                    b'a'..=b'f' => u32::from(byte - b'a' + 10),
                    b'A'..=b'F' => u32::from(byte - b'A' + 10),
                    _ => return Err("invalid Unicode escape"),
                };
        }
        Ok(code)
    }

// zcall-gui@3b9a0f4673c08a9aa259b52e02858c0a88f43f6b:src/json.rs:223
fn hex4(&mut self) -> Result<u32, String> {
        let end = self.at.checked_add(4).ok_or("JSON escape overflow")?;
        let digits = self
            .text
            .get(self.at..end)
            .ok_or("Incomplete JSON escape")?;
        let value = u32::from_str_radix(digits, 16).map_err(|_| "Invalid JSON Unicode escape")?;
        self.at = end;
        Ok(value)
    }

// zmem@5997b9581f5b6962c9d9cd12774a2ce119e46ca7:src/json.rs:313
fn hex_quad(&mut self) -> Result<u16, String> {
        let mut value = 0u16;
        for _ in 0..4 {
            let digit = match self.peek() {
                Some(b'0'..=b'9') => self.peek().unwrap() - b'0',
                Some(b'a'..=b'f') => self.peek().unwrap() - b'a' + 10,
                Some(b'A'..=b'F') => self.peek().unwrap() - b'A' + 10,
                _ => return Err(self.error("invalid Unicode escape")),
            };
            value = (value << 4) | u16::from(digit);
            self.offset += 1;
        }
        Ok(value)
    }

// zgpui@d34c41f79ddab343e7468c5192885a82ca487687:src/wire.rs:468
fn hex4(&mut self) -> Result<u32, Error> {
        let mut value = 0;
        for _ in 0..4 {
            let byte = *self.bytes.get(self.position).ok_or(Error::Syntax)?;
            self.position += 1;
            value = value * 16
                + match byte {
                    b'0'..=b'9' => u32::from(byte - b'0'),
                    b'a'..=b'f' => u32::from(byte - b'a' + 10),
                    b'A'..=b'F' => u32::from(byte - b'A' + 10),
                    _ => return Err(Error::Syntax),
                };
        }
        Ok(value)
    }

// ssmcp@b5fdceea9af1b14f6f178bbc1677969fd3ff73c9:src/platform_windows.rs:51
fn current() -> io::Result<Self> {
        let mut raw = std::ptr::null_mut();
        if unsafe { OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut raw) } == 0 {
            return Err(io::Error::last_os_error());
        }
        let token = unsafe { OwnedHandle::from_raw_handle(raw) };
        fn query(token: &OwnedHandle, class: i32) -> io::Result<Vec<usize>> {
            let mut needed = 0;
            unsafe {
                GetTokenInformation(
                    token.as_raw_handle(),
                    class,
                    std::ptr::null_mut(),
                    0,
                    &mut needed,
                );
            }
            if needed == 0 {
                return Err(io::Error::last_os_error());
            }
            let mut buffer = vec![0usize; (needed as usize).div_ceil(std::mem::size_of::<usize>())];
            if unsafe {
                GetTokenInformation(
                    token.as_raw_handle(),
                    class,
                    buffer.as_mut_ptr().cast(),
                    needed,
                    &mut needed,
                )
            } == 0
            {
                return Err(io::Error::last_os_error());
            }
            Ok(buffer)
        }
        Ok(Self {
            user: query(&token, TokenUser)?,
            owner: query(&token, TokenOwner)?,
        })
    }

// ssmcp@b5fdceea9af1b14f6f178bbc1677969fd3ff73c9:src/platform_windows.rs:115
fn verify_private(file: &File, identity: &Identity) -> io::Result<()> {
    let mut owner = std::ptr::null_mut();
    let mut dacl: *mut ACL = std::ptr::null_mut();
    let mut descriptor = std::ptr::null_mut();
    let code = unsafe {
        GetSecurityInfo(
            file.as_raw_handle(),
            SE_FILE_OBJECT,
            OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION,
            &mut owner,
            std::ptr::null_mut(),
            &mut dacl,
            std::ptr::null_mut(),
            &mut descriptor,
        )
    };
    if code != 0 {
        return Err(io::Error::from_raw_os_error(code as i32));
    }
    let _guard = LocalMemory(descriptor);
    if file.metadata()?.is_dir() {
        let mut control = 0;
        let mut revision = 0;
        if unsafe { GetSecurityDescriptorControl(descriptor, &mut control, &mut revision) } == 0 {
            return Err(io::Error::last_os_error());
        }
        if control & SE_DACL_PROTECTED == 0 {
            return Err(io::Error::other(
                "output directory must have a protected private access list",
            ));
        }
    }
    if owner.is_null()
        || dacl.is_null()
        || unsafe {
            EqualSid(owner, identity.user_sid()) == 0 && EqualSid(owner, identity.owner_sid()) == 0
        }
    {
        return Err(io::Error::other(
            "output storage is not owned by the current user",
        ));
    }
    if unsafe { (*dacl).AceCount } == 0 {
        return Err(io::Error::other(
            "output storage has no private access entries",
        ));
    }
    for index in 0..unsafe { (*dacl).AceCount } as u32 {
        let mut ace = std::ptr::null_mut();
        if unsafe { GetAce(dacl, index, &mut ace) } == 0 {
            return Err(io::Error::last_os_error());
        }
        let header = unsafe { &*(ace.cast::<ACE_HEADER>()) };
        // Only ordinary allow entries for this user and SYSTEM are accepted.
        // Reject broad inherited ACLs, object/callback ACEs, and unknown layouts.
        if header.AceType != 0
            || (header.AceSize as usize) < std::mem::size_of::<ACCESS_ALLOWED_ACE>()
        {
            return Err(io::Error::other(
                "output storage has an unsupported access rule",
            ));
        }
        let allowed = unsafe { &*(ace.cast::<ACCESS_ALLOWED_ACE>()) };
        let sid = (&allowed.SidStart as *const u32).cast_mut().cast();
        if unsafe {
            EqualSid(sid, identity.user_sid()) == 0 && IsWellKnownSid(sid, WinLocalSystemSid) == 0
        } {
            return Err(io::Error::other(
                "output storage grants access to another identity",
            ));
        }
    }
    Ok(())
}
