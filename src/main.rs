use std::{env,fs,io::Write,path::{Path,PathBuf},process::Command,time::{SystemTime,UNIX_EPOCH}};
fn home()->Result<PathBuf,String>{env::var_os("HOME").map(PathBuf::from).ok_or("HOME niedostępne".into())}
fn base()->Result<PathBuf,String>{
 let root=env::var_os("XDG_STATE_HOME")
  .filter(|p| !p.is_empty())
  .map(PathBuf::from)
  .unwrap_or(home()?.join(".local/state"));
 Ok(root.join("xarch-theme-studio/backups"))
}
fn stamp()->String{SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_nanos().to_string()}
fn icon_root(t:&str)->Result<PathBuf,String>{if t.is_empty() || t.len()>91 || !t.chars().all(|c|c.is_ascii_alphanumeric() || "._+-".contains(c)) || t=="." || t==".." {return Err("Niepoprawna nazwa motywu".into())}let h=home()?;for p in [h.join(".local/share/icons").join(t),h.join(".icons").join(t),PathBuf::from("/usr/share/icons").join(t)]{if p.join("index.theme").is_file(){return Ok(p)}}Err(format!("Brak motywu: {t}"))}
fn active()->Result<String,String>{let p=home()?.join(".config/kdeglobals");let s=fs::read_to_string(p).unwrap_or_default();let mut section=false;for l in s.lines(){let l=l.trim();if l.starts_with('['){section=l=="[Icons]";}else if section{if let Some(x)=l.strip_prefix("Theme="){return Ok(x.trim().to_string())}}}Ok("X-ARCH-Paranormal-Violet".into())}
fn write_key(old:&str,group:&str,key:&str,value:&str)->String{let mut lines=Vec::new();let mut inside=false;let mut seen_group=false;let mut inserted=false;for l in old.lines(){if l.trim().starts_with('[')&&l.trim().ends_with(']'){if inside&&!inserted{lines.push(format!("{key}={value}"));inserted=true;}inside=l.trim()==format!("[{group}]");if inside{seen_group=true;}lines.push(l.to_string());}else if inside&&l.split_once('=').is_some_and(|(k,_)|k.trim()==key){if !inserted{lines.push(format!("{key}={value}"));inserted=true;}}else{lines.push(l.to_string());}}if inside&&!inserted{lines.push(format!("{key}={value}"));}if !seen_group{lines.push(format!("[{group}]"));lines.push(format!("{key}={value}"));}format!("{}\n",lines.join("\n"))}
fn safe_write(p:&Path,s:&str)->Result<(),String>{let tmp=p.with_extension(format!("xarch-{}",stamp()));fs::write(&tmp,s).map_err(|e|e.to_string())?;fs::rename(&tmp,p).map_err(|e|e.to_string())}
fn backup_file(p:&Path)->Result<Option<PathBuf>,String>{if !p.exists(){return Ok(None)}let b=base()?.join("originals");fs::create_dir_all(&b).map_err(|e|e.to_string())?;let dest=b.join(format!("{}-{}",stamp(),p.file_name().unwrap_or_default().to_string_lossy()));fs::copy(p,&dest).map_err(|e|e.to_string())?;Ok(Some(dest))}
fn set_theme(t:&str)->Result<(),String>{icon_root(t)?;let p=home()?.join(".config/kdeglobals");backup_file(&p)?;let old=fs::read_to_string(&p).unwrap_or_default();{
let content=write_key(&old,"Icons","Theme",t);
let mut file=fs::OpenOptions::new()
    .write(true)
    .open(&p)
    .map_err(|e|e.to_string())?;
use std::io::Write;
file.write_all(content.as_bytes()).map_err(|e|e.to_string())?;
file.set_len(content.len() as u64).map_err(|e|e.to_string())?;
file.sync_all().map_err(|e|e.to_string())?;
}println!("Aktywny motyw: {t}. Otwórz ponownie Dolphina.");Ok(())}
fn icon_name(n:&str)->Result<(),String>{if n.is_empty()||!n.chars().all(|c|c.is_ascii_alphanumeric()||c=='-'||c=='_'){return Err("Niepoprawna nazwa ikony".into())}Ok(())}
fn set_folder(p:&Path,t:&str,n:&str,pin:bool)->Result<(),String>{if !p.is_dir()||p.is_symlink(){return Err("Folder nie istnieje lub jest dowiązaniem".into())}icon_name(n)?;let file=icon_root(t)?.join("scalable/places").join(format!("{n}.svg"));if !file.is_file(){return Err(format!("Nie ma ikony {} w motywie {t}",n))}let cfg=p.join(".directory");if cfg.is_symlink(){return Err(".directory jest dowiązaniem — pominięto".into())}backup_file(&cfg)?;let old=fs::read_to_string(&cfg).unwrap_or_default();let value=if pin{file.to_string_lossy().into_owned()}else{n.to_string()};safe_write(&cfg,&write_key(&old,"Desktop Entry","Icon",&value))?;println!("Ustawiono: {} → {}",p.display(),value);Ok(())}
fn pin_file(folder:&Path,theme:&str,icon:&Path)->Result<(),String>{
 if !folder.is_dir()||folder.is_symlink(){return Err("Folder nie istnieje lub jest dowiązaniem".into())}
 let root=fs::canonicalize(icon_root(theme)?).map_err(|e|e.to_string())?;
 let file=fs::canonicalize(icon).map_err(|e|e.to_string())?;
 if !file.starts_with(&root)||!file.is_file()||!matches!(file.extension().and_then(|x|x.to_str()),Some("svg"|"png"|"xpm")){return Err("Ikona spoza wybranego motywu".into())}
 let cfg=folder.join(".directory");if cfg.is_symlink(){return Err(".directory jest dowiązaniem".into())}
 backup_file(&cfg)?;let old=fs::read_to_string(&cfg).unwrap_or_default();
 safe_write(&cfg,&write_key(&old,"Desktop Entry","Icon",&file.to_string_lossy()))?;
 println!("Przypięto ikonę: {}",file.display());Ok(())
}
fn excluded(n:&str)->bool{matches!(n,"target"|"node_modules"|".git"|".cache"|"venv"|".venv"|"__pycache__"|".tox"|"dist"|"build"|".next"|"vendor"|".idea"|".vscode")||n.starts_with('.')}
fn collect(root:&Path,all:&mut Vec<PathBuf>,depth:usize)->Result<(),String>{if depth>12||all.len()>10000{return Err("Limit bezpieczeństwa skanowania".into())}if root.is_symlink(){return Ok(())}for e in fs::read_dir(root).map_err(|e|e.to_string())?{let e=e.map_err(|e|e.to_string())?;let path=e.path();let ty=e.file_type().map_err(|e|e.to_string())?;if !ty.is_dir()||ty.is_symlink(){continue}let n=e.file_name().to_string_lossy().to_string();if excluded(&n){continue}if !path.join(".directory").exists(){all.push(path.clone());}collect(&path,all,depth+1)?;}Ok(())}
fn repair(root:&Path,apply:bool)->Result<(),String>{if !root.is_dir()||root.is_symlink(){return Err("Niepoprawny katalog".into())}let theme=active()?;icon_root(&theme)?.join("scalable/places/folder.svg").is_file().then_some(()).ok_or("Brak folder.svg w aktywnym motywie")?;let mut dirs=Vec::new();collect(root,&mut dirs,0)?;println!("Folder: {}\nAktywny motyw: {theme}\nKatalogi do przypisania: {}",root.display(),dirs.len());if !apply{println!("PODGLĄD. Aby zapisać, dodaj --apply. Nie zmieniono plików.");return Ok(())}let b=base()?;fs::create_dir_all(&b).map_err(|e|e.to_string())?;let manifest=b.join(format!("repair-{}.txt",stamp()));let mut log=fs::OpenOptions::new().write(true).create_new(true).open(&manifest).map_err(|e|e.to_string())?;let mut count=0;for dir in dirs{let cfg=dir.join(".directory");if cfg.exists(){continue}let content="[Desktop Entry]\nIcon=folder\n";match fs::OpenOptions::new().write(true).create_new(true).open(&cfg){Ok(mut f)=>{f.write_all(content.as_bytes()).map_err(|e|e.to_string())?;writeln!(log,"{}",cfg.display()).map_err(|e|e.to_string())?;count+=1},Err(e)=>eprintln!("Pominięto {}: {e}",cfg.display())}}println!("Dodano: {count}\nCofanie: {}",manifest.display());Ok(())}
fn undo(manifest:&Path)->Result<(),String>{let b=fs::canonicalize(base()?).map_err(|e|e.to_string())?;let m=fs::canonicalize(manifest).map_err(|e|e.to_string())?;if !m.starts_with(&b)||!m.file_name().unwrap_or_default().to_string_lossy().starts_with("repair-"){return Err("Odmowa: manifest spoza katalogu kopii".into())}let data=fs::read_to_string(&m).map_err(|e|e.to_string())?;let mut n=0;for line in data.lines(){let p=Path::new(line);if p.file_name().is_none_or(|v|v!=".directory")||p.is_symlink(){continue}if fs::read_to_string(p).ok().as_deref()==Some("[Desktop Entry]\nIcon=folder\n"){fs::remove_file(p).map_err(|e|e.to_string())?;n+=1;}}println!("Cofnięto {n} niezmienionych przypisań. Zmodyfikowane pliki zachowano.");Ok(())}
fn dialog(args:&[&str])->Result<Option<String>,String>{let out=Command::new("zenity").args(args).output().map_err(|e|format!("Zenity niedostępne: {e}"))?;if !out.status.success(){return Ok(None)}Ok(Some(String::from_utf8_lossy(&out.stdout).trim().to_string()))}
fn gui()->Result<(),String>{if Command::new("zenity").arg("--version").output().is_err(){return Err("GUI wymaga Zenity. Zainstaluj: sudo pacman -S zenity".into())}loop{let choice=dialog(&["--list","--title=X-ARCH Theme Studio 0.5.0-beta","--width=720","--height=450","--column=Akcja","Zmień motyw globalny","Kolor pojedynczego folderu","Przywróć kolor globalny folderu","Napraw podfoldery — podgląd","Napraw podfoldery — zastosuj","Zakończ"])?;match choice.as_deref(){Some("Zmień motyw globalny")=>{let t=dialog(&["--list","--title=Motyw globalny","--column=Motyw","X-ARCH-FBI-Red","X-ARCH-X-Green","X-ARCH-Lab-Blue","X-ARCH-Steel-Silver","X-ARCH-Archive-Gold","X-ARCH-Paranormal-Violet","X-ARCH-Classified-Archive","X-ARCH-FBI-RedWhite"])?;if let Some(t)=t{set_theme(&t)?;}},Some("Kolor pojedynczego folderu")|Some("Przywróć kolor globalny folderu")=>{let pin=choice.as_deref()==Some("Kolor pojedynczego folderu");let folder=dialog(&["--file-selection","--directory","--title=Wybierz folder"])?;if let Some(folder)=folder{if pin{let t=dialog(&["--list","--title=Kolor folderu","--column=Motyw","X-ARCH-FBI-Red","X-ARCH-X-Green","X-ARCH-Lab-Blue","X-ARCH-Steel-Silver","X-ARCH-Archive-Gold","X-ARCH-Paranormal-Violet","X-ARCH-Classified-Archive","X-ARCH-FBI-RedWhite"])?;if let Some(t)=t{set_folder(Path::new(&folder),&t,"folder",true)?;}}else{set_folder(Path::new(&folder),&active()?,"folder",false)?;}}},Some("Napraw podfoldery — podgląd")|Some("Napraw podfoldery — zastosuj")=>{let apply=choice.as_deref()==Some("Napraw podfoldery — zastosuj");let folder=dialog(&["--file-selection","--directory","--title=Wybierz katalog główny"])?;if let Some(folder)=folder{if apply{let ok=dialog(&["--question","--title=Potwierdzenie","--text=Program doda pliki .directory w podfolderach. Kontynuować?"])?;if ok.is_none(){continue}}repair(Path::new(&folder),apply)?;let _=dialog(&["--info","--text=Operacja zakończona. Szczegóły w terminalu."]);}},_=>break}}Ok(())}
fn help(){println!("X-ARCH Theme Studio 0.5.0-beta\n  gui\n  list\n  theme NAZWA-MOTYWU\n  folder SCIEZKA NAZWA-IKONY [--theme NAZWA] [--pin]\n  repair SCIEZKA [--apply]\n  undo PLIK-MANIFESTU\n\nDomyślnie folder używa nazwy ikony i zmienia kolor z motywem. --pin przypina wybrany kolor.\nGUI wykorzystuje Zenity (GTK), a silnik jest w Rust.")}

fn list_installed()->Result<(),String>{
    let h=home()?;
    let roots=[
        h.join(".local/share/icons"),
        h.join(".icons"),
        PathBuf::from("/usr/share/icons")
    ];
    let mut found=std::collections::BTreeSet::new();

    for root in roots {
        if !root.is_dir(){continue}
        let entries=match fs::read_dir(&root){
            Ok(e)=>e,
            Err(e)=>{
                eprintln!("Pominieto {}: {e}",root.display());
                continue
            }
        };
        for entry in entries.flatten(){
            let path=entry.path();
            if path.is_dir() && path.join("index.theme").is_file(){
                if let Some(name)=path.file_name().and_then(|n|n.to_str()){
                    found.insert(name.to_string());
                }
            }
        }
    }
    for name in found {
        println!("{name}");
    }
    Ok(())
}

fn run()->Result<(),String>{let args:Vec<String>=env::args().collect();match args.get(1).map(String::as_str){Some("gui")=>{let exe=env::current_exe().map_err(|e|e.to_string())?;
let exe_dir=exe.parent().ok_or("Brak katalogu programu")?;
let mut candidates=Vec::new();
if let Some(root)=exe_dir.parent().and_then(|p|p.parent()){
    candidates.push(root.join("gui/studio.py"));
}
if let Some(data)=env::var_os("XDG_DATA_HOME"){
    candidates.push(PathBuf::from(data).join("xarch-theme-studio/gui/studio.py"));
}
candidates.push(home()?.join(".local/share/xarch-theme-studio/gui/studio.py"));
candidates.push(PathBuf::from("/usr/local/share/xarch-theme-studio/gui/studio.py"));
candidates.push(PathBuf::from("/usr/share/xarch-theme-studio/gui/studio.py"));
let script=candidates.into_iter().find(|p|p.is_file()).ok_or("Nie znaleziono gui/studio.py")?;if script.is_file(){let status=Command::new("python3").arg(script).status().map_err(|e|e.to_string())?;if status.success(){Ok(())}else{Err(format!("GUI GTK4 zakończyło się kodem: {status}"))}}else{gui()}},Some("theme-info")=>theme_info(args.get(2).ok_or("Podaj motyw")?),Some("list-icons")=>list_icons(args.get(2).ok_or("Podaj motyw")?),Some("list-installed")=>list_installed(),Some("list")=>list_installed(),Some("theme")=>set_theme(args.get(2).ok_or("Podaj motyw")?),Some("folder")=>{let p=Path::new(args.get(2).ok_or("Podaj folder")?);let n=args.get(3).ok_or("Podaj nazwę ikony")?;let t=if let Some(i)=args.iter().position(|x|x=="--theme"){args.get(i+1).ok_or("Brak motywu po --theme")?.clone()}else{active()?};set_folder(p,&t,n,args.iter().any(|x|x=="--pin"))},Some("pin-file")=>pin_file(Path::new(args.get(2).ok_or("Podaj folder")?),args.get(3).ok_or("Podaj motyw")?,Path::new(args.get(4).ok_or("Podaj plik ikony")?)),Some("repair")=>repair(Path::new(args.get(2).ok_or("Podaj katalog")?),args.iter().any(|x|x=="--apply")),Some("undo")=>undo(Path::new(args.get(2).ok_or("Podaj manifest")?)),Some("help")|Some("--help")|None=>{help();Ok(())},_=>Err("Nieznane polecenie. Użyj --help".into())}}

fn list_icons(theme:&str)->Result<(),String>{
 use std::collections::HashMap;
 let root=icon_root(theme)?;
 let mut files=Vec::<PathBuf>::new();
 let mut stack=vec![root];
 while let Some(dir)=stack.pop(){
  for entry in fs::read_dir(&dir).map_err(|e|e.to_string())?{
   let entry=entry.map_err(|e|e.to_string())?;
   let ty=entry.file_type().map_err(|e|e.to_string())?;
   if ty.is_symlink(){continue}
   let path=entry.path();
   if ty.is_dir(){stack.push(path)}
   else if ty.is_file(){
    let ext=path.extension().and_then(|x|x.to_str()).unwrap_or("");
    if ["svg","png","xpm"].contains(&ext){files.push(path)}
   }
  }
 }
 files.sort_by(|a,b|{
  fn rank(p:&Path)->(u8,u8,u8,String){
   let name=p.file_stem().unwrap_or_default().to_string_lossy().to_lowercase();
   let s=p.to_string_lossy().to_lowercase();
   (
    if name=="folder"{0}else if name.starts_with("folder-"){1}else{2},
    if s.contains("/places/"){0}else if s.contains("/apps/"){1}else{2},
    if s.contains("/scalable/"){0}else if s.contains("/128x128/"){1}else if s.contains("/64x64/"){2}else{3},
    name
   )
  }
  rank(a).cmp(&rank(b)).then_with(||a.cmp(b))
 });
 let mut seen=HashMap::new();
 for path in files{
  let stem=path.file_stem().unwrap_or_default().to_string_lossy().to_string();
  if seen.insert(stem.clone(),()).is_none(){
   println!("{}",path.display());
  }
 }
 Ok(())
}

fn main(){if let Err(e)=run(){eprintln!("BŁĄD: {e}");std::process::exit(1)}}


fn theme_info(theme:&str)->Result<(),String>{
    let root=icon_root(theme)?;
    let content=std::fs::read_to_string(root.join("index.theme"))
        .map_err(|e|format!("Nie mozna odczytac index.theme: {e}"))?;
    let mut section=String::new();
    let mut name=String::new();
    let mut comment=String::new();
    let mut inherits=String::new();
    let mut directories=String::new();
    for line in content.lines(){
        let line=line.trim().trim_start_matches('\u{feff}');
        if line.is_empty() || line.starts_with('#') || line.starts_with(';'){continue;}
        if line.starts_with('[') && line.ends_with(']'){
            section=line[1..line.len()-1].to_string();
            continue;
        }
        if section!="Icon Theme"{continue;}
        if let Some((key,value))=line.split_once('='){
            match key.trim(){
                "Name"=>name=value.trim().to_string(),
                "Comment"=>comment=value.trim().to_string(),
                "Inherits"=>inherits=value.trim().to_string(),
                "Directories"=>directories=value.trim().to_string(),
                _=>{}
            }
        }
    }
    if name.is_empty(){name=theme.to_string();}
    println!("Theme={theme}");
    println!("Name={name}");
    println!("Comment={comment}");
    println!("Inherits={inherits}");
    println!("Directories={directories}");
    Ok(())
}

