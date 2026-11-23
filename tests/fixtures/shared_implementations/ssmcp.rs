// Historical source excerpts for regression tests only; not a compiled crate.
// Provenance and exact fingerprints: scripts/shared_implementations.json.

// ssmcp@1388cf11458eb88618ceedd4be8194d9ec026277:src/hex.rs:6
fn encode(bytes: impl AsRef<[u8]>) -> String {
    let bytes = bytes.as_ref();
    let mut text = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        write!(&mut text, "{byte:02x}").expect("writing to String");
    }
    text
}
