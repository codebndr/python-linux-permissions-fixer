# -*- mode: python -*-
a = Analysis(['myserver.py'],
             pathex=['/home/tzikis/Desktop/python-websocket-daemon'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='myserver',
          debug=False,
          strip=None,
          upx=True,
          console=True )
