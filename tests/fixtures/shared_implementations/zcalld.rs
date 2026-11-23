// Historical source excerpts for regression tests only; not a compiled crate.
// Provenance and exact fingerprints: scripts/shared_implementations.json.

// zcalld@8e52d791c305a3730d2ea876b8dffb6be2e2c04c:src/digest.rs:2
fn sha256(bytes: &[u8]) -> String {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let mut state = [
        0x6a09e667u32,
        0xbb67ae85,
        0x3c6ef372,
        0xa54ff53a,
        0x510e527f,
        0x9b05688c,
        0x1f83d9ab,
        0x5be0cd19,
    ];
    let mut data = bytes.to_vec();
    let bits = (bytes.len() as u64) * 8;
    data.push(0x80);
    while data.len() % 64 != 56 {
        data.push(0);
    }
    data.extend_from_slice(&bits.to_be_bytes());
    for block in data.as_chunks::<64>().0 {
        let mut words = [0u32; 64];
        for (i, c) in block.as_chunks::<4>().0.iter().enumerate() {
            words[i] = u32::from_be_bytes(*c);
        }
        for i in 16..64 {
            let a = words[i - 15];
            let b = words[i - 2];
            words[i] = words[i - 16]
                .wrapping_add(a.rotate_right(7) ^ a.rotate_right(18) ^ (a >> 3))
                .wrapping_add(words[i - 7])
                .wrapping_add(b.rotate_right(17) ^ b.rotate_right(19) ^ (b >> 10));
        }
        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut h] = state;
        for i in 0..64 {
            let t1 = h
                .wrapping_add(e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25))
                .wrapping_add((e & f) ^ (!e & g))
                .wrapping_add(K[i])
                .wrapping_add(words[i]);
            let t2 = (a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22))
                .wrapping_add((a & b) ^ (a & c) ^ (b & c));
            h = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        for (s, v) in state.iter_mut().zip([a, b, c, d, e, f, g, h]) {
            *s = s.wrapping_add(v);
        }
    }
    state.iter().map(|v| format!("{v:08x}")).collect()
}

// zcalld@8e52d791c305a3730d2ea876b8dffb6be2e2c04c:crates/zcalld-installer/src/hash.rs:45
fn compress(&mut self) {
        let mut words = [0u32; 64];
        for (i, chunk) in self.block.as_chunks::<4>().0.iter().enumerate() {
            words[i] = u32::from_be_bytes(*chunk);
        }
        for i in 16..64 {
            let a = words[i - 15];
            let b = words[i - 2];
            words[i] = words[i - 16]
                .wrapping_add(a.rotate_right(7) ^ a.rotate_right(18) ^ (a >> 3))
                .wrapping_add(words[i - 7])
                .wrapping_add(b.rotate_right(17) ^ b.rotate_right(19) ^ (b >> 10));
        }
        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut h] = self.state;
        for i in 0..64 {
            let t = h
                .wrapping_add(e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25))
                .wrapping_add((e & f) ^ (!e & g))
                .wrapping_add(K[i])
                .wrapping_add(words[i]);
            let u = (a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22))
                .wrapping_add((a & b) ^ (a & c) ^ (b & c));
            h = g;
            g = f;
            f = e;
            e = d.wrapping_add(t);
            d = c;
            c = b;
            b = a;
            a = t.wrapping_add(u);
        }
        for (s, v) in self.state.iter_mut().zip([a, b, c, d, e, f, g, h]) {
            *s = s.wrapping_add(v);
        }
    }

// zcalld@8e52d791c305a3730d2ea876b8dffb6be2e2c04c:crates/zcalld-compat-client/src/lib.rs:311
fn encode(data: &[u8]) -> String {
    let mut out = String::with_capacity(data.len().div_ceil(3) * 4);
    for c in data.chunks(3) {
        let v = ((c[0] as u32) << 16)
            | ((c.get(1).copied().unwrap_or(0) as u32) << 8)
            | (c.get(2).copied().unwrap_or(0) as u32);
        for shift in [18, 12, 6, 0] {
            out.push(B64[((v >> shift) & 63) as usize] as char)
        }
        if c.len() < 3 {
            out.pop();
            out.push('=');
        }
        if c.len() == 1 {
            out.pop();
            out.pop();
            out.push('=');
            out.push('=');
        }
    }
    out
}

// zcalld@8e52d791c305a3730d2ea876b8dffb6be2e2c04c:crates/zcalld-compat-client/src/lib.rs:333
fn decode(s: &str) -> Result<Vec<u8>, String> {
    if !s.len().is_multiple_of(4) || s.len() > MAX_LINE {
        return Err("invalid encoded worker output".into());
    }
    let mut out = Vec::with_capacity(s.len() / 4 * 3);
    for (index, c) in s.as_bytes().chunks(4).enumerate() {
        let mut v = 0u32;
        let mut padding = 0;
        for (at, b) in c.iter().enumerate() {
            v <<= 6;
            if *b == b'=' {
                if at < 2 {
                    return Err("invalid base64 padding".into());
                }
                padding += 1;
            } else {
                if padding != 0 {
                    return Err("invalid base64 padding".into());
                }
                v |= B64
                    .iter()
                    .position(|x| x == b)
                    .ok_or("invalid base64 character")? as u32;
            }
        }
        if padding > 0 && index + 1 != s.len() / 4 {
            return Err("invalid base64 padding".into());
        }
        out.push((v >> 16) as u8);
        if padding < 2 {
            out.push((v >> 8) as u8)
        }
        if padding == 0 {
            out.push(v as u8)
        }
    }
    Ok(out)
}

// zcalld@6eab1150e8d58d330583c1b3206bf91e7862dc9a:crates/zcalld-compat-client/src/lib.rs:290
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
            c if c < ' ' => {
                use std::fmt::Write;
                let _ = write!(out, "\\u{:04x}", c as u32);
            }
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

// zcalld@6eab1150e8d58d330583c1b3206bf91e7862dc9a:src/privacy_windows.rs:70
fn protect(file: &std::fs::File) -> Result<(), String> {
    let error =
        || "cannot restrict the private file to this Windows account and SYSTEM".to_string();
    // Reprotecting an existing directory must not remove its children's inherited
    // access. Both inheritable ACEs still name only this account and SYSTEM.
    let inheritance = if file.metadata().map_err(|_| error())?.is_dir() {
        "OICI"
    } else {
        ""
    };
    let mut token = ptr::null_mut();
    // SAFETY: handles and output buffers follow the synchronous Win32 contracts.
    unsafe {
        if OpenProcessToken(GetCurrentProcess(), 8, &mut token) == 0 {
            return Err(error());
        }
        let token = Token(token);
        let mut size = 0;
        GetTokenInformation(token.0, 1, ptr::null_mut(), 0, &mut size);
        if size == 0 || size > 65536 {
            return Err(error());
        }
        let mut storage = vec![0usize; (size as usize).div_ceil(std::mem::size_of::<usize>())];
        if GetTokenInformation(token.0, 1, storage.as_mut_ptr().cast(), size, &mut size) == 0 {
            return Err(error());
        }
        let sid = *(storage.as_ptr().cast::<*mut c_void>());
        let mut raw = ptr::null_mut();
        if ConvertSidToStringSidW(sid, &mut raw) == 0 || raw.is_null() {
            return Err(error());
        }
        let sid_memory = Local(raw.cast());
        let mut length = 0;
        while length < 256 && *raw.add(length) != 0 {
            length += 1;
        }
        if length == 256 {
            return Err(error());
        }
        let sid =
            String::from_utf16(std::slice::from_raw_parts(raw, length)).map_err(|_| error())?;
        drop(sid_memory);
        let text = format!("D:P(A;{inheritance};FA;;;{sid})(A;{inheritance};FA;;;SY)")
            .encode_utf16()
            .chain([0])
            .collect::<Vec<_>>();
        let mut descriptor = ptr::null_mut();
        if ConvertStringSecurityDescriptorToSecurityDescriptorW(
            text.as_ptr(),
            1,
            &mut descriptor,
            ptr::null_mut(),
        ) == 0
        {
            return Err(error());
        }
        let descriptor = Local(descriptor);
        let mut present = 0;
        let mut defaulted = 0;
        let mut acl = ptr::null_mut();
        if GetSecurityDescriptorDacl(descriptor.0, &mut present, &mut acl, &mut defaulted) == 0
            || present == 0
            || acl.is_null()
        {
            return Err(error());
        }
        if SetSecurityInfo(
            file.as_raw_handle(),
            1,
            0x80000004,
            ptr::null_mut(),
            ptr::null_mut(),
            acl,
            ptr::null_mut(),
        ) != 0
        {
            return Err(error());
        }
    }
    Ok(())
}

// zcalld@6eab1150e8d58d330583c1b3206bf91e7862dc9a:src/privacy_windows.rs:217
fn check_private(file: &std::fs::File) -> Result<(), String> {
    let error = || {
        "private Windows files must be owned by this account and accessible only to it and SYSTEM"
            .to_string()
    };
    let directory = file.metadata().map_err(|_| error())?.is_dir();
    let user = private_user()?;
    #[repr(C)]
    struct AclSize {
        count: u32,
        used: u32,
        free: u32,
    }
    let mut owner = ptr::null_mut();
    let mut acl = ptr::null_mut();
    let mut descriptor = ptr::null_mut();
    // SAFETY: GetSecurityInfo returns one LocalFree-owned descriptor. Its SID and
    // ACL pointers remain live until the Local guard is dropped below.
    unsafe {
        if GetSecurityInfo(
            file.as_raw_handle(),
            1,
            1 | 4,
            &mut owner,
            ptr::null_mut(),
            &mut acl,
            ptr::null_mut(),
            &mut descriptor,
        ) != 0
            || descriptor.is_null()
        {
            return Err(error());
        }
        let descriptor = Local(descriptor);
        let user_sid = *(user.as_ptr().cast::<*mut c_void>());
        if owner.is_null() || acl.is_null() || EqualSid(owner, user_sid) == 0 {
            return Err(error());
        }
        let mut control = 0;
        let mut revision = 0;
        if GetSecurityDescriptorControl(descriptor.0, &mut control, &mut revision) == 0
            || control & 0x1000 == 0
        {
            return Err(error());
        }
        let mut size = AclSize {
            count: 0,
            used: 0,
            free: 0,
        };
        if GetAclInformation(
            acl,
            (&mut size as *mut AclSize).cast(),
            std::mem::size_of::<AclSize>() as u32,
            2,
        ) == 0
            || size.count == 0
            || size.count > 2
            || size.used > 65536
        {
            return Err(error());
        }
        let mut system = [0usize; 16];
        let mut system_size = std::mem::size_of_val(&system) as u32;
        if CreateWellKnownSid(
            22,
            ptr::null(),
            system.as_mut_ptr().cast(),
            &mut system_size,
        ) == 0
        {
            return Err(error());
        }
        let mut found_user = false;
        let mut found_system = false;
        for index in 0..size.count {
            let mut ace = ptr::null_mut();
            if GetAce(acl, index, &mut ace) == 0 || ace.is_null() {
                return Err(error());
            }
            let bytes = ace.cast::<u8>();
            let offset = (bytes as usize)
                .checked_sub(acl as usize)
                .ok_or_else(error)?;
            if offset.checked_add(8).is_none_or(|n| n > size.used as usize) {
                return Err(error());
            }
            let length = ptr::read_unaligned(bytes.add(2).cast::<u16>()) as usize;
            let flags = *bytes.add(1);
            if *bytes != 0
                || !(flags == 0 || (directory && flags == 0x03))
                || length < 16
                || offset
                    .checked_add(length)
                    .is_none_or(|n| n > size.used as usize)
            {
                return Err(error());
            }
            let sid = bytes.add(8).cast::<c_void>();
            if GetLengthSid(sid) as usize > length - 8 || IsValidSid(sid) == 0 {
                return Err(error());
            }
            let is_user = EqualSid(sid, user_sid) != 0;
            let is_system = EqualSid(sid, system.as_ptr().cast()) != 0;
            if !is_user && !is_system {
                return Err(error());
            }
            found_user |= is_user;
            found_system |= is_system;
        }
        if !found_user || !found_system {
            return Err(error());
        }
    }
    Ok(())
}

// zcalld@6eab1150e8d58d330583c1b3206bf91e7862dc9a:src/privacy_windows.rs:338
fn protect_created(file: &std::fs::File) -> Result<(), String> {
    let user = private_user()?;
    // SAFETY: the token SID remains inside the live user buffer for this call.
    let result = unsafe {
        SetSecurityInfo(
            file.as_raw_handle(),
            1,
            1,
            *(user.as_ptr().cast::<*mut c_void>()),
            ptr::null_mut(),
            ptr::null_mut(),
            ptr::null_mut(),
        )
    };
    if result != 0 {
        return Err("cannot set the new private object's Windows owner".into());
    }
    protect(file)?;
    check_private(file)
}
