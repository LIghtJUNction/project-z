// Historical source excerpts for regression tests only; not a compiled crate.
// Provenance and exact fingerprints: scripts/shared_implementations.json.

// zterm@f1da2db1613f97d613ed98b7f3e8cae231e5eae1:src/clipboard.rs:22
fn reply(&self, selector: u8, text: Option<&[u8]>) -> Vec<u8> {
        let text = text
            .filter(|bytes| {
                bytes.len() <= MAX_CLIPBOARD_BYTES
                    && !bytes.contains(&0)
                    && core::str::from_utf8(bytes).is_ok()
            })
            .unwrap_or_default();
        let selector = if self.selectors().contains(&selector) {
            selector
        } else {
            self.selectors[0]
        };
        let mut bytes = Vec::with_capacity(9 + text.len().div_ceil(3) * 4);
        bytes.extend_from_slice(b"\x1b]52;");
        bytes.push(selector);
        bytes.push(b';');
        const ALPHABET: &[u8; 64] =
            b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        for group in text.chunks(3) {
            let a = group[0];
            let b = group.get(1).copied().unwrap_or(0);
            let c = group.get(2).copied().unwrap_or(0);
            bytes.push(ALPHABET[usize::from(a >> 2)]);
            bytes.push(ALPHABET[usize::from((a & 3) << 4 | b >> 4)]);
            bytes.push(if group.len() > 1 {
                ALPHABET[usize::from((b & 15) << 2 | c >> 6)]
            } else {
                b'='
            });
            bytes.push(if group.len() > 2 {
                ALPHABET[usize::from(c & 63)]
            } else {
                b'='
            });
        }
        if self.bell_terminated {
            bytes.push(7);
        } else {
            bytes.extend_from_slice(b"\x1b\\");
        }
        bytes
    }

// zterm@f1da2db1613f97d613ed98b7f3e8cae231e5eae1:src/clipboard.rs:189
fn decode(bytes: &[u8]) -> Result<Vec<u8>, DecodeError> {
    if bytes.len() > MAX_CLIPBOARD_BYTES.div_ceil(3) * 4 {
        return Err(DecodeError::Limit);
    }
    if !bytes.len().is_multiple_of(4) {
        return Err(DecodeError::Invalid);
    }
    let padding = usize::from(bytes.last() == Some(&b'='))
        + usize::from(bytes.len() > 1 && bytes.get(bytes.len() - 2) == Some(&b'='));
    let size = (bytes.len() / 4 * 3).saturating_sub(padding);
    if size > MAX_CLIPBOARD_BYTES {
        return Err(DecodeError::Limit);
    }
    let mut out = Vec::with_capacity(size);
    for (i, group) in bytes.as_chunks::<4>().0.iter().enumerate() {
        let a = digit(group[0]).ok_or(DecodeError::Invalid)?;
        let b = digit(group[1]).ok_or(DecodeError::Invalid)?;
        let last = i + 1 == bytes.len() / 4;
        let c = if group[2] == b'=' && last {
            0
        } else {
            digit(group[2]).ok_or(DecodeError::Invalid)?
        };
        let d = if group[3] == b'=' && last {
            0
        } else {
            digit(group[3]).ok_or(DecodeError::Invalid)?
        };
        if group[2] == b'=' && (group[3] != b'=' || b & 15 != 0)
            || group[3] == b'=' && group[2] != b'=' && c & 3 != 0
        {
            return Err(DecodeError::Invalid);
        }
        out.push(a << 2 | b >> 4);
        if group[2] != b'=' {
            out.push(b << 4 | c >> 2);
        }
        if group[3] != b'=' {
            out.push(c << 6 | d);
        }
    }
    Ok(out)
}
