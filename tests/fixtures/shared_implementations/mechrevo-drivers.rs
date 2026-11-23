// Historical source excerpts for regression tests only; not a compiled crate.
// Provenance and exact fingerprints: scripts/shared_implementations.json.

// mechrevo-drivers@aaa7573dd2609e74936ba4c3724b169de1834f54:console/crates/core/src/brightness.rs:617
fn base64(bytes: &[u8]) -> String {
        const TABLE: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        let mut result = String::new();
        for bytes in bytes.chunks(3) {
            let a = bytes[0];
            let b = *bytes.get(1).unwrap_or(&0);
            let c = *bytes.get(2).unwrap_or(&0);
            result.push(TABLE[(a >> 2) as usize] as char);
            result.push(TABLE[(((a & 3) << 4) | (b >> 4)) as usize] as char);
            result.push(if bytes.len() > 1 {
                TABLE[(((b & 15) << 2) | (c >> 6)) as usize] as char
            } else {
                '='
            });
            result.push(if bytes.len() > 2 {
                TABLE[(c & 63) as usize] as char
            } else {
                '='
            });
        }
        result
    }
