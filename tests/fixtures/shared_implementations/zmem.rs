// Historical source excerpts for regression tests only; not a compiled crate.
// Provenance and exact fingerprints: scripts/shared_implementations.json.

// zmem@ff07982d751f48cbf4c9fca554760c658d882d43:src/install.rs:1615
fn encode_path(path: &Path) -> String {
    const HEX: &[u8] = b"0123456789abcdef";
    let mut text = String::with_capacity(path.as_os_str().as_bytes().len() * 2);
    for byte in path.as_os_str().as_bytes() {
        text.push(HEX[(byte >> 4) as usize] as char);
        text.push(HEX[(byte & 15) as usize] as char);
    }
    text
}

// zmem@ff07982d751f48cbf4c9fca554760c658d882d43:src/install.rs:1625
fn decode_path(text: &str) -> Result<PathBuf> {
    if text.len() % 2 != 0 {
        return fail("invalid path encoding in zmem backup");
    }
    let bytes: std::result::Result<Vec<_>, _> = text
        .as_bytes()
        .chunks_exact(2)
        .map(|pair| u8::from_str_radix(std::str::from_utf8(pair).unwrap_or("!"), 16))
        .collect();
    let bytes = bytes?;
    if bytes.contains(&0) {
        return fail("NUL in zmem backup path");
    }
    Ok(PathBuf::from(OsString::from_vec(bytes)))
}

// zmem@5997b9581f5b6962c9d9cd12774a2ce119e46ca7:src/json.rs:6
fn quote(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 32 => {
                let _ = write!(out, "\\u{:04x}", c as u32);
            }
            _ => out.push(c),
        }
    }
    out.push('"');
    out
}
