#!/usr/bin/env python3
"""X-ARCH Theme Studio 2.0 — illustrated cinematic bilingual visual icon-theme manager."""
import configparser
import pathlib
import re
import subprocess
import sys
from functools import lru_cache
from theme_import import install as install_theme
from bundled_themes import install_missing
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Gio, GLib

HOME = pathlib.Path.home()
ROOT = pathlib.Path(__file__).resolve().parent.parent
def find_backend():
    import os

    override = os.environ.get("XARCH_BACKEND")
    if override:
        candidate = pathlib.Path(override).expanduser()
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(f"XARCH_BACKEND not found: {candidate}")

    if (ROOT / "Cargo.toml").is_file():
        candidates = [
            ROOT / "target/release/xarch-theme-studio",
            ROOT / "target/debug/xarch-theme-studio",
        ]
    else:
        candidates = [
            HOME / ".local/bin/xarch-theme-studio",
            pathlib.Path("/usr/local/bin/xarch-theme-studio"),
            pathlib.Path("/usr/bin/xarch-theme-studio"),
        ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError("X-ARCH Rust backend not found")

BIN = find_backend()

ICONS = HOME / '.local/share/icons'
ASSETS = ROOT / 'gui/assets'
PREFS = HOME / '.config/xarch-theme-studio/preferences.ini'
BUILTINS = [
 ('Alien Crimson','X-ARCH-Alien-Crimson','#f15b72'),('Alien Arctic','X-ARCH-Alien-Arctic','#67d7fb'),
 ('Alien Violet','X-ARCH-Alien-Violet','#b993ff'),('Alien Amber','X-ARCH-Alien-Amber','#ffbd65'),
 ('Alien Toxic','X-ARCH-Alien-Toxic','#a2e87d'),('Alien Contact','X-ARCH-Alien-Contact','#55d9cc'),
 ('FBI Red / White','X-ARCH-FBI-RedWhite','#ef6478'),('Classified Archive','X-ARCH-Classified-Archive','#cb956d'),
 ('FBI Red','X-ARCH-FBI-Red','#e94c60'),('X Green','X-ARCH-X-Green','#70d3a2'),
 ('Lab Blue','X-ARCH-Lab-Blue','#7eb8ed'),('Steel Silver','X-ARCH-Steel-Silver','#b7c7d6'),
 ('Archive Gold','X-ARCH-Archive-Gold','#eac57c'),('Paranormal Violet','X-ARCH-Paranormal-Violet','#b79aef')]
SYMBOLS = ['folder','folder-documents','folder-downloads','folder-pictures','folder-music','folder-videos','folder-projects','folder-archive','folder-finance','folder-private','folder-backup','folder-fbi']
TEXT = {
 'Dashboard': 'Panel główny','Theme gallery':'Galeria motywów','Import themes':'Import motywów',
 'Folder icons':'Ikony folderów','Restore folder':'Przywróć folder','Repair folders':'Napraw foldery','About':'O programie',
 'COMMAND CENTER':'CENTRUM DOWODZENIA','Icon themes, beautifully organized.':'Motywy ikon w pięknej oprawie.',
 'Browse every installed icon pack, preview real icons, and personalize your desktop.':'Przeglądaj wszystkie zainstalowane motywy, podglądaj prawdziwe ikony i personalizuj pulpit.',
 'ACTIVE ICON THEME':'AKTYWNY MOTYW IKON','INSTALLED COLLECTIONS':'ZAINSTALOWANE KOLEKCJE',
 'ALIEN COLLECTION':'KOLEKCJA ALIEN','FBI ARCHIVE':'ARCHIWUM FBI','DOWNLOADED & SYSTEM THEMES':'POBRANE I SYSTEMOWE MOTYWY',
 'Browse collections':'Przeglądaj kolekcje','Install icon pack':'Zainstaluj motyw ikon',
 'Browse all installed themes':'Przeglądaj wszystkie motywy','Gallery':'Galeria',
 'Your installed themes, including downloads.':'Twoje zainstalowane motywy, także pobrane.',
 'Search themes…':'Szukaj motywów…','ALL THEMES':'WSZYSTKIE MOTYWY','LIVE ICON PREVIEW':'PODGLĄD PRAWDZIWYCH IKON',
 'Apply this theme':'Zastosuj ten motyw','Apply globally?':'Zastosować globalnie?',
 'This changes the desktop icon theme. Pinned folder icons are preserved.':'Zmieni to globalny motyw ikon. Przypięte ikony folderów pozostaną bez zmian.',
 'No icon preview available':'Brak podglądu ikon','icons found':'znalezionych ikon',
 'Import an icon pack':'Importuj motyw ikon','Install ZIP / TAR archive':'Zainstaluj archiwum ZIP / TAR',
 'Install unpacked folder':'Zainstaluj rozpakowany katalog',
 'Installed themes appear automatically in the gallery.':'Zainstalowane motywy automatycznie pojawią się w galerii.',
 'Choose an icon pack downloaded from KDE Store, GNOME-Look or another source.':'Wybierz zestaw ikon pobrany z KDE Store, GNOME-Look lub innego źródła.',
 'Your existing icon themes are backed up before replacement. Import does not activate the theme.':'Istniejące motywy są zabezpieczane przed zastąpieniem. Import nie aktywuje motywu.',
 'Select archive':'Wybierz archiwum','Select directory':'Wybierz katalog','Import selected theme?':'Zaimportować wybrany motyw?',
 'Import complete':'Import zakończony','Open gallery':'Otwórz galerię','Import failed':'Import nieudany',
 'Set a custom icon for one folder':'Ustaw własną ikonę pojedynczego folderu',
 'Select a folder, then choose a theme and icon.':'Wybierz folder, a następnie motyw i ikonę.',
 'Choose folder':'Wybierz folder','Select icon':'Wybierz ikonę','Pin icon':'Przypnij ikonę',
 'Pin this icon?':'Przypiąć tę ikonę?','Restore inherited folder icon':'Przywróć dziedziczoną ikonę folderu',
 'Choose a folder to restore its default icon.':'Wybierz folder, aby przywrócić domyślną ikonę.',
 'Restore this folder?':'Przywrócić ikonę tego folderu?',
 'Preview and repair nested folders':'Podgląd i naprawa podfolderów',
 'Existing .directory files are not overwritten.':'Istniejące pliki .directory nie zostaną nadpisane.',
 'Preview repair':'Podgląd naprawy','Apply repair':'Zastosuj naprawę','Apply repair?':'Zastosować naprawę?',
 'PROJECT DOSSIER':'AKTA PROJEKTU','Designed for Arch Linux and KDE / Hyprland.':'Zaprojektowano dla Arch Linux i KDE / Hyprland.',
 'Language':'Język','English':'English','Polski':'Polski','Ready':'Gotowe','Cancel':'Anuluj','Confirm':'Potwierdź',
 'Error':'Błąd','Operation completed':'Operacja zakończona','Theme installed':'Motyw zainstalowany',
 'Select theme':'Wybierz motyw','Choose an icon pack from the gallery':'Wybierz motyw z galerii',
 'Local icon packs':'Lokalne zestawy ikon','Collections':'Kolekcje','Icons':'Ikony',
 'No matching themes':'Brak pasujących motywów','Refresh library':'Odśwież galerię',
 'Switch to Polish':'Przełącz na polski','Switch to English':'Przełącz na angielski',
 'All icons in this theme':'Wszystkie ikony tego motywu',
 'Choose an installed theme and icon':'Wybierz zainstalowany motyw i ikonę',
 'No icons in this theme':'Brak ikon w tym motywie',
 'Open downloads':'Otwórz pobrane',
}
CSS = '''
/* 2.0 professional red-black finish */
.topbar {background: #101018; padding: 7px 14px; border-bottom:2px solid #d83c59;}
.side {background: #0d0d15; padding:10px 8px; border-right:1px solid #96344c;}
.brand {font-size:18px;font-weight:900;color:#ffffff;}
.nav {background:#171621;border:1px solid #55303f;border-radius:9px;padding:9px 10px;color:#f0dce1;}
.nav-active {background:#762038;border-left:3px solid #ff6179;}
.page {background:#0c0b11;padding:13px 15px 18px;}
.tile {background:#1b1720;border:1px solid #583040;border-radius:12px;padding:8px;}
.tile-active {border:2px solid #ff4c6a;background:#291923;}
.tile-title {font-size:13px;font-weight:800;color:#fff3f5;}
.cover-art {background:#100d13;border-radius:8px;}
.preview-pane {background:#17121c;border:1px solid #7c344b;border-radius:13px;padding:13px;}
.preview-art {background:#100d13;border-radius:9px;}
.apply-button {background:#c32b4c;border:1px solid #ff718b;font-weight:900;}
.iconcell {background:#251b27;border:1px solid #513242;border-radius:9px;padding:5px;}

* {font-family:'Noto Sans','Inter',sans-serif;}
window,.shell,.viewport,.page {background:#09090e;color:#f5f0f0;}
.topbar {background:rgba(8,11,19,0.70);padding:10px 18px;border-bottom:2px solid #dc395e;}
.brand {font-size:16px;font-weight:900;color:#fff8f7;letter-spacing:1.3px;}
.muted {font-size:13px;color:#bcb4bd;}
.micro {font-size:10px;color:#c6adb6;font-weight:800;letter-spacing:1px;}
.accent {font-size:11px;color:#ff667f;font-weight:900;letter-spacing:2px;}
.side {background:#10101b;padding:12px 10px;border-right:2px solid #7b344a;}
.nav {min-height:24px;background:#171a28;border:1px solid #5a3447;color:#e6dce4;border-radius:9px;padding:9px;font-weight:750;}
.nav:hover {background:#2d1c29;color:white;}
.nav-active {background:rgba(103,30,48,0.88);color:#fff;border:1px solid #b34c64;border-left:4px solid #ff5679;}
.page {padding:12px 14px 22px;}
.h1 {font-size:25px;font-weight:900;color:#fff8f7;}
.h2 {font-size:17px;font-weight:850;color:#fff4f2;}
.card {min-width:0;background:#19151f;border:1px solid #47303e;border-radius:17px;padding:18px;}
.card-strong {min-width:0;background:#211822;border:1px solid #855064;border-radius:19px;padding:20px;}
.tile {min-width:0;background:#1b1822;border:1px solid #4a3647;border-radius:14px;padding:12px;}
.tile:hover {background:#33222e;border-color:#f27c93;}
.tile-active {background:#3e2533;border:2px solid #ff6585;}
.primary {background:#ad304d;border:1px solid #ff7592;color:#fff;font-weight:900;border-radius:11px;padding:12px 18px;}
.primary:hover {background:#d43e61;}
.secondary {background:#332431;border:1px solid #6c465b;color:#fff1f4;font-weight:750;border-radius:11px;padding:10px 14px;}
.secondary:hover {background:#493044;}
.pill {background:#31202c;color:#f7afc1;border-radius:9px;padding:8px 12px;font-weight:800;}
.art {background:#160f1a;border:1px solid #765066;border-radius:18px;}
.iconcell {background:#201a24;border:1px solid #4c3546;border-radius:11px;padding:9px;}
.status {background:#110f16;border-top:1px solid #5b3648;padding:11px 23px;color:#cbb7c2;font-size:11px;}
entry {background:#2b202c;color:#fff;border:1px solid #735368;border-radius:11px;padding:12px;}
scrollbar slider {background:#765367;border-radius:8px;}
.picture-frame {min-width:0;background:#130e17;border:1px solid #6a3a50;border-radius:15px;padding:3px;}
.nav-icon {color:#ff6b89;}
.chrome-heading {font-size:10px;color:#e7b6c4;font-weight:800;letter-spacing:2px;}
.header-glass {background:rgba(9,11,22,0.45);border-bottom:2px solid #c93659;}
.sidebar-banner {background:#141523;border:1px solid #7a344c;border-radius:12px;padding:3px;}
.section-rule {background:#d03d5b;min-height:2px;}


.header-compact {background:#100b12; background-image:linear-gradient(90deg,#151019 0%,#180d15 58%,#100b12 100%); border-top:2px solid #c52d4d; border-bottom:2px solid #d43b5b; padding:8px 18px;}
.header-seal {background:#1b1420; border:1px solid #ad3856; border-radius:10px; padding:3px;}
.header-compact .brand {font-size:18px; font-weight:900; color:#fff8f8; letter-spacing:1px;}
.header-compact .micro {font-size:10px; color:#d8a8b4;}

.header-compact {background:rgba(9,7,15,0.25); border-bottom:2px solid #b42d4e; padding:8px 18px;}
.header-compact .brand {color:#ffffff; font-size:18px; font-weight:900;}
.header-compact .micro {color:#f0c6d1;}
.sidebar-banner {border-radius:9px;}
/* Full-width UFO image: remove padding and ghosted background. */
.archive-wide {padding:0; background:#100d15; background-image:none; border-radius:18px;}
.archive-actions {padding:14px 18px 18px; background:#17101b; background-image:none;}

'''

def read_language():
 try:
  p=configparser.ConfigParser();p.read(PREFS);return p.get('ui','language',fallback='en') if p.get('ui','language',fallback='en') in ('en','pl') else 'en'
 except Exception:return 'en'

def theme_root(theme):
 for root in (ICONS, HOME/'.icons', pathlib.Path('/usr/share/icons')):
  p=root/theme
  if (p/'index.theme').is_file():return p
 return ICONS/theme

@lru_cache(maxsize=256)
def icon_paths(theme):
 root=theme_root(theme)
 if not root.is_dir():return ()
 # Support freedesktop icon packs in scalable/, 16x16/, 48x48/, 128x128/ etc.
 files=[]
 for ext in ('*.svg','*.png','*.xpm'):
  files.extend(root.rglob(ext))
 def rank(p):
  name=p.stem.lower();s=str(p).lower()
  return (0 if name=='folder' else 1 if name.startswith('folder-') else 2,
          0 if '/places/' in s else 1 if '/apps/' in s else 2,
          0 if '/scalable/' in s else 1 if '/128x128/' in s else 2 if '/64x64/' in s else 3,
          name)
 files.sort(key=rank)
 unique={}
 for f in files:
  unique.setdefault(f.stem,f)
 return tuple(unique.values())

def preview_icon(theme,name='folder'):
 paths=icon_paths(theme)
 for p in paths:
  if p.stem==name:return p
 return paths[0] if paths else None

def all_themes():
 base={x[1]:x for x in BUILTINS if (ICONS/x[1]/'index.theme').is_file()}
 for root in (ICONS,HOME/'.icons',pathlib.Path('/usr/share/icons')):
  if not root.is_dir():continue
  try:folders=sorted(root.iterdir())
  except OSError:continue
  for p in folders:
   if p.is_dir() and (p/'index.theme').is_file() and p.name not in base:
    base[p.name]=(p.name.replace('-',' '),p.name,'#76cbd6')
 return list(base.values())

class Studio(Gtk.Application):
 def __init__(self):
  super().__init__(application_id=('io.github.runningwithrottweilers.XArchThemeStudio' if pathlib.Path('/.flatpak-info').exists() else 'online.xarch.ThemeStudio'),flags=Gio.ApplicationFlags.FLAGS_NONE)
  self.lang=read_language();self.page='dashboard';self.selected=None;self.cards={};self.navs={}

  for source in (
   ROOT / "bundled-themes",
   ROOT / "share/xarch-theme-studio/bundled-themes",
   pathlib.Path("/app/share/xarch-theme-studio/bundled-themes"),
   HOME / ".local/share/xarch-theme-studio/bundled-themes",
  ):
   if source.is_dir():
    install_missing(source, ICONS)
    break

 def t(self,key):return TEXT.get(key,key) if self.lang=='pl' else key
 def label(self,parent,value,style=None,wrap=True):
  w=Gtk.Label(label=str(value),xalign=0);w.set_wrap(wrap)
  if style:w.add_css_class(style)
  parent.append(w);return w
 def pic(self,path,size):
  if path is None or not pathlib.Path(path).is_file():
   x=Gtk.Label(label='◈');x.set_size_request(size,size);return x
  x=Gtk.Picture.new_for_filename(str(path));x.set_content_fit(Gtk.ContentFit.CONTAIN);x.set_size_request(size,size);return x
 def art_image(self,path,width=900,height=250):
   """Real packaged artwork, rendered with a bounded aspect ratio."""
   path=pathlib.Path(path)
   if not path.is_file():
    return self.pic(None,96)
   frame=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
   frame.add_css_class('picture-frame')
   frame.set_size_request(-1,height);frame.set_hexpand(True)
   picture=Gtk.Picture.new_for_filename(str(path))
   picture.set_content_fit(Gtk.ContentFit.COVER)
   picture.set_can_shrink(True)
   picture.set_size_request(-1,height);picture.set_hexpand(True)
   frame.append(picture)
   return frame
 def col(self,parent,spacing=12):
  x=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=spacing);parent.append(x);return x
 def row(self,parent,spacing=12):
  x=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=spacing);parent.append(x);return x
 def card(self,parent,style='card'):
  x=self.col(parent,12);x.add_css_class(style);return x
 def btn(self,parent,text,fn,style='secondary'):
  b=Gtk.Button(label=self.t(text));b.add_css_class(style);b.connect('clicked',lambda _:fn());parent.append(b);return b
 def do_activate(self):
  self.win=Gtk.ApplicationWindow(application=self,title='X-ARCH Theme Studio 2.6 — Cinematic Collections',default_width=1320,default_height=800)
  css=Gtk.CssProvider();css.load_from_data(CSS.encode());Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
  self.shell=Gtk.Box(orientation=Gtk.Orientation.VERTICAL);self.shell.add_css_class('shell');self.win.set_child(self.shell)
  self.draw_shell();self.win.present()
 def draw_shell(self):
  while child:=self.shell.get_first_child():self.shell.remove(child)
  # Cinematic background is an actual GTK4 image; controls remain native widgets.
  header_layer=Gtk.Overlay()
  header_layer.set_size_request(-1,86)
  self.shell.append(header_layer)
  header_art=Gtk.Picture.new_for_filename(str(ASSETS/'xarch-25-header.png'))
  header_art.set_content_fit(Gtk.ContentFit.COVER)
  header_art.set_can_shrink(True)
  header_art.set_size_request(-1,86)
  header_layer.set_child(header_art)
  header=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=14)
  header.add_css_class('header-compact')
  header.set_size_request(-1,86)
  header_layer.add_overlay(header)
  seal_frame=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
  seal_frame.add_css_class('header-seal')
  seal_frame.set_valign(Gtk.Align.CENTER)
  seal=self.pic(ASSETS/'agency.svg',52)
  seal.set_size_request(52,52)
  seal_frame.append(seal)
  header.append(seal_frame)
  titles=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=3)
  titles.set_hexpand(True)
  titles.set_valign(Gtk.Align.CENTER)
  header.append(titles)
  brand=self.label(titles,'X-ARCH  /  THEME STUDIO','brand')
  brand.set_ellipsize(3)
  subtitle=self.label(titles,'AGENT ARTUR MACIEJEWSKI  •  GUKS CARBO GLIWICE','micro')
  subtitle.set_ellipsize(3)
  subtitle.set_wrap(False)
  lang=Gtk.DropDown.new_from_strings(['English','Polski'])
  lang.set_selected(0 if self.lang=='en' else 1)
  lang.connect('notify::selected',self.change_language)
  lang.set_valign(Gtk.Align.CENTER)
  header.append(lang)
  logo=self.pic(ASSETS/'rottweilers.png',56)
  logo.set_size_request(56,56)
  logo.set_valign(Gtk.Align.CENTER)
  header.append(logo)
  body=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=0)
  body.set_vexpand(True)
  self.shell.append(body)
  side=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=7)
  side.set_size_request(218,-1)
  side.set_hexpand(False)
  side.add_css_class('side')
  body.append(side)
  banner=Gtk.Picture.new_for_filename(str(ASSETS/'xarch-25-sidebar.png'))
  banner.set_content_fit(Gtk.ContentFit.CONTAIN)
  banner.set_can_shrink(True)
  banner.set_size_request(190,232)
  banner.add_css_class('sidebar-banner')
  side.append(banner)
  self.label(side,'FBI  /  OPERATIONS','accent')
  self.navs={}
  nav_icons={'dashboard':'view-grid-symbolic','gallery':'image-x-generic-symbolic',
             'import':'document-open-symbolic','folder':'folder-symbolic',
             'restore':'edit-undo-symbolic','repair':'emblem-system-symbolic',
             'about':'dialog-information-symbolic'}
  for key,title in [('dashboard','Dashboard'),('gallery','Theme gallery'),('import','Import themes'),('folder','Folder icons'),('restore','Restore folder'),('repair','Repair folders'),('about','About')]:
   b=Gtk.Button()
   b.add_css_class('nav')
   content=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10)
   img=Gtk.Image.new_from_icon_name(nav_icons[key])
   img.set_pixel_size(18)
   img.add_css_class('nav-icon')
   content.append(img)
   text=Gtk.Label(label=self.t(title),xalign=0)
   text.set_hexpand(True)
   content.append(text)
   b.set_child(content)
   b.connect('clicked',lambda _,k=key:self.navigate(k))
   side.append(b)
   self.navs[key]=b
  spacer=Gtk.Box()
  spacer.set_vexpand(True)
  side.append(spacer)
  self.label(side,'CLASSIFIED  /  X-ARCH','micro')
  self.scroll=Gtk.ScrolledWindow()
  self.scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
  self.scroll.set_hexpand(True);self.scroll.set_vexpand(True)
  self.scroll.add_css_class('viewport');body.append(self.scroll)
  self.status=self.label(self.shell,'●  '+self.t('Ready'),'status')
  self.navigate(self.page)
 def change_language(self,dropdown,_):
  new='en' if dropdown.get_selected()==0 else 'pl'
  if new==self.lang:return
  self.lang=new
  try:
   PREFS.parent.mkdir(parents=True,exist_ok=True)
   PREFS.write_text('[ui]\nlanguage='+new+'\n')
  except OSError:pass
  self.draw_shell()
 def navigate(self,key):
  self.page=key
  for k,b in self.navs.items():
   b.remove_css_class('nav-active')
   if k==key:b.add_css_class('nav-active')
  page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);page.add_css_class('page');page.set_hexpand(True);self.scroll.set_child(page)
  getattr(self,'page_'+key)(page)
 def heading(self,page,kicker,title,description):
  self.label(page,kicker,'accent');self.label(page,self.t(title),'h1');self.label(page,self.t(description),'muted')
 def active(self):
  try:
   text=(HOME/'.config/kdeglobals').read_text();m=re.search(r'(?ms)^\[Icons\]\s*(.*?)(?=^\[|\Z)',text)
   if m:
    a=re.search(r'^Theme=(.*)$',m.group(1),re.M)
    if a:return a.group(1).strip()
  except OSError:pass
  return '—'
 def page_dashboard(self,page):
  self.heading(page,'COMMAND CENTER','Icon themes, beautifully organized.','Browse every installed icon pack, preview real icons, and personalize your desktop.')
  hero=self.card(page,'card-strong');hero_row=self.row(hero,20)
  hero_art=Gtk.Picture.new_for_filename(str(ASSETS/'xarch-26-laboratory.png'))
  hero_art.set_content_fit(Gtk.ContentFit.CONTAIN)
  hero_art.set_can_shrink(True)
  hero_art.set_size_request(260,150)
  hero_row.append(hero_art)
  txt=self.col(hero_row,10);txt.set_hexpand(True)
  self.label(txt,'CLASSIFIED  /  PROJECT X','accent')
  self.label(txt,'ALIEN  /  FBI  /  ARCHIVE','h1')
  self.label(txt,'AGENT ARTUR MACIEJEWSKI  •  GUKS CARBO GLIWICE','muted')
  self.btn(txt,'Browse collections',lambda:self.navigate('gallery'),'primary')
  stats=self.row(page,14)
  for number,name in [(str(len(all_themes())),'Collections'),(str(sum(len(icon_paths(t[1])) for t in all_themes())),'Icons'),(self.active(),'ACTIVE ICON THEME')]:
   tile=self.card(stats);tile.set_hexpand(True);self.label(tile,number,'h2');self.label(tile,self.t(name),'micro')
  archive=self.card(page,'card-strong')
  archive.add_css_class('archive-wide')
  archive_frame=Gtk.Overlay()
  archive_frame.set_hexpand(True)
  archive_frame.set_size_request(-1,260)
  archive_art=Gtk.Picture.new_for_filename(str(ASSETS/'xarch-26-ufo.png'))
  archive_art.set_content_fit(Gtk.ContentFit.COVER)
  archive_art.set_can_shrink(True)
  archive_art.set_hexpand(True)
  archive_art.set_vexpand(True)
  archive_frame.set_child(archive_art)
  archive.append(archive_frame)
  archive_actions=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
  archive_actions.add_css_class('archive-actions')
  archive.append(archive_actions)
  self.label(archive_actions,'FBI  /  ALIEN  /  ICON ARCHIVE','h2')
  self.btn(archive_actions,'Browse collections',lambda:self.navigate('gallery'),'primary')
  self.btn(page,'Install icon pack',lambda:self.navigate('import'),'primary')
 def theme_tile(self,flow,theme,i,cols=3):
  name,code,color=theme
  content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6)
  art=(ASSETS / {'X-ARCH-Alien-Crimson':'collection-alien-crimson.png','X-ARCH-Alien-Arctic':'collection-alien-arctic.png'}.get(code,'cover-'+code+'.jpg'))
  if art.is_file():
   picture=Gtk.Picture.new_for_filename(str(art))
   picture.set_content_fit(Gtk.ContentFit.CONTAIN)
   picture.set_can_shrink(True)
   picture.set_size_request(180,112)
   picture.add_css_class('cover-art')
   content.append(picture)
  else:
   content.append(self.pic(preview_icon(code),80))
  title=Gtk.Label(label=name,xalign=0)
  title.add_css_class('tile-title');title.set_ellipsize(3)
  content.append(title)
  detail=Gtk.Label(label=str(len(icon_paths(code)))+' '+self.t('icons found'),xalign=0)
  detail.add_css_class('micro');content.append(detail)
  button=Gtk.Button()
  button.add_css_class('tile');button.set_child(content)
  button.connect('clicked',lambda _,t=theme:self.select_theme(t))
  flow.insert(button,-1);self.cards[code]=button
 def page_gallery(self,page):
  icon_paths.cache_clear()
  self.heading(page,'ICON LIBRARY  /  2.0','Gallery','Your installed themes, including downloads.')
  search=Gtk.SearchEntry()
  search.set_placeholder_text(self.t('Search themes…'))
  search.set_hexpand(True);page.append(search)
  actions=self.row(page,8)
  self.btn(actions,'Refresh library',lambda:self.navigate('gallery'))
  self.btn(actions,'Install icon pack',lambda:self.navigate('import'),'primary')
  # Two independent vertical panes; horizontal scroll is explicitly disabled.
  panes=Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
  panes.set_hexpand(True);panes.set_vexpand(True)
  panes.set_size_request(-1,550)
  panes.set_resize_start_child(True);panes.set_shrink_start_child(True)
  panes.set_resize_end_child(False);panes.set_shrink_end_child(True)
  panes.set_position(510)
  page.append(panes)
  gallery_scroll=Gtk.ScrolledWindow()
  gallery_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
  gallery_scroll.set_min_content_width(280)
  self.theme_list=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=14)
  self.theme_list.set_margin_end(10)
  gallery_scroll.set_child(self.theme_list)
  panes.set_start_child(gallery_scroll)
  preview_scroll=Gtk.ScrolledWindow()
  preview_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
  preview_scroll.set_min_content_width(290)
  self.preview=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
  self.preview.add_css_class('preview-pane')
  preview_scroll.set_child(self.preview)
  panes.set_end_child(preview_scroll)
  search.connect('search-changed',lambda w:self.render_tiles(w.get_text()))
  self.render_tiles('')
  options=all_themes()
  if options:
   self.select_theme(next((t for t in options if self.selected and t[1]==self.selected[1]),options[0]))
  else:self.label(self.preview,self.t('No matching themes'),'muted')
 def render_tiles(self,query):
  while child:=self.theme_list.get_first_child():self.theme_list.remove(child)
  self.cards={};q=query.casefold().strip();found=0
  groups=[('ALIEN COLLECTION',lambda t:t[1].startswith('X-ARCH-Alien')),
          ('FBI ARCHIVE',lambda t:t[1].startswith('X-ARCH-') and not t[1].startswith('X-ARCH-Alien')),
          ('DOWNLOADED & SYSTEM THEMES',lambda t:not t[1].startswith('X-ARCH-'))]
  for title,predicate in groups:
   themes=[t for t in all_themes() if predicate(t) and (q in t[0].casefold() or q in t[1].casefold())]
   if not themes:continue
   found+=len(themes)
   self.label(self.theme_list,self.t(title)+'  /  '+str(len(themes)),'accent')
   flow=Gtk.FlowBox()
   flow.set_selection_mode(Gtk.SelectionMode.NONE)
   flow.set_homogeneous(True)
   flow.set_min_children_per_line(1)
   flow.set_max_children_per_line(2)
   flow.set_column_spacing(10);flow.set_row_spacing(10)
   flow.set_hexpand(True)
   self.theme_list.append(flow)
   for i,t in enumerate(themes):self.theme_tile(flow,t,i)
  if not found:self.label(self.theme_list,self.t('No matching themes'),'muted')
  if self.selected and self.selected[1] in self.cards:
   self.cards[self.selected[1]].add_css_class('tile-active')
 def select_theme(self,theme):
  self.selected=theme
  for code,card in self.cards.items():
   card.remove_css_class('tile-active')
   if code==theme[1]:card.add_css_class('tile-active')
  while child:=self.preview.get_first_child():self.preview.remove(child)
  name,code,color=theme
  self.label(self.preview,self.t('LIVE ICON PREVIEW'),'accent')
  self.label(self.preview,name,'h2')
  self.label(self.preview,code,'micro')
  art=(ASSETS / {'X-ARCH-Alien-Crimson':'collection-alien-crimson.png','X-ARCH-Alien-Arctic':'collection-alien-arctic.png'}.get(code,'cover-'+code+'.jpg'))
  if art.is_file():
   picture=Gtk.Picture.new_for_filename(str(art))
   picture.set_content_fit(Gtk.ContentFit.CONTAIN)
   picture.set_can_shrink(True)
   picture.set_size_request(-1,150)
   picture.add_css_class('preview-art')
   self.preview.append(picture)
  paths=icon_paths(code)
  self.label(self.preview,f'{len(paths)} '+self.t('icons found'),'muted')
  # Apply stays above the icon list, always easy to find.
  apply=self.btn(self.preview,'Apply this theme',lambda:self.confirm('Apply globally?',self.t('This changes the desktop icon theme. Pinned folder icons are preserved.'),lambda:self.run_cmd('theme',code)),'primary')
  apply.add_css_class('apply-button')
  self.label(self.preview,self.t('All icons in this theme'),'accent')
  icons_scroll=Gtk.ScrolledWindow()
  icons_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
  icons_scroll.set_min_content_height(260)
  icons_scroll.set_max_content_height(420)
  flow=Gtk.FlowBox()
  flow.set_selection_mode(Gtk.SelectionMode.NONE)
  flow.set_min_children_per_line(1)
  flow.set_max_children_per_line(4)
  flow.set_column_spacing(5);flow.set_row_spacing(5)
  for path in paths[:240]:
   cell=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=3)
   cell.add_css_class('iconcell')
   cell.append(self.pic(path,46))
   caption=Gtk.Label(label=path.stem)
   caption.set_max_width_chars(10);caption.set_ellipsize(3)
   caption.add_css_class('micro');cell.append(caption)
   flow.insert(cell,-1)
  icons_scroll.set_child(flow);self.preview.append(icons_scroll)
  if not paths:self.label(self.preview,self.t('No icon preview available'),'muted')
 def page_import(self,page):
  self.heading(page,'ACQUISITION  /  EXTERNAL PACKS','Import an icon pack','Choose an icon pack downloaded from KDE Store, GNOME-Look or another source.')
  p=self.card(page,'card-strong');p.append(self.art_image(ASSETS/'fbi-banner.jpg',950,235))
  self.label(p,self.t('Your existing icon themes are backed up before replacement. Import does not activate the theme.'),'muted')
  self.btn(p,'Install ZIP / TAR archive',self.choose_archive,'primary')
  self.btn(p,'Install unpacked folder',lambda:self.choose_folder(self.import_selected))
  self.label(p,self.t('Installed themes appear automatically in the gallery.'),'muted')
  self.btn(p,'Open gallery',lambda:self.navigate('gallery'))
 def choose_archive(self):
  d=Gtk.FileDialog();d.set_title(self.t('Select archive'))
  def done(obj,res):
   try:
    f=obj.open_finish(res);path=f.get_path()
    if path:self.import_selected(pathlib.Path(path))
   except GLib.Error:pass
  d.open(self.win,None,done)
 def import_selected(self,path):self.confirm('Import selected theme?',str(path),lambda:self.import_now(path))
 def import_now(self,path):
  try:
   names=install_theme(path,ICONS,HOME/'.local/state/xarch-theme-studio/backups')
   icon_paths.cache_clear();self.alert('Import complete',', '.join(names));self.navigate('gallery')
   if names:
    theme=next((t for t in all_themes() if t[1]==names[0]),None)
    if theme:self.select_theme(theme)
  except Exception as e:self.alert('Import failed',str(e))
 def page_folder(self,page):
  self.heading(page,'FOLDER LAB','Set a custom icon for one folder','Select a folder, then choose a theme and icon.')
  p=self.card(page);self.btn(p,'Choose folder',lambda:self.choose_folder(self.folder_options),'primary')
 def folder_options(self,path):
  page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16);page.add_css_class('page');self.scroll.set_child(page)
  self.heading(page,'FOLDER LAB',str(path), 'Choose an installed theme and icon')
  themes=all_themes();names=[t[0] for t in themes]
  if not themes:return
  chooser=Gtk.DropDown.new_from_strings(names);page.append(chooser)
  flow=Gtk.FlowBox();flow.set_selection_mode(Gtk.SelectionMode.NONE);flow.set_max_children_per_line(6);flow.set_column_spacing(10);flow.set_row_spacing(10)
  sc=Gtk.ScrolledWindow();sc.set_min_content_height(450);sc.set_child(flow);page.append(sc)
  def draw(*_):
   while child:=flow.get_first_child():flow.remove(child)
   theme=themes[chooser.get_selected()];code=theme[1]
   for icon in icon_paths(code)[:300]:
    box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4);box.append(self.pic(icon,76));self.label(box,icon.stem,'micro')
    b=Gtk.Button();b.set_child(box);b.add_css_class('tile')
    b.connect('clicked',lambda _,n=icon.stem,t=code,p=icon:self.confirm('Pin this icon?',str(path)+'  /  '+n,lambda:self.run_cmd('pin-file',path,t,p)))
    flow.insert(b,-1)
  chooser.connect('notify::selected',draw);draw()
 def page_restore(self,page):
  self.heading(page,'FOLDER LAB','Restore inherited folder icon','Choose a folder to restore its default icon.')
  p=self.card(page);self.btn(p,'Choose folder',lambda:self.choose_folder(lambda path:self.confirm('Restore this folder?',str(path),lambda:self.run_cmd('folder',path,'folder'))),'primary')
 def page_repair(self,page):
  self.heading(page,'FOLDER LAB','Preview and repair nested folders','Existing .directory files are not overwritten.')
  p=self.card(page);self.btn(p,'Choose folder',lambda:self.choose_folder(self.repair_options),'primary')
 def repair_options(self,path):
  page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=15);page.add_css_class('page');self.scroll.set_child(page)
  self.heading(page,'FOLDER LAB',self.t('Preview repair'),str(path));p=self.card(page)
  try:
   result=subprocess.run([str(BIN),'repair',str(path)],capture_output=True,text=True,timeout=120)
   self.label(p,result.stdout or result.stderr or '—','muted')
  except Exception as e:self.label(p,str(e),'muted')
  self.btn(p,'Apply repair',lambda:self.confirm('Apply repair?',str(path),lambda:self.run_cmd('repair',path,'--apply')),'primary')
 def page_about(self,page):
  pl = self.lang == "pl"
  self.heading(page,"CLASSIFIED / PROJECT DOSSIER","X-ARCH Theme Studio","Informacje o aplikacji i autorze." if pl else "Application and author information.")
  p = self.card(page,"card-strong")
  logo = self.pic(ASSETS/"rottweilers.png",200)
  logo.set_margin_top(20)
  logo.set_margin_bottom(12)
  p.append(logo)
  self.label(p,"RUNNING WITH ROTTWEILERS","accent")
  self.label(p,"X-ARCH Theme Studio","h1")
  self.label(p,"VERSION 0.1.2-beta","accent")
  p.append(self.art_image(ASSETS/"mission-banner.jpg",950,150))
  self.label(p,"AUTOR / CREATED BY" if pl else "CREATED BY","accent")
  self.label(p,"Artur Maciejewski","h2")
  self.label(p,"GUKS CARBO GLIWICE","muted")
  self.label(p,"Menedżer motywów ikon dla systemów Linux." if pl else "Icon theme manager for Linux desktops.","h2")
  self.label(p,"Przeglądanie, importowanie i zmiana motywów ikon. Personalizacja ikon folderów, przywracanie i naprawa przypisań." if pl else "Browse, import and apply icon themes. Customize folder icons, restore and repair icon assignments.","muted")
  self.label(p,"TECHNOLOGY / RUST - PYTHON - GTK4","accent")
  self.label(p,"Linux / KDE Plasma / Hyprland / English / Polski","muted")
  self.label(p,"GITHUB / OPEN SOURCE PROJECT","accent")
  github = Gtk.Button(label="GitHub / RUNNING WITH ROTTWEILERS")
  github.add_css_class("primary")
  github.connect("clicked",lambda _: Gio.AppInfo.launch_default_for_uri("https://github.com/runningwithrottweilers/xarch-theme-studio",None))
  p.append(github)
  self.label(p,"Copyright 2026 Artur Maciejewski - RUNNING WITH ROTTWEILERS","muted")
 def run_cmd(self,*args):
  try:
   r=subprocess.run([str(BIN),*map(str,args)],capture_output=True,text=True,timeout=120)
   msg=(r.stdout if r.returncode==0 else r.stderr).strip() or self.t('Operation completed')
   self.status.set_text(('●  OK  /  ' if r.returncode==0 else '●  ERROR  /  ')+msg[-230:])
   if r.returncode:self.alert('Error',msg)
   return r.returncode==0
  except Exception as e:self.alert('Error',str(e));return False
 def alert(self,title,detail):
  d=Gtk.AlertDialog();d.set_message(self.t(title));d.set_detail(str(detail)[:2500]);d.show(self.win)
 def confirm(self,title,detail,callback):
  d=Gtk.AlertDialog();d.set_message(self.t(title));d.set_detail(str(detail));d.set_buttons([self.t('Cancel'),self.t('Confirm')]);d.set_default_button(1)
  def done(obj,res):
   try:
    if obj.choose_finish(res)==1:callback()
   except GLib.Error:pass
  d.choose(self.win,None,done)
 def choose_folder(self,callback):
  d=Gtk.FileDialog();d.set_title(self.t('Select directory'))
  def done(obj,res):
   try:
    f=obj.select_folder_finish(res);p=f.get_path()
    if p:callback(pathlib.Path(p))
   except GLib.Error:pass
  d.select_folder(self.win,None,done)

if __name__=='__main__':Studio().run(sys.argv)
