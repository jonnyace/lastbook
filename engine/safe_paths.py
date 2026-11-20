"""Where a library path really leads, and whether it may be opened. Shared by engine/library.py and engine/encyclopedias.py.

Standard library only, so either can import it without importing the other.
"""
from __future__ import annotations
import os
from pathlib import Path

RESERVED_NAMES={'con','prn','aux','nul'}|{f'{d}{i}' for d in ('com','lpt') for i in range(1,10)}

def real_path(path):
 """Where a path really ends up: links and junctions followed and, on Windows, 8.3 short names expanded."""
 real=os.path.realpath(path)
 if os.name=='nt':
  import ctypes
  buf=ctypes.create_unicode_buffer(32768);n=ctypes.windll.kernel32.GetLongPathNameW(real,buf,32768)
  if 0<n<32768:real=buf.value
  if real.startswith('\\\\?\\') and not real.startswith('\\\\?\\UNC\\'):real=real[4:]
 return real

def parts_below(real,root):
 """The path parts of real below root, or None when real is not inside root."""
 real,root=os.path.normcase(real),os.path.normcase(str(root))
 if real==root:return ()
 prefix=root.rstrip(os.sep)+os.sep
 return tuple(real[len(prefix):].split(os.sep)) if real.startswith(prefix) else None

def name_refused(parts):
 """The file name itself: hidden files, sign-in files, and yt-dlp's .info.json, which can hold request headers."""
 name=parts[-1].lower() if parts else ''
 return name.startswith(('.','video-auth')) or 'cookie' in name or name.endswith('.info.json')

def segments_ok(path,windows=os.name=='nt'):
 """NTFS opens "x.", "x " and "x::$DATA" as x, and treats some names as devices; the name checks would not see those."""
 if not windows:return True
 for s in path.split('/'):
  if s!=s.rstrip('. ') or ':' in s or '\\' in s or s.split('.')[0].lower() in RESERVED_NAMES:return False
 return True

def zim_file(library,name):
 """The encyclopedia file <library>/collections/<name>, after the same checks as any other file; ValueError if refused.
 Links and junctions are followed: a file whose real path is outside collections/ is refused, as are refused names."""
 if not name or '\0' in name or Path(name).name!=name or not segments_ok(name):raise ValueError('Invalid collection')
 path=Path(library)/'collections'/name
 real=real_path(path);parts=parts_below(real,real_path(Path(library)/'collections'))
 if parts is None or name_refused(parts) or not segments_ok('/'.join(parts)) or not real.lower().endswith('.zim'):raise ValueError('Invalid collection')
 return path
