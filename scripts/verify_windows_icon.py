"""Fail the build if the supplied multi-size icon was not embedded in the EXE."""
from pathlib import Path
import struct
import pefile

root=Path(__file__).resolve().parents[1]
data=(root/'assets/orcaprime-commercial.ico').read_bytes()
_,kind,count=struct.unpack_from('<HHH',data)
assert kind==1 and count>=5,'Expected a multi-size Windows icon'
expected=[]
for i in range(count):
    length,offset=struct.unpack_from('<II',data,6+i*16+8)
    expected.append(data[offset:offset+length])
with pefile.PE(str(root/'dist/OrcaPrime/OrcaPrime.exe')) as exe:
    icons=[]
    for resource in exe.DIRECTORY_ENTRY_RESOURCE.entries:
        if resource.id!=3:continue
        for group in resource.directory.entries:
            for language in group.directory.entries:
                info=language.data.struct
                icons.append(exe.get_data(info.OffsetToData,info.Size))
    assert all(frame in icons for frame in expected),'EXE does not contain the new supplied icon'
print(f'Ícone novo confirmado no EXE: {count} tamanhos.')
