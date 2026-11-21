/* mkmpq.c - write a StarCraft map MPQ through StormLib (MIT, ladislav-zezula/StormLib,
 * commit d60b7e6d3501474f4d92c7b9c752a37e78385f67), replacing the hand-rolled
 * build_map.build_mpq writer. TASK-0042 dispatch 2.
 *
 * Usage: mkmpq <out.scm> <mode> <archived-name>=<local-file> [...]
 *   mode: plain       blob stored single-unit, uncompressed, unencrypted
 *         zlib        blob stored single-unit, zlib-compressed (payload 0x02+zlib)
 *         attrs       plain + (attributes) added to the archive
 *         zlibattrs   zlib + (attributes) added to the archive
 * Archive always carries (listfile) via MPQ_CREATE_LISTFILE.
 * Names must be given with the backslash escaped by the shell quoting, e.g.
 *   "staredit\\scenario.chk"=chk.bin  */
#include <StormLib.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char ** argv)
{
    HANDLE hMpq = NULL;
    DWORD createFlags;
    DWORD fileFlags;
    DWORD compression;
    int i;

    if (argc < 4) {
        fprintf(stderr, "usage: mkmpq <out.scm> <plain|zlib|attrs|zlibattrs> name=file ...\n");
        return 2;
    }

    /* archive-level flags: always listfile; attrs modes also add (attributes) */
    createFlags = MPQ_CREATE_LISTFILE;
    if (strstr(argv[2], "attrs"))
        createFlags |= MPQ_CREATE_ATTRIBUTES;

    /* file-level storage: single unit like every real map; zlib adds MPQ_FILE_COMPRESS */
    fileFlags = MPQ_FILE_SINGLE_UNIT;
    compression = MPQ_COMPRESSION_PKWARE; /* unused when no COMPRESS flag */
    if (strncmp(argv[2], "zlib", 4) == 0) {
        fileFlags |= MPQ_FILE_COMPRESS;
        compression = MPQ_COMPRESSION_ZLIB;
    }

    if (!SFileCreateArchive(argv[1], createFlags, 8, &hMpq)) {
        fprintf(stderr, "SFileCreateArchive failed: %u\n", (unsigned)SErrGetLastError());
        return 1;
    }

    for (i = 3; i < argc; i++) {
        char pair[1024];
        char * sep;
        strcpy(pair, argv[i]);
        sep = strchr(pair, '=');
        if (sep == NULL) {
            fprintf(stderr, "bad pair (need name=file): %s\n", argv[i]);
            SFileCloseArchive(hMpq);
            return 2;
        }
        *sep = '\0';
        if (!SFileAddFileEx(hMpq, sep + 1, pair, fileFlags, compression, MPQ_COMPRESSION_NEXT_SAME)) {
            fprintf(stderr, "SFileAddFileEx(%s) failed: %u\n", pair, (unsigned)SErrGetLastError());
            SFileCloseArchive(hMpq);
            return 1;
        }
    }

    if (!SFileCloseArchive(hMpq)) {
        fprintf(stderr, "SFileCloseArchive failed: %u\n", (unsigned)SErrGetLastError());
        return 1;
    }
    printf("wrote %s mode=%s\n", argv[1], argv[2]);
    return 0;
}
