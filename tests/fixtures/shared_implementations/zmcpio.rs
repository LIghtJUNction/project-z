// Historical source excerpts for regression tests only; not a compiled crate.
// Provenance and exact fingerprints: scripts/shared_implementations.json.

// zmcpio@89a247ac274bcd96b760dd9e7dcb0d4d924a901e:src/http.rs:703
fn encode_value(value: &str, w: &mut Bytes<'_>) {
    let sentinel = value.starts_with("=?base64?") && value.ends_with("?=");
    if field_value(value) && value.trim_matches([' ', '\t']) == value && !sentinel {
        w.raw(value.as_bytes());
        return;
    }
    const TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    w.raw(b"=?base64?");
    for chunk in value.as_bytes().chunks(3) {
        let a = chunk[0];
        let b = chunk.get(1).copied().unwrap_or(0);
        let c = chunk.get(2).copied().unwrap_or(0);
        w.raw(&[
            TABLE[(a >> 2) as usize],
            TABLE[(((a & 3) << 4) | (b >> 4)) as usize],
            if chunk.len() > 1 {
                TABLE[(((b & 15) << 2) | (c >> 6)) as usize]
            } else {
                b'='
            },
            if chunk.len() > 2 {
                TABLE[(c & 63) as usize]
            } else {
                b'='
            },
        ]);
    }
    w.raw(b"?=");
}

// zmcpio@89a247ac274bcd96b760dd9e7dcb0d4d924a901e:src/http.rs:733
fn decode_header_value<'a>(value: &'a str, output: &'a mut [u8]) -> Result<&'a str, HttpError> {
    if !field_value(value) {
        return Err(HttpError::InvalidHeader);
    }
    let Some(encoded) = value
        .strip_prefix("=?base64?")
        .and_then(|s| s.strip_suffix("?="))
    else {
        if value.trim_matches([' ', '\t']) != value {
            return Err(HttpError::InvalidHeader);
        }
        return Ok(value);
    };
    let input = encoded.as_bytes();
    if input.len() % 4 != 0 {
        return Err(HttpError::InvalidHeader);
    }
    let padding = usize::from(input.last() == Some(&b'='))
        + usize::from(input.len() >= 2 && input[input.len() - 2] == b'=');
    let needed = input.len() / 4 * 3 - padding;
    if output.len() < needed {
        return Err(HttpError::Capacity { needed });
    }
    let mut at = 0;
    for (index, chunk) in input.as_chunks::<4>().0.iter().enumerate() {
        let last = index + 1 == input.len() / 4;
        let a = base64(chunk[0])?;
        let b = base64(chunk[1])?;
        let c = if chunk[2] == b'=' {
            0
        } else {
            base64(chunk[2])?
        };
        let d = if chunk[3] == b'=' {
            0
        } else {
            base64(chunk[3])?
        };
        if (chunk[2] == b'=' && (chunk[3] != b'=' || b & 15 != 0))
            || (chunk[3] == b'=' && chunk[2] != b'=' && c & 3 != 0)
            || (!last && chunk.contains(&b'='))
        {
            return Err(HttpError::InvalidHeader);
        }
        output[at] = (a << 2) | (b >> 4);
        at += 1;
        if chunk[2] != b'=' {
            output[at] = (b << 4) | (c >> 2);
            at += 1;
        }
        if chunk[3] != b'=' {
            output[at] = (c << 6) | d;
            at += 1;
        }
    }
    core::str::from_utf8(&output[..at]).map_err(|_| HttpError::InvalidHeader)
}
