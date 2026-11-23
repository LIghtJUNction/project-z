// Historical source excerpts for regression tests only; not a compiled crate.
// Provenance and exact fingerprints: scripts/shared_implementations.json.

// zuse@f13412e3c148ecf01c347423caba509d45df9ccc:src/browser.rs:1834
fn encode_base64(bytes: &[u8]) -> String {
    const ALPHABET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut output = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let bits = ((chunk[0] as u32) << 16)
            | ((chunk.get(1).copied().unwrap_or(0) as u32) << 8)
            | chunk.get(2).copied().unwrap_or(0) as u32;
        output.push(ALPHABET[(bits >> 18) as usize] as char);
        output.push(ALPHABET[((bits >> 12) & 63) as usize] as char);
        output.push(if chunk.len() > 1 {
            ALPHABET[((bits >> 6) & 63) as usize] as char
        } else {
            '='
        });
        output.push(if chunk.len() > 2 {
            ALPHABET[(bits & 63) as usize] as char
        } else {
            '='
        });
    }
    output
}

// zuse@f13412e3c148ecf01c347423caba509d45df9ccc:src/browser.rs:1857
fn decode_base64(text: &str) -> Result<Vec<u8>> {
    if !text.len().is_multiple_of(4) || text.len() > MAX_MESSAGE {
        return Err("invalid base64 length".into());
    }
    let mut output = Vec::with_capacity(text.len() / 4 * 3);
    let value = |byte: u8| -> Result<u8> {
        match byte {
            b'A'..=b'Z' => Ok(byte - b'A'),
            b'a'..=b'z' => Ok(byte - b'a' + 26),
            b'0'..=b'9' => Ok(byte - b'0' + 52),
            b'+' => Ok(62),
            b'/' => Ok(63),
            _ => Err("invalid base64 character".into()),
        }
    };
    for (index, chunk) in text.as_bytes().as_chunks::<4>().0.iter().enumerate() {
        let last = (index + 1) * 4 == text.len();
        let a = value(chunk[0])?;
        let b = value(chunk[1])?;
        let pad_c = chunk[2] == b'=';
        let pad_d = chunk[3] == b'=';
        if (pad_c && !pad_d) || ((pad_c || pad_d) && !last) {
            return Err("invalid base64 padding".into());
        }
        let c = if pad_c { 0 } else { value(chunk[2])? };
        let d = if pad_d { 0 } else { value(chunk[3])? };
        if (pad_c && b & 15 != 0) || (pad_d && !pad_c && c & 3 != 0) {
            return Err("non-canonical base64 padding".into());
        }
        output.push((a << 2) | (b >> 4));
        if !pad_c {
            output.push((b << 4) | (c >> 2));
        }
        if !pad_d {
            output.push((c << 6) | d);
        }
    }
    Ok(output)
}

// zuse@f13412e3c148ecf01c347423caba509d45df9ccc:src/browser.rs:1897
fn sha1(input: &[u8]) -> [u8; 20] {
    let mut bytes = input.to_vec();
    bytes.push(0x80);
    while bytes.len() % 64 != 56 {
        bytes.push(0);
    }
    bytes.extend_from_slice(&((input.len() as u64) * 8).to_be_bytes());
    let mut state = [
        0x67452301u32,
        0xefcdab89,
        0x98badcfe,
        0x10325476,
        0xc3d2e1f0,
    ];
    for chunk in bytes.as_chunks::<64>().0 {
        let mut words = [0u32; 80];
        for (i, bytes) in chunk.as_chunks::<4>().0.iter().enumerate() {
            words[i] = u32::from_be_bytes(*bytes);
        }
        for i in 16..80 {
            words[i] = (words[i - 3] ^ words[i - 8] ^ words[i - 14] ^ words[i - 16]).rotate_left(1);
        }
        let [mut a, mut b, mut c, mut d, mut e] = state;
        for (i, word) in words.into_iter().enumerate() {
            let (f, k) = match i {
                0..=19 => ((b & c) | ((!b) & d), 0x5a827999),
                20..=39 => (b ^ c ^ d, 0x6ed9eba1),
                40..=59 => ((b & c) | (b & d) | (c & d), 0x8f1bbcdc),
                _ => (b ^ c ^ d, 0xca62c1d6),
            };
            let next = a
                .rotate_left(5)
                .wrapping_add(f)
                .wrapping_add(e)
                .wrapping_add(k)
                .wrapping_add(word);
            e = d;
            d = c;
            c = b.rotate_left(30);
            b = a;
            a = next;
        }
        for (item, value) in state.iter_mut().zip([a, b, c, d, e]) {
            *item = item.wrapping_add(value);
        }
    }
    let mut output = [0; 20];
    for (chunk, value) in output.as_chunks_mut::<4>().0.iter_mut().zip(state) {
        chunk.copy_from_slice(&value.to_be_bytes());
    }
    output
}

// zuse@13be18166f9f1bdfb219da851c28b3319fdb7653:src/json.rs:7
fn quote(text: &str) -> String {
    let mut s = String::with_capacity(text.len() + 2);
    s.push('"');
    for c in text.chars() {
        match c {
            '"' => s.push_str("\\\""),
            '\\' => s.push_str("\\\\"),
            '\n' => s.push_str("\\n"),
            '\r' => s.push_str("\\r"),
            '\t' => s.push_str("\\t"),
            c if c < ' ' => {
                let _ = write!(s, "\\u{:04x}", c as u32);
            }
            c => s.push(c),
        }
    }
    s.push('"');
    s
}
