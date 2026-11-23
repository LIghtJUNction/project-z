//! A bounded native diagnostic for the unchanged zsys directory ACL contract.
//! It prints the stored descriptor and handle metadata before the real tests.
use std::{
    ffi::c_void,
    fs::{self, File},
    os::windows::{fs::OpenOptionsExt, io::AsRawHandle},
    ptr,
};

#[link(name = "advapi32")]
unsafe extern "system" {
    fn GetSecurityInfo(
        handle: *mut c_void,
        kind: u32,
        information: u32,
        owner: *mut *mut c_void,
        group: *mut *mut c_void,
        dacl: *mut *mut c_void,
        sacl: *mut *mut c_void,
        descriptor: *mut *mut c_void,
    ) -> u32;
    fn ConvertSidToStringSidW(sid: *mut c_void, text: *mut *mut u16) -> i32;
    fn ConvertSecurityDescriptorToStringSecurityDescriptorW(
        descriptor: *mut c_void,
        revision: u32,
        information: u32,
        text: *mut *mut u16,
        length: *mut u32,
    ) -> i32;
    fn ConvertStringSecurityDescriptorToSecurityDescriptorW(
        text: *const u16,
        revision: u32,
        descriptor: *mut *mut c_void,
        length: *mut u32,
    ) -> i32;
    fn GetSecurityDescriptorDacl(
        descriptor: *mut c_void,
        present: *mut i32,
        acl: *mut *mut c_void,
        defaulted: *mut i32,
    ) -> i32;
    fn SetSecurityInfo(
        handle: *mut c_void,
        kind: u32,
        information: u32,
        owner: *mut c_void,
        group: *mut c_void,
        dacl: *mut c_void,
        sacl: *mut c_void,
    ) -> u32;
}
#[link(name = "kernel32")]
unsafe extern "system" {
    fn LocalFree(memory: *mut c_void) -> *mut c_void;
    fn GetLastError() -> u32;
}
struct Local(*mut c_void);
impl Drop for Local {
    fn drop(&mut self) {
        unsafe {
            LocalFree(self.0);
        }
    }
}
unsafe fn wide(raw: *const u16) -> String {
    assert!(!raw.is_null());
    let mut len = 0;
    while len < 65_536 && unsafe { *raw.add(len) } != 0 {
        len += 1;
    }
    assert!(len < 65_536, "native diagnostic string is not bounded");
    String::from_utf16_lossy(unsafe { std::slice::from_raw_parts(raw, len) })
}
fn descriptor(file: &File) -> Result<(String, String), u32> {
    unsafe {
        let mut owner = ptr::null_mut();
        let mut raw = ptr::null_mut();
        let status = GetSecurityInfo(
            file.as_raw_handle(),
            1,
            1 | 4,
            &mut owner,
            ptr::null_mut(),
            ptr::null_mut(),
            ptr::null_mut(),
            &mut raw,
        );
        if status != 0 {
            return Err(status);
        }
        let memory = Local(raw);
        let mut sid = ptr::null_mut();
        if ConvertSidToStringSidW(owner, &mut sid) == 0 {
            return Err(GetLastError());
        }
        let sid_memory = Local(sid.cast());
        let owner_text = wide(sid);
        drop(sid_memory);
        let mut text = ptr::null_mut();
        if ConvertSecurityDescriptorToStringSecurityDescriptorW(
            memory.0,
            1,
            1 | 4,
            &mut text,
            ptr::null_mut(),
        ) == 0
        {
            return Err(GetLastError());
        }
        let text_memory = Local(text.cast());
        let sddl = wide(text);
        drop(text_memory);
        Ok((owner_text, sddl))
    }
}
fn set(
    file: &File,
    sid: &str,
    user_flags: &str,
    system_flags: &str,
    rights: &str,
) -> Result<(), u32> {
    let text: Vec<u16> =
        format!("D:P(A;{user_flags};{rights};;;{sid})(A;{system_flags};{rights};;;SY)")
            .encode_utf16()
            .chain([0])
            .collect();
    unsafe {
        let mut raw = ptr::null_mut();
        if ConvertStringSecurityDescriptorToSecurityDescriptorW(
            text.as_ptr(),
            1,
            &mut raw,
            ptr::null_mut(),
        ) == 0
        {
            return Err(GetLastError());
        }
        let memory = Local(raw);
        let mut present = 0;
        let mut defaulted = 0;
        let mut acl = ptr::null_mut();
        if GetSecurityDescriptorDacl(memory.0, &mut present, &mut acl, &mut defaulted) == 0 {
            return Err(GetLastError());
        }
        assert_ne!(present, 0);
        assert!(!acl.is_null());
        let status = SetSecurityInfo(
            file.as_raw_handle(),
            1,
            0x8000_0004,
            ptr::null_mut(),
            ptr::null_mut(),
            acl,
            ptr::null_mut(),
        );
        if status != 0 {
            return Err(status);
        }
        Ok(())
    }
}
fn main() {
    use zsys::windows::privacy::{DirectoryInheritance, check_private, protect_created};
    let stamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let path = std::env::temp_dir().join(format!(
        "project-z-acl-probe-{}-{stamp}",
        std::process::id()
    ));
    fs::create_dir(&path).unwrap();
    let original = File::options()
        .access_mode(0x0002_0000 | 0x0004_0000 | 0x0008_0000)
        .custom_flags(0x0200_0000)
        .open(&path)
        .unwrap();
    protect_created(&original, DirectoryInheritance::FilesAndDirectories).unwrap();
    let attributes = File::options()
        .access_mode(0x0002_0000 | 0x80)
        .custom_flags(0x0200_0000)
        .open(&path)
        .unwrap();
    let (sid, _) = descriptor(&original).unwrap();
    for (user_flags, system_flags) in [("", "OICI"), ("OICI", "")] {
        for rights in ["FR", "FW", "0x00000000"] {
            println!(
                "CASE user_flags={user_flags:?} system_flags={system_flags:?} rights={rights}"
            );
            println!(
                "set_security_info={:?}",
                set(&original, &sid, user_flags, system_flags, rights)
            );
            println!(
                "metadata_original={:?}",
                original
                    .metadata()
                    .map(|m| m.is_dir())
                    .map_err(|e| e.raw_os_error())
            );
            println!(
                "metadata_attributes={:?}",
                attributes
                    .metadata()
                    .map(|m| m.is_dir())
                    .map_err(|e| e.raw_os_error())
            );
            println!("stored_descriptor={:?}", descriptor(&original));
            println!("check_original={:?}", check_private(&original));
            println!("check_attributes={:?}", check_private(&attributes));
            // Restore this owned fixture before the next case and before cleanup.
            set(&original, &sid, "OICI", "OICI", "FA").unwrap();
        }
    }
    drop(attributes);
    drop(original);
    fs::remove_dir(&path).unwrap();
}
