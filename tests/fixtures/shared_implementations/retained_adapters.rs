// Real retained adapters and MD5 helpers: legal negative regression fixtures.
// Excerpts are not a standalone compiled crate; no fixture is a production source.

// ztty@963afbd7f9463f6de61a96e1968fdf26d3bc8990:src/broker/encoding.rs:11
fn unhex(value: &str) -> Result<CString, String> {
    CString::new(unhex_bytes(value)?).map_err(|_| "NUL in process metadata".into())
}

// ztty@963afbd7f9463f6de61a96e1968fdf26d3bc8990:src/broker/encoding.rs:15
fn unhex_bytes(value: &str) -> Result<Vec<u8>, String> {
    if !value.len().is_multiple_of(2) || value.bytes().any(|byte| byte.is_ascii_uppercase()) {
        return Err("invalid byte string".into());
    }
    let mut bytes = alloc::vec![0; value.len() / 2];
    zhex::decode(value.as_bytes(), &mut bytes).map_err(|_| String::from("invalid byte string"))?;
    Ok(bytes)
}

// zmem@5997b9581f5b6962c9d9cd12774a2ce119e46ca7:src/install.rs:1622
fn decode_path(text: &str) -> Result<PathBuf> {
    if !text.len().is_multiple_of(2) {
        return fail("invalid path encoding in zmem backup");
    }
    // Older backups accepted a leading plus in each two-character byte.
    // Normalize only that spelling before using the shared hexadecimal codec.
    let normalized = if text
        .as_bytes()
        .as_chunks::<2>()
        .0
        .iter()
        .any(|pair| pair[0] == b'+')
    {
        let mut normalized = text.as_bytes().to_vec();
        for pair in normalized.as_chunks_mut::<2>().0 {
            if pair[0] == b'+' {
                pair[0] = b'0';
            }
        }
        std::borrow::Cow::Owned(normalized)
    } else {
        std::borrow::Cow::Borrowed(text.as_bytes())
    };
    let mut bytes = vec![0; text.len() / 2];
    // Invalid pairs previously returned ParseIntError; retain its type and text.
    zhex::decode(&normalized, &mut bytes).map_err(|_| u8::from_str_radix("!", 16).unwrap_err())?;
    if bytes.contains(&0) {
        return fail("NUL in zmem backup path");
    }
    Ok(PathBuf::from(OsString::from_vec(bytes)))
}

// zuse@13be18166f9f1bdfb219da851c28b3319fdb7653:src/browser.rs:1853
fn base64_error(input: &[u8], error: z64::Error) -> String {
    match error {
        z64::Error::InvalidLength { .. }
        | z64::Error::LengthOverflow
        | z64::Error::OutputTooSmall { .. } => "invalid base64 length",
        z64::Error::NonCanonical { .. } => "non-canonical base64 padding",
        z64::Error::InvalidByte { index, .. } | z64::Error::InvalidPadding { index } => {
            // Preserve the browser's diagnostic precedence within the failing
            // quantum. z64 alone validates and converts the encoded bytes.
            let start = index / 4 * 4;
            let chunk = &input[start..start + 4];
            if index % 4 >= 2
                && ((chunk[2] == b'=' && chunk[3] != b'=')
                    || ((chunk[2] == b'=' || chunk[3] == b'=') && start + 4 != input.len()))
            {
                "invalid base64 padding"
            } else {
                "invalid base64 character"
            }
        }
    }
    .into()
}

// zcalld@6eab1150e8d58d330583c1b3206bf91e7862dc9a:crates/zcalld-compat-client/src/lib.rs:338
fn worker_encoding_error(bytes: &[u8]) -> &'static str {
    // Only classify a codec rejection here: preserve the original left-to-right
    // padding/character diagnostic without implementing byte decoding again.
    let mut padding = false;
    for (index, &byte) in bytes.iter().enumerate() {
        if byte == b'=' {
            if index % 4 < 2 || index / 4 + 1 != bytes.len() / 4 {
                return "invalid base64 padding";
            }
            padding = true;
        } else if padding {
            return "invalid base64 padding";
        } else if !byte.is_ascii_alphanumeric() && !matches!(byte, b'+' | b'/') {
            return "invalid base64 character";
        }
    }
    "invalid encoded worker output"
}

// zmcl@61c3655806fee9f4a20fc8bea2e881ce0531fc48:crates/zmcl-core/src/hash.rs:20
fn update(&mut self, mut input: &[u8], mut compress: impl FnMut(&[u8; 64])) {
        self.bytes = self.bytes.wrapping_add(input.len() as u64);
        if self.used != 0 {
            let n = (64 - self.used).min(input.len());
            self.block[self.used..self.used + n].copy_from_slice(&input[..n]);
            self.used += n;
            input = &input[n..];
            if self.used == 64 {
                compress(&self.block);
                self.used = 0;
            }
        }
        while input.len() >= 64 {
            let (block, rest) = input.split_at(64);
            compress(block.try_into().expect("exact block"));
            input = rest;
        }
        if !input.is_empty() {
            self.block[..input.len()].copy_from_slice(input);
            self.used = input.len();
        }
    }

// zmcl@61c3655806fee9f4a20fc8bea2e881ce0531fc48:crates/zmcl-core/src/hash.rs:42
fn finish(mut self, little_endian: bool, mut compress: impl FnMut(&[u8; 64])) {
        let bits = self.bytes.wrapping_mul(8);
        self.update(&[0x80], &mut compress);
        let padding = if self.used <= 56 {
            56 - self.used
        } else {
            120 - self.used
        };
        self.update(&[0; 64][..padding], &mut compress);
        self.update(
            &if little_endian {
                bits.to_le_bytes()
            } else {
                bits.to_be_bytes()
            },
            compress,
        );
    }

// zmcl@61c3655806fee9f4a20fc8bea2e881ce0531fc48:crates/zmcl-core/src/hash.rs:71
fn update(&mut self, bytes: &[u8]) {
        self.inner.get_or_insert_with(sha1::Sha1::new).update(bytes);
    }

// zmcl@61c3655806fee9f4a20fc8bea2e881ce0531fc48:crates/zmcl-core/src/hash.rs:74
fn finalize(self) -> [u8; 20] {
        self.inner.unwrap_or_default().finalize().into()
    }

// zmcl@61c3655806fee9f4a20fc8bea2e881ce0531fc48:crates/zmcl-core/src/hash.rs:88
fn update(&mut self, bytes: &[u8]) {
        self.inner
            .get_or_insert_with(sha2::Sha256::new)
            .update(bytes);
    }

// zmcl@61c3655806fee9f4a20fc8bea2e881ce0531fc48:crates/zmcl-core/src/hash.rs:93
fn finalize(self) -> [u8; 32] {
        self.inner.unwrap_or_default().finalize().into()
    }

// zmcl@61c3655806fee9f4a20fc8bea2e881ce0531fc48:crates/zmcl-core/src/hash.rs:115
fn update(&mut self, bytes: &[u8]) {
        let state = &mut self.state;
        self.blocks.update(bytes, |block| md5_block(state, block));
    }

// zmcl@61c3655806fee9f4a20fc8bea2e881ce0531fc48:crates/zmcl-core/src/hash.rs:119
fn finalize(mut self) -> [u8; 16] {
        self.blocks
            .finish(true, |block| md5_block(&mut self.state, block));
        let mut out = [0; 16];
        for (word, chunk) in self.state.iter().zip(out.as_chunks_mut::<4>().0.iter_mut()) {
            chunk.copy_from_slice(&word.to_le_bytes());
        }
        out
    }

// zmcl@61c3655806fee9f4a20fc8bea2e881ce0531fc48:crates/zmcl-core/src/hash.rs:129
fn md5_block(s: &mut [u32; 4], input: &[u8; 64]) {
    const ROT: [u32; 64] = [
        7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 5, 9, 14, 20, 5, 9, 14, 20, 5,
        9, 14, 20, 5, 9, 14, 20, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 6, 10,
        15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
    ];
    const K: [u32; 64] = [
        0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee, 0xf57c0faf, 0x4787c62a, 0xa8304613,
        0xfd469501, 0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be, 0x6b901122, 0xfd987193,
        0xa679438e, 0x49b40821, 0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa, 0xd62f105d,
        0x02441453, 0xd8a1e681, 0xe7d3fbc8, 0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
        0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a, 0xfffa3942, 0x8771f681, 0x6d9d6122,
        0xfde5380c, 0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70, 0x289b7ec6, 0xeaa127fa,
        0xd4ef3085, 0x04881d05, 0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665, 0xf4292244,
        0x432aff97, 0xab9423a7, 0xfc93a039, 0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
        0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1, 0xf7537e82, 0xbd3af235, 0x2ad7d2bb,
        0xeb86d391,
    ];
    let mut m = [0u32; 16];
    for (i, b) in input.as_chunks::<4>().0.iter().enumerate() {
        m[i] = u32::from_le_bytes(*b);
    }
    let [mut a, mut b, mut c, mut d] = *s;
    for i in 0..64 {
        let (f, g) = match i {
            0..16 => ((b & c) | (!b & d), i),
            16..32 => ((d & b) | (!d & c), (5 * i + 1) % 16),
            32..48 => (b ^ c ^ d, (3 * i + 5) % 16),
            _ => (c ^ (b | !d), (7 * i) % 16),
        };
        let next = b.wrapping_add(
            a.wrapping_add(f)
                .wrapping_add(K[i])
                .wrapping_add(m[g])
                .rotate_left(ROT[i]),
        );
        a = d;
        d = c;
        c = b;
        b = next;
    }
    for (v, x) in s.iter_mut().zip([a, b, c, d]) {
        *v = v.wrapping_add(x);
    }
}
