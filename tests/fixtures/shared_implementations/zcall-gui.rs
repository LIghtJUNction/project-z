// Historical source excerpts for regression tests only; not a compiled crate.
// Provenance and exact fingerprints: scripts/shared_implementations.json.

// zcall-gui@daa540307573d86838b108f4a76aa45230fca5f5:src/updater.rs:335
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

// zcall-gui@3b9a0f4673c08a9aa259b52e02858c0a88f43f6b:src/json.rs:65
fn quote(value: &str) -> String {
    let mut out = String::from("\"");
    for character in value.chars() {
        match character {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c < ' ' => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

// zcall-gui@3b9a0f4673c08a9aa259b52e02858c0a88f43f6b:src/core_install_windows.rs:61
fn protect(file: &std::fs::File) -> Result<(), String> {
    let error =
        || "cannot restrict the private file to this Windows account and SYSTEM".to_string();
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
        let text = format!("D:P(A;;FA;;;{sid})(A;;FA;;;SY)")
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

// zcall-gui@3b9a0f4673c08a9aa259b52e02858c0a88f43f6b:src/core_install_windows.rs:201
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

// zcall-gui@3b9a0f4673c08a9aa259b52e02858c0a88f43f6b:src/core_install_windows.rs:322
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
