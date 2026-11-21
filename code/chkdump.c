/* chkdump.c - extract one file from an MPQ using StormLib (MIT, ladislav-zezula/StormLib).
 * Usage: chkdump <archive> <internal-name> <out-file>
 * Purpose: read staredit\scenario.chk out of a protected StarCraft map so the terrain
 * sections can be inspected. Read-only on the archive. */
#include <StormLib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char ** argv)
{
    HANDLE hMpq = NULL;
    HANDLE hFile = NULL;
    DWORD dwSize, dwRead = 0;
    unsigned char * pb;

    if (argc < 4) {
        fprintf(stderr, "usage: chkdump <archive> <internal-name> <out-file>\n");
        return 2;
    }
    if (!SFileOpenArchive(argv[1], 0, MPQ_OPEN_READ_ONLY, &hMpq)) {
        fprintf(stderr, "SFileOpenArchive failed: %u\n", (unsigned)SErrGetLastError());
        return 1;
    }
    if (!SFileOpenFileEx(hMpq, argv[2], 0, &hFile)) {
        fprintf(stderr, "SFileOpenFileEx(%s) failed: %u\n", argv[2], (unsigned)SErrGetLastError());
        SFileCloseArchive(hMpq);
        return 1;
    }
    dwSize = SFileGetFileSize(hFile, NULL);
    if (dwSize == 0 || dwSize > 0x4000000) {
        fprintf(stderr, "bad size %u\n", (unsigned)dwSize);
        return 1;
    }
    pb = (unsigned char *)malloc(dwSize);
    if (pb == NULL) return 1;
    if (!SFileReadFile(hFile, pb, dwSize, &dwRead, NULL)) {
        fprintf(stderr, "SFileReadFile failed: %u (read %u of %u)\n",
                (unsigned)SErrGetLastError(), (unsigned)dwRead, (unsigned)dwSize);
        return 1;
    }
    FILE * f = fopen(argv[3], "wb");
    if (f == NULL) return 1;
    fwrite(pb, 1, dwRead, f);
    fclose(f);
    printf("extracted %u bytes of %s -> %s\nhead: ", (unsigned)dwRead, argv[2], argv[3]);
    for (unsigned i = 0; i < 16 && i < dwRead; i++) printf("%02x", pb[i]);
    printf("\n");
    SFileCloseFile(hFile);
    SFileCloseArchive(hMpq);
    return 0;
}
