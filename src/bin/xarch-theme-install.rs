// X-ARCH Stage 5B.2 archive support; isolated CLI, no GTK or global theme changes.
use std::{env,ffi::{CString,OsStr},fs,io::{self,Read},os::unix::ffi::OsStrExt,path::{Path,PathBuf}};
use std::os::raw::{c_char,c_int};
extern "C" {fn renameat2(a:c_int,b:*const c_char,c:c_int,d:*const c_char,e:u32)->c_int;}
const AT_FDCWD:c_int=-100;const RENAME_NOREPLACE:u32=1;
const LIMIT:u64=700*1024*1024;const COUNT:usize=25000;
fn valid_name(s:&OsStr)->bool{let b=s.as_bytes();!b.is_empty()&&b.len()<=91&&b[0].is_ascii_alphanumeric()&&b.iter().all(|c|c.is_ascii_alphanumeric()||b"._+-".contains(c))}
fn safe_relative(s:&Path)->bool{!s.as_os_str().is_empty()&&s.components().all(|c|matches!(c,std::path::Component::Normal(_)))}
fn validate_tree(p:&Path,count:&mut usize,size:&mut u64,depth:usize)->Result<usize,String>{
 if depth>24{return Err("Za duża głębokość".into())}let mut icons=0;
 for e in fs::read_dir(p).map_err(|e|e.to_string())?{let e=e.map_err(|e|e.to_string())?;*count+=1;if *count>COUNT{return Err("Za dużo elementów".into())}
 let t=e.file_type().map_err(|e|e.to_string())?;if t.is_symlink()||!(t.is_file()||t.is_dir()){return Err("Niedozwolony typ pliku".into())}
 if t.is_dir(){icons+=validate_tree(&e.path(),count,size,depth+1)?}else{*size=size.checked_add(e.metadata().map_err(|e|e.to_string())?.len()).ok_or("Przekroczono limit")?;if *size>LIMIT{return Err("Limit 700 MiB".into())}
 if let Some(ext)=e.path().extension(){if ["svg","png","xpm"].iter().any(|x|ext.to_string_lossy().eq_ignore_ascii_case(x)){icons+=1}}}}
 Ok(icons)
}
fn copy_tree(src:&Path,dst:&Path)->Result<(),String>{fs::create_dir(dst).map_err(|e|e.to_string())?;for e in fs::read_dir(src).map_err(|e|e.to_string())?{let e=e.map_err(|e|e.to_string())?;let t=e.file_type().map_err(|e|e.to_string())?;if t.is_symlink()||!(t.is_file()||t.is_dir()){return Err("Niedozwolony element źródła".into())}let to=dst.join(e.file_name());if t.is_dir(){copy_tree(&e.path(),&to)?}else{fs::copy(e.path(),to).map_err(|e|e.to_string())?;}}Ok(())}
fn write_member<R:Read>(mut input:R,dst:&Path,expected:u64,total:&mut u64)->Result<(),String>{
 *total=total.checked_add(expected).ok_or("Limit rozmiaru")?;if *total>LIMIT{return Err("Limit 700 MiB".into())}
 let mut out=fs::OpenOptions::new().write(true).create_new(true).open(dst).map_err(|e|e.to_string())?;
 let n=io::copy(&mut input.by_ref().take(expected.saturating_add(1)),&mut out).map_err(|e|e.to_string())?;
 if n!=expected{return Err("Niezgodny rozmiar elementu archiwum".into())}Ok(())
}
fn archive_path(root:&Path,rel:&Path,seen:&mut std::collections::HashSet<PathBuf>)->Result<PathBuf,String>{
 if !safe_relative(rel){return Err("Niebezpieczna ścieżka archiwum".into())}
 let path=root.join(rel);if !seen.insert(rel.to_path_buf()){return Err("Powtórzony element archiwum".into())}Ok(path)
}
fn unpack_zip(src:&Path,root:&Path)->Result<(),String>{
 let f=fs::File::open(src).map_err(|e|e.to_string())?;let mut zip=zip::ZipArchive::new(f).map_err(|e|e.to_string())?;
 if zip.len()>COUNT{return Err("Za dużo elementów".into())}let mut seen=std::collections::HashSet::new();let mut total=0;
 for i in 0..zip.len(){let mut e=zip.by_index(i).map_err(|e|e.to_string())?;
 if let Some(mode)=e.unix_mode(){let kind=mode&0o170000;if kind!=0&&kind!=0o100000&&kind!=0o040000{return Err("Niedozwolony typ ZIP".into())}}
 let rel=Path::new(e.name());let dest=archive_path(root,rel,&mut seen)?;
 if e.is_dir(){fs::create_dir_all(&dest).map_err(|e|e.to_string())?}else{if let Some(p)=dest.parent(){fs::create_dir_all(p).map_err(|e|e.to_string())?}let size=e.size();write_member(&mut e,&dest,size,&mut total)?;}}
 Ok(())
}
fn unpack_tar<R:Read>(reader:R,root:&Path)->Result<(),String>{
 let mut ar=tar::Archive::new(reader);let mut seen=std::collections::HashSet::new();let mut total=0;let mut count=0;
 for entry in ar.entries().map_err(|e|e.to_string())?{let mut e=entry.map_err(|e|e.to_string())?;count+=1;if count>COUNT{return Err("Za dużo elementów".into())}
 let kind=e.header().entry_type();if !(kind.is_file()||kind.is_dir()){return Err("Niedozwolony typ TAR".into())}
 let rel=e.path().map_err(|e|e.to_string())?.into_owned();let dest=archive_path(root,&rel,&mut seen)?;
 if kind.is_dir(){fs::create_dir_all(&dest).map_err(|e|e.to_string())?}else{if let Some(p)=dest.parent(){fs::create_dir_all(p).map_err(|e|e.to_string())?}{let size=e.header().size().map_err(|e|e.to_string())?;write_member(&mut e,&dest,size,&mut total)?};}}
 Ok(())
}
fn extract(src:&Path,root:&Path)->Result<(),String>{
 let name=src.file_name().unwrap_or_default().to_string_lossy().to_lowercase();
 let f=fs::File::open(src).map_err(|e|e.to_string())?;
 if name.ends_with(".zip"){unpack_zip(src,root)}
 else if name.ends_with(".tar"){unpack_tar(f,root)}
 else if name.ends_with(".tar.gz")||name.ends_with(".tgz"){unpack_tar(flate2::read::GzDecoder::new(f),root)}
 else if name.ends_with(".tar.xz"){unpack_tar(xz2::read::XzDecoder::new(f),root)}
 else{Err("Format nieobsługiwany: ZIP, TAR, TAR.GZ, TAR.XZ".into())}
}
fn find_themes(root:&Path,depth:usize,out:&mut Vec<PathBuf>)->Result<(),String>{
 if depth>12{return Err("Zbyt głęboko zagnieżdżone motywy".into())}
 if root.join("index.theme").is_file(){let name=root.file_name().ok_or("Brak nazwy motywu")?;if !valid_name(name){return Err("Niepoprawna nazwa motywu".into())}out.push(root.to_path_buf());return Ok(())}
 for e in fs::read_dir(root).map_err(|e|e.to_string())?{let e=e.map_err(|e|e.to_string())?;if e.file_type().map_err(|e|e.to_string())?.is_dir(){find_themes(&e.path(),depth+1,out)?}}Ok(())
}
fn install(src:&Path,dest:&Path)->Result<Vec<String>,String>{
 if !dest.is_dir()||dest.is_symlink(){return Err("Cel musi być istniejącym zwykłym katalogiem".into())}
 if !src.exists()||src.is_symlink(){return Err("Niepoprawne źródło".into())}
 let temp=tempfile::Builder::new().prefix(".xarch-import-").tempdir_in(dest).map_err(|e|e.to_string())?;
 let root=temp.path().join("extracted");fs::create_dir(&root).map_err(|e|e.to_string())?;
 if src.is_dir(){let name=src.file_name().ok_or("Brak nazwy źródła")?;if !valid_name(name){return Err("Niepoprawna nazwa".into())}copy_tree(src,&root.join(name))?}else{extract(src,&root)?}
 let mut count=0;let mut total=0;validate_tree(&root,&mut count,&mut total,0)?;
 let mut themes=Vec::new();find_themes(&root,0,&mut themes)?;if themes.is_empty(){return Err("Brak index.theme".into())}
 let mut names=std::collections::HashSet::new();for p in &themes{let name=p.file_name().unwrap();if !names.insert(name.to_os_string()){return Err("Duplikat nazwy motywu".into())}if fs::symlink_metadata(dest.join(name)).is_ok(){return Err("Motyw już istnieje — odmowa nadpisania".into())}
 let mut n=0;let mut s=0;if validate_tree(p,&mut n,&mut s,0)?==0{return Err("Motyw nie zawiera ikon".into())}}
 // Staging on the same filesystem. Atomic NOREPLACE for each theme; rollback only newly installed directories.
 let mut installed:Vec<PathBuf>=Vec::new();let mut result=Vec::new();
 for p in &themes{let name=p.file_name().unwrap();let target=dest.join(name);
 let old=CString::new(p.as_os_str().as_bytes()).map_err(|e|e.to_string())?;let new=CString::new(target.as_os_str().as_bytes()).map_err(|e|e.to_string())?;
 let rc=unsafe{renameat2(AT_FDCWD,old.as_ptr(),AT_FDCWD,new.as_ptr(),RENAME_NOREPLACE)};
 if rc!=0{
    let rename_error=io::Error::last_os_error();
    let mut rollback_errors=Vec::new();
    for path in installed.iter().rev(){
        if let Err(e)=fs::remove_dir_all(path){
            rollback_errors.push(format!("{}: {}",path.display(),e));
        }
    }
    if rollback_errors.is_empty(){
        return Err(format!("Bezpieczne przeniesienie odrzucone: {rename_error}; rollback zakończony"));
    }
    return Err(format!(
        "Bezpieczne przeniesienie odrzucone: {rename_error}; UWAGA: rollback niekompletny: {}",
        rollback_errors.join("; ")
    ));
}
 installed.push(target);result.push(name.to_string_lossy().into_owned());}
 Ok(result)
}
fn main(){let a:Vec<_>=env::args_os().collect();if a.len()!=3{eprintln!("Użycie: xarch-theme-install ARCHIWUM_LUB_KATALOG ISTNIEJĄCY_KATALOG_DOCELOWY");std::process::exit(2)}match install(Path::new(&a[1]),Path::new(&a[2])){Ok(names)=>for n in names{println!("INSTALLED: {n}")},Err(e)=>{eprintln!("ERROR: {e}");std::process::exit(1)}}}
#[cfg(test)]mod tests{use super::*;#[test]fn names(){assert!(valid_name(OsStr::new("X-ARCH-Test")));assert!(!valid_name(OsStr::new("..")));assert!(!valid_name(OsStr::new("bad/name")));}#[test]fn paths(){assert!(!safe_relative(Path::new("../evil")));assert!(!safe_relative(Path::new("/tmp/evil")));assert!(safe_relative(Path::new("theme/scalable/folder.svg")));}}
